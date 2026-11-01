from __future__ import annotations

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from .const import (
    DOMAIN,
    HR_FAN_TARGET_1,
    HR_POWER_DEV,
    HR_TEMP_TARGET,
    IR_FAN_STATE_1,
    IR_STATE_0,
    IR_STATE_1,
    IR_TKAN_X10,
)
from .entity import GTCBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GTCClimate(hub, entry)])


class GTCClimate(GTCBaseEntity, ClimateEntity):
    _attr_has_entity_name = True
    _attr_name = "Климат"

    _attr_min_temp = 5.0
    _attr_max_temp = 30.0
    _attr_target_temperature_step = 0.5
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_fan_modes = [str(i) for i in range(1, 11)]
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]

    def __init__(self, hub, entry):
        super().__init__(hub)
        self._attr_unique_id = f"{entry.entry_id}_climate_vfinal"

    @property
    def current_temperature(self) -> float | None:
        val = self._hub.data.get(f"in_{IR_TKAN_X10}")
        if val is None:
            return None
        if val > 32767:
            val -= 65536
        return round(float(val) * 0.1, 1)

    @property
    def target_temperature(self) -> float | None:
        val = self._hub.data.get(f"in_{HR_TEMP_TARGET}")
        if val is None:
            return None
        if val > 32767:
            val -= 65536
        return round(float(val) * 0.1, 1)

    async def async_set_temperature(self, **kwargs) -> None:
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is not None:
            temp = max(self._attr_min_temp, min(self._attr_max_temp, float(temp)))
            await self._hub.async_write(HR_TEMP_TARGET, int(round(temp * 10)))

    @property
    def hvac_mode(self) -> HVACMode:
        pwr = self._hub.data.get(f"in_{IR_STATE_0}", 0)
        return HVACMode.HEAT if (pwr & 1) else HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        pwr = self._hub.data.get(f"in_{IR_STATE_0}", 0)
        stage = self._hub.data.get(f"in_{IR_STATE_1}", 0) & 0x1F
        fan_spd = self._hub.data.get(f"in_{IR_FAN_STATE_1}", 0)
        if not (pwr & 1) and stage == 0 and fan_spd == 0:
            return HVACAction.OFF
        # Если нагрев доступен (бит 6 в State_0) или идет предподогрев/работа
        if pwr & 64:
            return HVACAction.HEATING
        if fan_spd > 0:
            return HVACAction.FAN
        return HVACAction.IDLE

    async def async_set_hvac_mode(self, hvac_mode: HVACMode, *args, **kwargs) -> None:
        if hvac_mode == HVACMode.OFF:
            await self._hub.async_set_power(False)
        else:
            await self._hub.async_set_power(True)

    @property
    def fan_mode(self) -> str:
        val = self._hub.data.get(f"in_{HR_FAN_TARGET_1}", 1)
        if not isinstance(val, int) or val < 1 or val > 10:
            return "1"
        return str(val)

    async def async_set_fan_mode(self, fan_mode: str, *args, **kwargs) -> None:
        if str(fan_mode).isdigit():
            val = int(fan_mode)
            if 1 <= val <= 10:
                await self._hub.async_write(HR_FAN_TARGET_1, val)

    async def async_turn_on(self, *args, **kwargs) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self, *args, **kwargs) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)
