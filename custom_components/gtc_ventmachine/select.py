import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GTCPollIntervalSelect(hub, entry)], True)

class GTCPollIntervalSelect(SelectEntity):
    _attr_has_entity_name = True
    _attr_name = "Интервал опроса системы"
    _attr_icon = "mdi:timer-cog"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hub, entry):
        self._hub = hub
        self._attr_unique_id = f"gtc_{entry.data['host']}_poll_select"
        self._attr_options = ["2", "3", "4", "5", "6", "7", "8", "9", "10"]

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
    def current_option(self) -> str:
        return str(getattr(self._hub, 'poll_interval', 5))

    async def async_select_option(self, option: str) -> None:
        self._hub.poll_interval = int(option)
        self.async_write_ha_state()
