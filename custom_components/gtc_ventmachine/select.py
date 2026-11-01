from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DEFAULT_POLL_INTERVAL, DOMAIN
from .entity import GTCBaseEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GTCPollIntervalSelect(hub, entry)])


class GTCPollIntervalSelect(GTCBaseEntity, SelectEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_name = "Интервал опроса системы"
    _attr_icon = "mdi:timer-cog"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_options = ["2", "3", "4", "5", "6", "7", "8", "9", "10"]

    def __init__(self, hub, entry):
        super().__init__(hub)
        host_key = entry.data.get("host", entry.entry_id)
        self._attr_unique_id = f"gtc_{host_key}_poll_select"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state in self._attr_options:
            self._hub.poll_interval = int(last_state.state)

    @property
    def current_option(self) -> str:
        return str(getattr(self._hub, "poll_interval", DEFAULT_POLL_INTERVAL))

    async def async_select_option(self, option: str) -> None:
        if option in self._attr_options:
            self._hub.poll_interval = int(option)
            self.async_write_ha_state()

