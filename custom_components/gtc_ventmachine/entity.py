"""Базовый класс сущностей GTC Ventmachine."""

from __future__ import annotations

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .hub import GTCVentHub


class GTCBaseEntity(Entity):
    """Общий базовый класс для всех сущностей GTC Ventmachine."""

    _attr_should_poll = False

    def __init__(self, hub: GTCVentHub) -> None:
        self._hub = hub

    async def async_added_to_hass(self) -> None:
        """Подписка на обновления хаба при добавлении сущности в HA."""
        await super().async_added_to_hass()
        self.async_on_remove(self._hub.register_listener(self.async_write_ha_state))

    @property
    def device_info(self) -> dict:
        """Информация об устройстве для реестра Home Assistant."""
        hw_cfg = self._hub.hw_config or "Стандартная"
        info = {
            "identifiers": {(DOMAIN, "gtc_syberia")},
            "name": "GTC Syberia 5",
            "manufacturer": "GTC",
            "model": f"Syberia 5 [{hw_cfg}] ({self._hub.host}:{self._hub.port})",
            "configuration_url": f"http://{self._hub.host}",
        }
        if self._hub.sw_version:
            info["sw_version"] = self._hub.sw_version
        if self._hub.mac:
            info["connections"] = {(dr.CONNECTION_NETWORK_MAC, self._hub.mac)}
        return info
