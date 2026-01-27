import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory, DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Настройка платформы select (ровно 3 аргумента!)."""
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
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "gtc_syberia")},
            name="GTC Ventmachine",
        )

    @property
    def current_option(self) -> str:
        return str(getattr(self._hub, 'poll_interval', 5))

    async def async_select_option(self, option: str) -> None:
        self._hub.poll_interval = int(option)
        self.async_write_ha_state()
