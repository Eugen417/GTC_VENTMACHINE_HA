from homeassistant.components.number import NumberEntity
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
        info = {
            "identifiers": {(DOMAIN, "gtc_syberia")},
            "name": "GTC Syberia 5",
            "manufacturer": "GTC",
            # ИСПРАВЛЕНО: добавлено [{self._hub.hw_config}]
            "model": f"Syberia 5 [{self._hub.hw_config}] ({self._hub.host}:{self._hub.port})",
            "configuration_url": f"http://{self._hub.host}"
        }
        if self._hub.sw_version:
            info["sw_version"] = self._hub.sw_version
        if self._hub.mac:
            import homeassistant.helpers.device_registry as dr
            info["connections"] = {(dr.CONNECTION_NETWORK_MAC, self._hub.mac)}
        return info

    @property
    def native_value(self):
        val = self._hub.data.get("in_31")
        if val is None or val == 0:
            return None
        return round(float(val) * 0.1, 1)

    async def async_set_native_value(self, value):
        await self._hub.async_write(31, int(value * 10))
