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
        # Место для хранения ссылки на фоновую задачу
        self.poll_task = None

    async def async_update(self):
        """Метод обновления данных."""
        async with self._lock:
            return await asyncio.to_thread(self._fetch_sync)

    def _fetch_sync(self):
        try:
            # Уменьшаем таймаут до 2 сек, чтобы не вешать поток надолго
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
            # Логируем как warning, чтобы не спамить error в случае штатных разрывов
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
        """Метод для очистки ресурсов, если потребуется в будущем"""
        pass
