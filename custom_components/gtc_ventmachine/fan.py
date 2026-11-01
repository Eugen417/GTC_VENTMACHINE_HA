from __future__ import annotations

import asyncio
from homeassistant.components.fan import FanEntity, FanEntityFeature

from .const import DOMAIN, HR_FAN_TARGET_1, IR_FAN_STATE_1, IR_STATE_0
from .entity import GTCBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GTCFan(hub, entry)])


class GTCFan(GTCBaseEntity, FanEntity):
    _attr_has_entity_name = False
    _attr_name = "GTC Fan"
    _attr_speed_count = 10
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
    )

    def __init__(self, hub, entry):
        super().__init__(hub)
        self._attr_unique_id = f"{entry.entry_id}_gtc_fan_v_final_strict"

    @property
    def is_on(self) -> bool:
        pwr = self._hub.data.get(f"in_{IR_STATE_0}", 0)
        speed = self._hub.data.get(f"in_{IR_FAN_STATE_1}", 0)
        return bool(pwr & 1) or speed > 0

    @property
    def percentage(self) -> int:
        if not self.is_on:
            return 0
        speed = self._hub.data.get(f"in_{HR_FAN_TARGET_1}", 0)
        return int(speed * 10) if 1 <= speed <= 10 else 0

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage <= 0:
            await self.async_turn_off()
            return

        speed = max(1, min(10, round(percentage / 10)))
        if not (self._hub.data.get(f"in_{IR_STATE_0}", 0) & 1):
            await self._hub.async_set_power(True)
            await asyncio.sleep(0.2)
        await self._hub.async_write(HR_FAN_TARGET_1, speed)

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs) -> None:
        if percentage is not None and percentage > 0:
            await self.async_set_percentage(percentage)
            return

        await self._hub.async_set_power(True)
        if self._hub.data.get(f"in_{HR_FAN_TARGET_1}", 0) < 1:
            await asyncio.sleep(0.2)
            await self._hub.async_write(HR_FAN_TARGET_1, 1)

    async def async_turn_off(self, **kwargs) -> None:
        await self._hub.async_set_power(False)
