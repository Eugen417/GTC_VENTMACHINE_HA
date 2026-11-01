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
    HR_DEV_KEYS_3,
    HR_FAN_CONFIG_2,
    HR_FAN_TARGET_1,
    HR_FAN_TARGET_2,
    HR_MAC_START,
    HR_POWER_DEV,
    HR_TEMP_TARGET,
    HR_TYPE_DEV,
    IR_FIRMWARE_VERS,
    IR_STATE_0,
)

_LOGGER = logging.getLogger(__name__)

# Межпакетная пауза (30 мс) для стабильной работы через RS-485 шлюзы (Promodem WiFi-485 и др.)
INTER_FRAME_DELAY = 0.03
SOCKET_TIMEOUT = 3.0

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

        self._sock: socket.socket | None = None
        self._tx_id: int = 0
        self.online: bool = True
        self._listeners: list[Callable[[], None]] = []

        self.mac: str | None = None
        self.ip: str = host
        self.sw_version: str | None = None
        self.hw_config: str = "Стандартная"

        # Автоопределяемые флаги комплектации установки
        self.hw_detected: bool = False
        self.heater_type: int = 1
        self.cooler_type: int = 0
        self.recup_type: int = 0
        self.fan2_speeds: int = 0
        self.has_water_heater: bool = False
        self.has_cooler: bool = False
        self.has_recup: bool = False
        self.has_rotor: bool = False
        self.has_exhaust_fan: bool = False
        self.separate_fans: bool = False

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

    def _next_tx_id(self) -> int:
        self._tx_id = (self._tx_id % 65535) + 1
        return self._tx_id

    def _ensure_socket(self) -> socket.socket:
        if self._sock is not None:
            return self._sock
        sock = socket.create_connection((self.host, self.port), timeout=SOCKET_TIMEOUT)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._sock = sock
        return sock

    def _close_socket(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def _drain_socket(self, sock: socket.socket) -> None:
        try:
            sock.setblocking(False)
            while sock.recv(1024):
                pass
        except (BlockingIOError, OSError):
            pass
        finally:
            sock.settimeout(SOCKET_TIMEOUT)

    def _recv_exact(self, sock: socket.socket, size: int) -> bytes:
        buf = bytearray()
        while len(buf) < size:
            chunk = sock.recv(size - len(buf))
            if not chunk:
                raise ConnectionError("Соединение закрыто удалённым узлом")
            buf.extend(chunk)
        return bytes(buf)

    def _modbus_request(self, func: int, address: int, count_or_val: int) -> bytes | None:
        # Важно (Issue #1): контроллеры GTC на прошивках 0.95/0.102 требуют Transaction ID = 0x0000
        tx_id = 0x0000
        for attempt in range(3):
            try:
                sock = self._ensure_socket()
                self._drain_socket(sock)
                packet = struct.pack(
                    ">HHHBBHH",
                    tx_id,
                    0x0000,
                    0x0006,
                    self.slave_id,
                    func,
                    address,
                    count_or_val & 0xFFFF,
                )
                sock.sendall(packet)
                header = self._recv_exact(sock, 7)
                _rx_tx_id, rx_proto, rx_len, _rx_unit = struct.unpack(">HHHB", header)
                if rx_proto != 0 or rx_len < 2 or rx_len > 260:
                    raise ValueError(f"Некорректный MBAP: proto={rx_proto}, len={rx_len}")
                pdu = self._recv_exact(sock, rx_len - 1)
                rx_func = pdu[0]
                if rx_func & 0x80:
                    exc_code = pdu[1] if len(pdu) > 1 else 0
                    _LOGGER.debug("Modbus exc func=0x%02X addr=%d code=0x%02X", func, address, exc_code)
                    return None
                if rx_func != func:
                    raise ValueError(f"Несовпадение функции ({func} != {rx_func})")
                return pdu
            except (socket.timeout, OSError, ValueError) as err:
                self._close_socket()
                if attempt < 2:
                    time.sleep(0.25 * (attempt + 1))
                    continue
                raise err
        return None

    def _read_registers(self, func: int, start: int, count: int) -> list[int] | None:
        pdu = self._modbus_request(func, start, count)
        if pdu is None:
            return None
        expected_bytes = count * 2
        if len(pdu) < 2 + expected_bytes or pdu[1] != expected_bytes:
            raise ValueError(f"Неверная длина ответа ({len(pdu) - 2} != {expected_bytes})")
        payload = pdu[2 : 2 + expected_bytes]
        return list(struct.unpack(f">{count}H", payload))


    async def async_init_device_info(self) -> None:
        """Одиночный запрос при старте для получения версии ПО, MAC и конфигурации оборудования."""
        async with self._lock:
            await asyncio.to_thread(self._init_device_info_sync)

    def _init_device_info_sync(self) -> None:
        try:
            # 1. Версия прошивки: PDF 0x01 (01) Firmware_Vers -> адрес 0, PDF 0x02 (02) -> адрес 1
            fw_regs = self._read_registers(0x04, IR_FIRMWARE_VERS, 2)
            if fw_regs:
                self.sw_version = self._format_firmware(fw_regs[0], fw_regs[1])
            time.sleep(INTER_FRAME_DELAY)

            # 2. MAC-адрес: PDF 0x162..0x164 (354..356) -> адрес 353, 3 регистра
            mac_regs = self._read_registers(0x03, HR_MAC_START, 3)
            if mac_regs and len(mac_regs) == 3:
                m0, m1, m2 = mac_regs
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

            # 3. Автоопределение железа: PDF 0x01 (01) Type_Dev -> адрес 0
            hw_regs = self._read_registers(0x03, HR_TYPE_DEV, 1)
            if hw_regs:
                hw_val = hw_regs[0]
                heater = hw_val & 0x0F
                cooler = (hw_val >> 4) & 0x0F
                recup = (hw_val >> 8) & 0x0F

                self.heater_type = heater
                self.cooler_type = cooler
                self.recup_type = recup
                self.has_water_heater = heater in (2, 3)
                self.has_cooler = cooler > 0
                self.has_recup = recup > 0
                self.has_rotor = recup == 2
                self.hw_detected = True

                parts = []
                if heater in HEATER_MAP:
                    parts.append(HEATER_MAP[heater])
                if cooler in COOLER_MAP:
                    parts.append(COOLER_MAP[cooler])
                if recup in RECUP_MAP:
                    parts.append(RECUP_MAP[recup])

                self.hw_config = " + ".join(parts) if parts else "Стандартная"
            time.sleep(INTER_FRAME_DELAY)

            # 4. Автоопределение 2-го вентилятора (вытяжки): PDF 0x12 (18) -> адрес 17
            fan2_regs = self._read_registers(0x03, HR_FAN_CONFIG_2, 1)
            if fan2_regs:
                self.fan2_speeds = fan2_regs[0] & 0xFF
                self.hw_detected = True
            time.sleep(INTER_FRAME_DELAY)

            # 5. Режим управления притоком и вытяжкой: PDF 0x58 (88) -> адрес 87 (Bit 10: 0 - разд., 1 - синхр.)
            keys_regs = self._read_registers(0x03, HR_DEV_KEYS_3, 1)
            sync_fans = False
            if keys_regs:
                sync_fans = bool(keys_regs[0] & (1 << 10))

            self.has_exhaust_fan = (self.fan2_speeds > 0) or self.has_recup
            self.separate_fans = self.has_exhaust_fan and not sync_fans
            _LOGGER.info(
                "GTC автоопределение: config='%s', fan2_speeds=%d, has_exhaust=%s, separate_fans=%s",
                self.hw_config,
                self.fan2_speeds,
                self.has_exhaust_fan,
                self.separate_fans,
            )
        except Exception as err:
            _LOGGER.warning("Не удалось прочитать системную информацию (MAC/Прошивка/Железо): %s", err)

    @staticmethod
    def _format_firmware(fw_main: int, fw_sub: int) -> str:
        # В контроллерах Syberia 5 основная версия часто лежит в IR 1 (fw_sub: ст. байт.мл. байт, напр. 0.102)
        if fw_sub > 0:
            sub_str = f"{fw_sub >> 8}.{fw_sub & 0xFF}"
            if 0 < fw_main < 20 and (fw_sub >> 8) == 0:
                return f"{fw_main}.{sub_str}"
            return sub_str
        if fw_main > 0:
            hi = (fw_main >> 8) & 0xFF
            lo = fw_main & 0xFF
            if hi > 0x09 and (hi >> 4) > 0:
                major = (hi >> 4) & 0x0F
                minor = hi & 0x0F
                patch = int(f"{lo:02x}") if (lo & 0x0F) <= 9 and (lo >> 4) <= 9 else lo
                return f"{major}.{minor}.{patch}"
            return f"{hi}.{lo}"
        return "5.0"

    async def async_test_connection(self) -> bool:
        """Проверяет доступность контроллера."""
        async with self._lock:
            return await asyncio.to_thread(self._test_connection_sync)

    def _test_connection_sync(self) -> bool:
        try:
            regs = self._read_registers(0x04, IR_STATE_0, 2)
            return regs is not None
        except Exception:
            return False

    async def async_update(self) -> bool:
        async with self._lock:
            ok = await asyncio.to_thread(self._fetch_sync)
        if ok:
            self.notify_listeners()
        return ok

    def _fetch_sync(self) -> bool:
        try:
            poll_map = [
                # Input Registers (0x04):
                # (2, 13) -> 2..14 (State_0, State_1, Errors, Last_Time, T1..T3, Filter1)
                # (25, 6) -> 25..30 (Fan_State_1, Next_Timer, Max_Holding, Fan_State_2 [in_30])
                # (57, 4) -> 57..60 (TKomn_x10_P, Room_Hum_P, Room_CO2)
                # (69, 2) -> 69..70 (Error_Code_2, Error_Code_3)
                # (74, 3) -> 74..76 (TKomn_x10, Trecp_x10)
                # (81, 4) -> 81..84 (Fan1_RPM, Fan2_RPM, ZagrFiltr2)
                (0x04, [(2, 13), (25, 6), (57, 4), (69, 2), (74, 3), (81, 4)]),
                # Holding Registers (0x03):
                # (31, 3) -> 31..33 (Temp_Target [in_31], Fan_Target_1 [in_32], Fan_Target_2 [in_33])
                (0x03, [(31, 3)]),
            ]
            new_data: dict[str, int] = {}
            for func, blocks in poll_map:
                for start, count in blocks:
                    regs = self._read_registers(func, start, count)
                    if regs is not None:
                        for i, val in enumerate(regs):
                            new_data[f"in_{start + i}"] = val
                            if func == 0x03:
                                new_data[f"hr_{start + i}"] = val
                    time.sleep(INTER_FRAME_DELAY)
            if new_data:
                self.data.update(new_data)
                self.online = True
                return True
        except (socket.timeout, OSError, ValueError) as err:
            _LOGGER.warning("GTC Connection/Read Error (%s:%s): %s", self.host, self.port, err)
        except Exception as err:
            _LOGGER.error("GTC Unexpected Error: %s", err)
        return False

    async def async_set_power(self, turn_on: bool) -> bool:
        """Включает или выключает установку (с импульсом 1 -> 0 при выключении)."""
        if turn_on:
            return await self.async_write(HR_POWER_DEV, 1)
        # Для гарантированного выключения (даже если включили с пульта) формируем фронт 1 -> 0
        await self.async_write(HR_POWER_DEV, 1)
        await asyncio.sleep(0.4)
        return await self.async_write(HR_POWER_DEV, 0)

    async def async_write(self, address: int, value: int) -> bool:
        async with self._lock:
            ok = await asyncio.to_thread(self._write_sync, address, int(value))
        if ok:
            int_val = int(value) & 0xFFFF
            self.data[f"hr_{address}"] = int_val
            if address == HR_POWER_DEV:
                cur_state = self.data.get(f"in_{IR_STATE_0}", 0)
                self.data[f"in_{IR_STATE_0}"] = (cur_state | 1) if (int_val & 1) else (cur_state & ~1)
            elif address in (HR_TEMP_TARGET, HR_FAN_TARGET_1, HR_FAN_TARGET_2):
                self.data[f"in_{address}"] = int_val
            self.notify_listeners()
        return ok

    def _write_sync(self, address: int, value: int) -> bool:
        try:
            pdu = self._modbus_request(0x06, address, int(value))
            time.sleep(INTER_FRAME_DELAY)
            return pdu is not None and len(pdu) >= 5
        except Exception as err:
            _LOGGER.error("GTC Write Error (addr=%s, val=%s): %s", address, value, err)
        return False

    def close(self) -> None:
        self._close_socket()

