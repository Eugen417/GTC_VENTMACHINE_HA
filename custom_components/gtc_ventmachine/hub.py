import socket
import struct
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class GTCVentHub:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.data = {}
        self._lock = asyncio.Lock()
        self.poll_interval = 5 
        self.poll_task = None
        
        # Системные данные для карточки устройства
        self.mac = None
        self.ip = host
        self.sw_version = None

    async def async_init_device_info(self):
        """Одиночный запрос при старте для получения MAC и прошивки."""
        def _fetch():
            try:
                with socket.create_connection((self.host, self.port), timeout=3) as s:
                    # Версия прошивки (Input Reg 1, count 1)
                    s.send(struct.pack('>HHHBBHH', 1, 0, 6, 1, 0x04, 1, 1))
                    res_fw = s.recv(1024)
                    if len(res_fw) >= 11:
                        fw_val = struct.unpack('>H', res_fw[9:11])[0]
                        self.sw_version = f"{fw_val >> 8}.{fw_val & 0xFF}"

                    # MAC-адрес (Holding Reg 354-356, count 3)
                    s.send(struct.pack('>HHHBBHH', 1, 0, 6, 1, 0x03, 354, 3))
                    res_mac = s.recv(1024)
                    if len(res_mac) >= 15:
                        m0 = struct.unpack('>H', res_mac[9:11])[0]
                        m1 = struct.unpack('>H', res_mac[11:13])[0]
                        m2 = struct.unpack('>H', res_mac[13:15])[0]
                        self.mac = f"{m0 & 0xFF:02x}:{m0 >> 8:02x}:{m1 & 0xFF:02x}:{m1 >> 8:02x}:{m2 & 0xFF:02x}:{m2 >> 8:02x}"
            except Exception as e:
                _LOGGER.warning("Не удалось прочитать системную информацию (MAC/Прошивка): %s", e)

        await asyncio.to_thread(_fetch)

    async def async_update(self):
        """Метод обновления данных."""
        async with self._lock:
            return await asyncio.to_thread(self._fetch_sync)

    def _fetch_sync(self):
        try:
            with socket.create_connection((self.host, self.port), timeout=2) as s:
                poll_map = [
                    (0x04, [(2, 13), (25, 1), (57, 2), (69, 2)]), 
                    (0x03, [(31, 2)])
                ]

                for func, blocks in poll_map:
                    for start, count in blocks:
                        packet = struct.pack('>HHHBBHH', 0x01, 0x00, 0x06, 0x01, func, start, count)
                        s.send(packet)
                        res = s.recv(1024)
                        if len(res) >= 9 + (count * 2):
                            payload = res[9:9 + (count * 2)]
                            for i in range(count):
                                self.data[f"in_{start + i}"] = struct.unpack('>H', payload[i*2:i*2+2])[0]
                return True
        except (socket.timeout, OSError) as e:
            _LOGGER.warning("GTC Connection/Read Error: %s", e)
        except Exception as e:
            _LOGGER.error("GTC Unexpected Error: %s", e)
        return False

    async def async_write(self, address, value):
        async with self._lock:
            await asyncio.sleep(0.2)
            return await asyncio.to_thread(self._write_sync, address, value)

    def _write_sync(self, address, value):
        try:
            packet = struct.pack('>HHHBBHH', 0x01, 0x00, 0x06, 0x01, 0x06, address, int(value))
            with socket.create_connection((self.host, self.port), timeout=2) as s:
                s.send(packet)
                return True
        except Exception as e:
            _LOGGER.error("GTC Write Error: %s", e)
        return False
        
    def close(self):
        pass