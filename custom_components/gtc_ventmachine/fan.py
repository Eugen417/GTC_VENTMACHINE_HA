import asyncio
from homeassistant.components.fan import FanEntity, FanEntityFeature
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GTCFan(hub, entry)], True)

class GTCFan(FanEntity):
    _attr_has_entity_name = False

    def __init__(self, hub, entry):
        self._hub = hub
        self._attr_name = "GTC Fan"
        self._attr_unique_id = f"{entry.entry_id}_gtc_fan_v_final_strict"
        self._attr_supported_features = (
            FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        )

    @property
    def device_info(self):
        info = {
            "identifiers": {(DOMAIN, "gtc_syberia")},
            "name": "GTC Syberia 5",
            "manufacturer": "GTC",
            # Добавляем IP и порт прямо в строку модели для отображения в карточке
            "model": f"Syberia 5 ({self._hub.host}:{self._hub.port})",
            # Эта строка создаст кнопку "Открыть веб-интерфейс" (если он висит на 80 порту)
            "configuration_url": f"http://{self._hub.host}"
        }
        if self._hub.sw_version:
            info["sw_version"] = self._hub.sw_version
        if self._hub.mac:
            import homeassistant.helpers.device_registry as dr
            info["connections"] = {(dr.CONNECTION_NETWORK_MAC, self._hub.mac)}
        return info

    @property
    def is_on(self):
        speed = self._hub.data.get("in_25", 0)
        return speed > 0

    @property
    def percentage(self):
        speed = self._hub.data.get("in_32", 0)
        return int(speed * 10) if 1 <= speed <= 10 else 0

    @property
    def speed_count(self):
        return 10

    async def async_set_percentage(self, percentage):
        if percentage == 0:
            await self.async_turn_off()
        else:
            speed = int(percentage / 10)
            if speed > 10: speed = 10
            if speed < 1: speed = 1
            
            await self._hub.async_write(2, 1)
            await asyncio.sleep(0.2)
            await self._hub.async_write(32, speed)

    async def async_turn_on(self, percentage=None, *args, **kwargs):
        await self._hub.async_write(2, 1)
        if percentage:
            await self.async_set_percentage(percentage)
        else:
            if self._hub.data.get("in_32", 0) == 0:
                await self._hub.async_write(32, 1)

    async def async_turn_off(self, *args, **kwargs):
        await self._hub.async_write(2, 1)
        await asyncio.sleep(0.5)
        await self._hub.async_write(2, 0)