from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature

from .const import DOMAIN, HR_FAN_TARGET_1, HR_FAN_TARGET_2, HR_TEMP_TARGET
from .entity import GTCBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            GTCTempTarget(hub, entry),
            GTCSupplySpeed(hub, entry),
            GTCExhaustSpeed(hub, entry),
        ]
    )


class GTCTempTarget(GTCBaseEntity, NumberEntity):
    """Уставка температуры приточного воздуха."""

    _attr_has_entity_name = False
    _attr_name = "Уставка температуры"
    _attr_icon = "mdi:thermometer-check"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 5.0
    _attr_native_max_value = 30.0
    _attr_native_step = 0.5

    def __init__(self, hub, entry):
        super().__init__(hub)
        self._attr_unique_id = f"{entry.entry_id}_target_temp_v16"

    @property
    def native_value(self) -> float | None:
        val = self._hub.data.get(f"in_{HR_TEMP_TARGET}")
        if val is None or val == 0:
            return None
        if val > 32767:
            val -= 65536
        return round(float(val) * 0.1, 1)

    async def async_set_native_value(self, value: float) -> None:
        clamped = max(self._attr_native_min_value, min(self._attr_native_max_value, float(value)))
        await self._hub.async_write(HR_TEMP_TARGET, int(round(clamped * 10)))


class GTCSupplySpeed(GTCBaseEntity, NumberEntity):
    """Ступень скорости приточного вентилятора (1–10) при раздельном управлении."""

    _attr_has_entity_name = True
    _attr_name = "Скорость притока"
    _attr_icon = "mdi:fan-chevron-up"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 1
    _attr_native_max_value = 10
    _attr_native_step = 1
    _attr_entity_registry_enabled_default = False

    def __init__(self, hub, entry):
        super().__init__(hub)
        self._attr_unique_id = f"{entry.entry_id}_supply_speed"

    @property
    def native_value(self) -> int | None:
        val = self._hub.data.get(f"in_{HR_FAN_TARGET_1}")
        return int(val) if val is not None and 1 <= int(val) <= 10 else None

    async def async_set_native_value(self, value: float) -> None:
        speed = max(1, min(10, int(round(float(value)))))
        await self._hub.async_write(HR_FAN_TARGET_1, speed)


class GTCExhaustSpeed(GTCBaseEntity, NumberEntity):
    """Ступень скорости вытяжного вентилятора (1–10) для ПВУ с раздельным управлением."""

    _attr_has_entity_name = True
    _attr_name = "Скорость вытяжки"
    _attr_icon = "mdi:fan-chevron-down"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 1
    _attr_native_max_value = 10
    _attr_native_step = 1
    _attr_entity_registry_enabled_default = False

    def __init__(self, hub, entry):
        super().__init__(hub)
        self._attr_unique_id = f"{entry.entry_id}_exhaust_speed"

    @property
    def native_value(self) -> int | None:
        val = self._hub.data.get(f"in_{HR_FAN_TARGET_2}")
        return int(val) if val is not None and 1 <= int(val) <= 10 else None

    async def async_set_native_value(self, value: float) -> None:
        speed = max(1, min(10, int(round(float(value)))))
        await self._hub.async_write(HR_FAN_TARGET_2, speed)


