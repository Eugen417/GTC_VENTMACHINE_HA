import asyncio
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.helpers.entity import DeviceInfo
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
        return DeviceInfo(identifiers={(DOMAIN, "gtc_syberia")}, name="GTC Syberia 5")

    @property
    def is_on(self):
        # Проверяем питание (регистр 2), а не вращение (регистр 25)
        # Это гарантирует, что HA сразу видит выключение, не дожидаясь остановки мотора
        return bool(self._hub.data.get("in_2", 0) & 1)

    @property
    def percentage(self):
        # Берем уставку (регистр 32), чтобы ползунок в HA не прыгал при разгоне
        speed = self._hub.data.get("in_32", 0)
        return int((speed / 7) * 100) if 1 <= speed <= 7 else 0

    @property
    def speed_count(self):
        return 7

    async def async_set_percentage(self, percentage):
        if percentage == 0:
            await self.async_turn_off()
        else:
            # Конвертируем % в ступени 1-7
            step = max(1, min(7, round((percentage / 100) * 7)))
            await self._hub.async_write(2, 1)  # Питание ВКЛ
            await asyncio.sleep(0.1)
            await self._hub.async_write(32, step) # Скорость

    async def async_turn_on(self, percentage=None, *args, **kwargs):
        await self._hub.async_write(2, 1)
        if percentage:
            await self.async_set_percentage(percentage)
        elif self._hub.data.get("in_32", 0) == 0:
            await self._hub.async_write(32, 1)

    async def async_turn_off(self, *args, **kwargs):
        # Просто выключаем питание. Контроллер GTC сам обеспечит выбег и продувку.
        await self._hub.async_write(2, 0)
