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
        # Твоя верная логика по датчику вращения
        speed = self._hub.data.get("in_25", 0)
        return speed > 0

    @property
    def percentage(self):
        # Красивые 10%, 20%... на основе регистра уставки 32
        speed = self._hub.data.get("in_32", 0)
        return int(speed * 10) if 1 <= speed <= 7 else 0

    @property
    def speed_count(self):
        return 10

    async def async_set_percentage(self, percentage):
        if percentage == 0:
            await self.async_turn_off()
        else:
            # Мапим проценты в ступени 1-7
            speed = int(percentage / 10)
            if speed > 7: speed = 7
            if speed < 1: speed = 1
            
            await self._hub.async_write(2, 1) # Питание ВКЛ
            await asyncio.sleep(0.2)
            await self._hub.async_write(32, speed) # Скорость 1-7

    # Добавляем *args и **kwargs, чтобы HA не ругался на количество аргументов
    async def async_turn_on(self, percentage=None, *args, **kwargs):
        await self._hub.async_write(2, 1)
        
        if percentage:
            await self.async_set_percentage(percentage)
        else:
            # Если скорость не задана, ставим 1-ю
            if self._hub.data.get("in_32", 0) == 0:
                await self._hub.async_write(32, 1)

    # Здесь тоже добавляем поддержку любых входящих аргументов
    async def async_turn_off(self, *args, **kwargs):
        await self._hub.async_write(2, 1)
        await asyncio.sleep(0.5)
        await self._hub.async_write(2, 0)
