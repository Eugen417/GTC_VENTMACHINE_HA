import asyncio
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GTCFan(hub, entry)], True)

class GTCFan(FanEntity):
    def __init__(self, hub, entry):
        self._hub = hub
        self._attr_name = "GTC Fan"
        self._attr_unique_id = f"{entry.entry_id}_gtc_fan_v_final_strict"
        self._attr_supported_features = (
            FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        )

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, "gtc_syberia")}, name="GTC Syberia 5")

    @property
    def is_on(self):
        speed = self._hub.data.get("in_25", 0)
        return speed > 0

    @property
    def percentage(self):
        speed = self._hub.data.get("in_25", 0)
        return int(speed * 10) if 1 <= speed <= 10 else 0

    async def async_set_percentage(self, percentage):
        if percentage == 0:
            await self.async_turn_off()
        else:
            speed = max(1, int(percentage / 10))
            await self._hub.async_write(2, 1) # Включить
            await self._hub.async_write(32, speed) # Скорость

    # ПРИНИМАЕМ ВСЁ: и позиционные (*args), и именованные (**kwargs)
    async def async_turn_on(self, percentage=None, *args, **kwargs):
        # ДЕЙСТВИЕ: Включить (1 в регистр 2)
        await self._hub.async_write(2, 1)
        
        if percentage:
            await self.async_set_percentage(percentage)
        else:
            # Если скорость не выбрана, а в 32-м пусто — ставим 1
            if self._hub.data.get("in_32", 0) == 0:
                await self._hub.async_write(32, 1)

    async def async_turn_off(self, *args, **kwargs):
        # ДЕЙСТВИЕ: Выключить (0 в регистр 2)
        # Шлем 1, потом 0 с задержкой, как просили в YAML
        await self._hub.async_write(2, 1)
        await asyncio.sleep(1)
        await self._hub.async_write(2, 0)
