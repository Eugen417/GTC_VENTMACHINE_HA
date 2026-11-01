from __future__ import annotations

import asyncio
import logging
import socket
import struct
import time
from typing import Callable

from .const import (
    DEFAULT_POLL_INTERVAL,
    DEFAULT_SLAVE_ID,
    HR_FAN_TARGET_1,
    HR_FAN_TARGET_2,
    HR_POWER_DEV,
    HR_TEMP_TARGET,
    HR_TYPE_DEV,
    IR_STATE_0,
)

_LOGGER = logging.getLogger(__name__)

# Межпакетная пауза (30 мс) для стабильной работы через RS-485 шлюзы (Promodem WiFi-485 и др.)
INTER_FRAME_DELAY = 0.03
SOCKET_TIMEOUT = 2.0

HEATER_MAP = {
    1: "Эл. калорифер",
    2: "Вод. калорифер",
    3: "Комб. калорифер",
}

COOLER_MAP = {
    1: "ККБ",
    2: "Фанкойл",
    3: "Вод. охладитель",
    4: "Инвертор. ККБ",
    5: "Комб. ККБ",
    6: "Двойной ККБ",
    7: "Двойной ККБ (ротация)",
    8: "Ротация ККБ",
}

RECUP_MAP = {
    1: "Пласт. рекуператор",
    2: "Ротор. рекуператор",
    3: "Гликол. рекуператор",
    4: "Хладон. рекуператор",
}


class GTCVentHub:
    """Хаб обмена данными с контроллером GTC (Оазис v.5 / Syberia 5) по Modbus TCP."""

    def __init__(self, host: str, port: int, slave_id: int = DEFAULT_SLAVE_ID) -> None:
        self.host = host
        self.port = port
        self.slave_id = slave_id
        self.data: dict[str, int] = {}
        self._lock = asyncio.Lock()
        self.poll_interval: int = DEFAULT_POLL_INTERVAL
        self.poll_task: asyncio.Task | None = None

        self.online: bool = True
        self._listeners: list[Callable[[], None]] = []

        self.mac: str | None = None
        self.ip: str = host
        self.sw_version: str | None = None
        self.hw_config: str = "Стандартная"

    def register_listener(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Регистрирует callback сущности и возвращает функцию отписки."""
        self._listeners.append(callback)

        def _remove() -> None:
            if callback in self._listeners:
                self._listeners.remove(callback)

        return _remove

    def notify_listeners(self) -> None:
        """Уведомляет все зарегистрированные сущности о новых данных."""
        for callback in list(self._listeners):
            try:
                callback()
            except Exception as err:
                _LOGGER.debug("Ошибка при обновлении слушателя GTC: %s", err)


    async def async_init_device_info(self) -> None:
        """Одиночный запрос при старте для получения MAC, прошивки и железа."""
        async with self._lock:
            await asyncio.to_thread(self._init_device_info_sync)

    def _init_device_info_sync(self) -> None:
        try:
            with socket.create_connection((self.host, self.port), timeout=3) as s:
                # 1. Версия прошивки (Input Reg 1, count 1)
                s.send(struct.pack(">HHHBBHH", 0, 0, 6, self.slave_id, 0x04, 1, 1))
                res_fw = s.recv(1024)
                if len(res_fw) >= 11 and not (res_fw[7] & 0x80):
                    fw_val = struct.unpack(">H", res_fw[9:11])[0]
                    self.sw_version = f"{fw_val >> 8}.{fw_val & 0xFF}"
                time.sleep(INTER_FRAME_DELAY)

                # 2. MAC-адрес (Holding Reg 354..356, count 3)
                s.send(struct.pack(">HHHBBHH", 0, 0, 6, self.slave_id, 0x03, 354, 3))
                res_mac = s.recv(1024)
                if len(res_mac) >= 15 and not (res_mac[7] & 0x80):
                    m0 = struct.unpack(">H", res_mac[9:11])[0]
                    m1 = struct.unpack(">H", res_mac[11:13])[0]
                    m2 = struct.unpack(">H", res_mac[13:15])[0]
                    mac_bytes = [
                        m0 & 0xFF,
                        (m0 >> 8) & 0xFF,
                        m1 & 0xFF,
                        (m1 >> 8) & 0xFF,
                        m2 & 0xFF,
                        (m2 >> 8) & 0xFF,
                    ]
                    if any(b != 0x00 for b in mac_bytes) and any(b != 0xFF for b in mac_bytes):
                        self.mac = ":".join(f"{b:02x}" for b in mac_bytes)
                time.sleep(INTER_FRAME_DELAY)

                # 3. Автоопределение железа (Holding Reg 0 [Type_Dev], count 1)
                s.send(struct.pack(">HHHBBHH", 0, 0, 6, self.slave_id, 0x03, HR_TYPE_DEV, 1))
                res_hw = s.recv(1024)
                if len(res_hw) >= 11 and not (res_hw[7] & 0x80):
                    hw_val = struct.unpack(">H", res_hw[9:11])[0]
                    heater = hw_val & 0x0F
                    cooler = (hw_val >> 4) & 0x0F
                    recup = (hw_val >> 8) & 0x0F

                    parts = []
                    if heater in HEATER_MAP:
                        parts.append(HEATER_MAP[heater])
                    if cooler in COOLER_MAP:
                        parts.append(COOLER_MAP[cooler])
                    if recup in RECUP_MAP:
                        parts.append(RECUP_MAP[recup])

                    self.hw_config = " + ".join(parts) if parts else "Стандартная"
        except Exception as err:
            _LOGGER.warning("Не удалось прочитать системную информацию (MAC/Прошивка/Железо): %s", err)

    async def async_update(self) -> bool:
        async with self._lock:
            ok = await asyncio.to_thread(self._fetch_sync)
        if ok:
            self.notify_listeners()
        return ok

    def _fetch_sync(self) -> bool:
        try:
            with socket.create_connection((self.host, self.port), timeout=SOCKET_TIMEOUT) as s:
                poll_map = [
                    # (2, 13) -> 2..14 (State_0, State_1, Errors, Last_Time, T1..T3, Filter1)
                    # (25, 6) -> 25..30 (Fan_State_1, Next_Timer, Max_Holding, Fan_State_2 [in_30])
                    # (57, 2) -> 57..58 (TKomn_x10_P, Room_Hum_P)
                    # (69, 2) -> 69..70 (Error_Code_2, Error_Code_3)
                    # (81, 2) -> 81..82 (Fan1_RPM, Fan2_RPM)
                    (0x04, [(2, 13), (25, 6), (57, 2), (69, 2), (81, 2)]),
                    # (31, 3) -> 31..33 (Temp_Target [in_31], Fan_Target_1 [in_32], Fan_Target_2 [in_33])
                    (0x03, [(31, 3)]),
                ]

                for func, blocks in poll_map:
                    for start, count in blocks:
                        packet = struct.pack(">HHHBBHH", 0x00, 0x00, 0x06, self.slave_id, func, start, count)
                        s.send(packet)
                        res = s.recv(1024)
                        if len(res) >= 9 + (count * 2) and not (res[7] & 0x80):
                            payload = res[9 : 9 + (count * 2)]
                            for i in range(count):
                                self.data[f"in_{start + i}"] = struct.unpack(">H", payload[i * 2 : i * 2 + 2])[0]
                        time.sleep(INTER_FRAME_DELAY)
                self.online = True
                return True
        except (socket.timeout, OSError) as err:
            _LOGGER.warning("GTC Connection/Read Error: %s", err)
        except Exception as err:
            _LOGGER.error("GTC Unexpected Error: %s", err)
        return False

    async def async_set_power(self, turn_on: bool) -> bool:
        """Включает или выключает установку (с импульсом 1 -> 0 при выключении)."""
        if turn_on:
            return await self.async_write(HR_POWER_DEV, 1)
        await self.async_write(HR_POWER_DEV, 1)
        await asyncio.sleep(0.4)
        return await self.async_write(HR_POWER_DEV, 0)

    async def async_write(self, address: int, value: int) -> bool:
        async with self._lock:
            await asyncio.sleep(0.15)
            ok = await asyncio.to_thread(self._write_sync, address, int(value))
        if ok:
            int_val = int(value) & 0xFFFF
            if address == HR_POWER_DEV:
                cur_state = self.data.get(f"in_{IR_STATE_0}", 0)
                self.data[f"in_{IR_STATE_0}"] = (cur_state | 1) if (int_val & 1) else (cur_state & ~1)
            elif address in (HR_TEMP_TARGET, HR_FAN_TARGET_1, HR_FAN_TARGET_2):
                self.data[f"in_{address}"] = int_val
            self.notify_listeners()
        return ok

    def _write_sync(self, address: int, value: int) -> bool:
        packet = struct.pack(">HHHBBHH", 0x00, 0x00, 0x06, self.slave_id, 0x06, address, int(value) & 0xFFFF)
        for attempt in range(2):
            try:
                with socket.create_connection((self.host, self.port), timeout=SOCKET_TIMEOUT) as s:
                    s.send(packet)
                    try:
                        s.recv(1024)
                    except (socket.timeout, OSError):
                        pass
                    return True
            except Exception as err:
                if attempt == 0:
                    time.sleep(0.2)
                    continue
                _LOGGER.error("GTC Write Error: %s", err)
        return False

    def close(self) -> None:
        pass


