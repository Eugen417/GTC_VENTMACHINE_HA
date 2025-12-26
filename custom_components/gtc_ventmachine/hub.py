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

    async def async_update(self):
        async with self._lock:
            return await asyncio.to_thread(self._fetch_sync)

    def _fetch_sync(self):
        try:
            with socket.create_connection((self.host, self.port), timeout=5) as s:
                # Читаем Input Registers (0x04) и Holding Registers (0x03)
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
        except Exception as e:
            _LOGGER.error("GTC Hub Read Error: %s", e)
        return False

    async def async_write(self, address, value):
        async with self._lock:
            await asyncio.sleep(0.2)
            return await asyncio.to_thread(self._write_sync, address, value)

    def _write_sync(self, address, value):
        try:
            packet = struct.pack('>HHHBBHH', 0x01, 0x00, 0x06, 0x01, 0x06, address, int(value))
            with socket.create_connection((self.host, self.port), timeout=5) as s:
                s.send(packet)
                return True
        except Exception as e:
            _LOGGER.error("GTC Write Error: %s", e)
        return False
