from homeassistant.components.number import NumberEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import UnitOfTemperature
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GTCTempTarget(hub, entry)], True)

class GTCTempTarget(NumberEntity):
    def __init__(self, hub, entry):
        self._hub = hub
        self._attr_name = "Уставка температуры"
        self._attr_unique_id = f"{entry.entry_id}_target_temp_v16"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_native_min_value = 5.0
        self._attr_native_max_value = 30.0
        self._attr_native_step = 0.5

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, "gtc_syberia")}, name="GTC Syberia 5")

    @property
    def native_value(self):
        # Состояние берется из ключа 'in_31'
        val = self._hub.data.get("in_31")
        if val is None or val == 0:
            return None
        # Если в регистре 130, в HA будет 13.0
        return round(float(val) * 0.1, 1)

    async def async_set_native_value(self, value):
        # Запись: 13.5 -> 135
        await self._hub.async_write(31, int(value * 10))
