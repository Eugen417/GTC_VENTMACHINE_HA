from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from .const import DOMAIN

STATE_1_MAP = {
    0: "Ожидание", 1: "Открытие заслонки", 2: "Предподогрев",
    3: "Работа", 4: "Северный старт", 5: "Выбег",
    6: "Закрытие заслонки", 7: "Продувка", 8: "Клапан ГВС +",
    9: "Клапан ГВС -", 10: "Клапан ХВС +", 11: "Клапан ХВС -", 
    12: "Разгон ротора"
}

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    
    sensors = [
        ("gtc_current_temp", 7, "temp_01", UnitOfTemperature.CELSIUS, "Текущая температура", None),
        ("gtc_outside_temp", 11, "temp_01", UnitOfTemperature.CELSIUS, "Наружная температура", None),
        ("gtc_target_temp", 31, "temp_01", UnitOfTemperature.CELSIUS, "Целевая температура", None), 
        ("gtc_room_temp", 57, "temp_01", UnitOfTemperature.CELSIUS, "Температура в помещении", None),
        ("gtc_room_humidity", 58, "as_is", PERCENTAGE, "Влажность", None),
        ("gtc_filter_state", 14, "as_is", PERCENTAGE, "Загрязнение фильтра", None),
        ("gtc_current_fan_speed", 25, "as_is", None, "Текущая скорость", None),
        ("gtc_target_fan_speed", 32, "as_is", None, "Целевая скорость", None),
        ("gtc_operation_stage", 3, "state_map", None, "Этап работы", EntityCategory.DIAGNOSTIC)
    ]
    
    async_add_entities([GTCSensor(hub, entry, *s) for s in sensors], True)

class GTCSensor(SensorEntity):
    _attr_has_entity_name = False

    def __init__(self, hub, entry, key, address, mode, unit, friendly_name, category):
        self._hub = hub
        self._address = address
        self._mode = mode
        self._attr_native_unit_of_measurement = unit
        self._attr_name = friendly_name
        self._attr_entity_category = category
        self._attr_unique_id = f"gtc_final_v2_{key}"
        
        if "temp" in key:
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, "gtc_syberia")}, name="GTC Syberia 5")

    @property
    def native_value(self):
        val = self._hub.data.get(f"in_{self._address}")
        if val is None: return None
        if self._mode == "temp_01":
            if val > 32767: val -= 65536
            return round(float(val) * 0.1, 1)
        if self._mode == "state_map":
            if val == 0:
                pwr = self._hub.data.get("in_2", 0)
                return "Готов" if (pwr & 1) else "Выключено"
            return STATE_1_MAP.get(val, f"Код {val}")
        return val
