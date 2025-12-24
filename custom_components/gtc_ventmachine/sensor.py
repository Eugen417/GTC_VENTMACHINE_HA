from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from .const import DOMAIN

STATE_1_MAP = {
    0: "Ожидание", 1: "Открытие заслонки", 2: "Предподогрев",
    3: "Работа", 4: "Северный старт", 5: "Выбег",
    6: "Закрытие заслонки", 7: "Продувка", 8: "Клапан ГВС +",
    9: "Клапан ГВС -", 10: "Клапан ХВС +", 11: "Клапан ХВС -", 12: "Разгон ротора"
}

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    
    sensors = [
        ("gtc_current_temp", 7, "temp_01", UnitOfTemperature.CELSIUS),
        ("gtc_target_temp", 31, "temp_01", UnitOfTemperature.CELSIUS), 
        ("gtc_room_temp", 57, "temp_01", UnitOfTemperature.CELSIUS),
        ("gtc_room_humidity", 58, "as_is", PERCENTAGE),
        ("gtc_filter_state", 14, "as_is", PERCENTAGE),
        ("gtc_current_fan_speed", 25, "as_is", None),
        ("gtc_target_fan_speed", 32, "as_is", None),
        ("gtc_state_0", 2, "as_is", None),
        ("gtc_state_1", 3, "as_is", None),
        ("gtc_error_code_1", 5, "as_is", None),
        ("gtc_operation_stage", 3, "state_map", None),
    ]
    
    async_add_entities([GTCSensor(hub, entry, *s) for s in sensors], True)

class GTCSensor(SensorEntity):
    _attr_has_entity_name = True # Это заставляет HA искать имя в переводах

    def __init__(self, hub, entry, name, address, mode, unit):
        self._hub = hub
        self._address = address
        self._mode = mode
        self._attr_native_unit_of_measurement = unit
        self._attr_translation_key = name  # Ключ из JSON
        self._attr_unique_id = f"gtc_fix_final_{name}"
        
        if "temp" in name:
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, "gtc_syberia")}, name="GTC Syberia 5")

    @property
    def native_value(self):
        val = self._hub.data.get(f"in_{self._address}")
        if val is None: return None
        if self._mode == "temp_01": return round(float(val) * 0.1, 1)
        if self._mode == "state_map":
            if val == 0:
                pwr = self._hub.data.get("in_2", 0)
                return "Работает" if (pwr & 1) else "Выключено"
            return STATE_1_MAP.get(val, f"Код {val}")
        return val
