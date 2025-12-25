from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature, HVACMode, FAN_LOW, FAN_MEDIUM, FAN_HIGH
)
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GTCClimate(hub, entry)], True)

class GTCClimate(ClimateEntity):
    _attr_has_entity_name = True
    _attr_name = "Климат"
    
    def __init__(self, hub, entry):
        self._hub = hub
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        
        # Настраиваем возможности: установка темп. и режимы вентилятора
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | 
            ClimateEntityFeature.FAN_MODE |
            ClimateEntityFeature.TURN_ON |
            ClimateEntityFeature.TURN_OFF
        )
        # Определяем список доступных скоростей (от 1 до 10)
        self._attr_fan_modes = [str(i) for i in range(1, 11)]
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, "gtc_syberia")}, "name": "GTC Syberia 5"}

    # --- ТЕМПЕРАТУРА ---
    @property
    def current_temperature(self):
        val = self._hub.data.get("in_7")
        if val is None: return None
        if val > 32767: val -= 65536
        return round(float(val) * 0.1, 1)

    @property
    def target_temperature(self):
        val = self._hub.data.get("in_31")
        if val is None: return None
        return round(float(val) * 0.1, 1)

    async def async_set_temperature(self, **kwargs):
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self._hub.async_write(31, int(temp * 10))

    # --- РЕЖИМЫ (ВКЛ/ВЫКЛ) ---
    @property
    def hvac_mode(self):
        # Проверяем бит 0 в регистре 2 (питание)
        pwr = self._hub.data.get("in_2", 0)
        return HVACMode.HEAT if (pwr & 1) else HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            await self._hub.async_write(2, 0)
        else:
            await self._hub.async_write(2, 1)

    # --- ВЕНТИЛЯТОР ---
    @property
    def fan_mode(self):
        # Читаем целевую скорость из регистра 32
        return str(self._hub.data.get("in_32", 1))

    async def async_set_fan_mode(self, fan_mode):
        if fan_mode.isdigit():
            await self._hub.async_write(32, int(fan_mode))
