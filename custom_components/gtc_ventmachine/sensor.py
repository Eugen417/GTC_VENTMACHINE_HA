from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from .const import DOMAIN

STATE_MAP = {
    0: "Ожидание", 1: "Открытие заслонки", 2: "Предподогрев",
    3: "Запуск вентилятора", 4: "Северный старт", 5: "Выбег",
    6: "Закрытие заслонки", 7: "Продувка эл. калорифера", 
    8: "Открытие клапана ГВС", 9: "Закрытие клапана ГВС",
    10: "Открытие клапана ХВС", 11: "Закрытие клапана ХВС",
    12: "Разгон ротора"
}

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    
    # 1. Основные цифровые сенсоры (Добавлен флаг enabled_default)
    sensors = [
        ("stg", 3, "stage", None, "Состояние Уст.", "mdi:state-machine", True),
        ("t_cur", 7, "temp", UnitOfTemperature.CELSIUS, "Текущая температура", "mdi:thermometer", True),
        ("t_set", 31, "temp", UnitOfTemperature.CELSIUS, "Целевая температура", "mdi:thermometer-check", True),
        ("t_out", 11, "temp", UnitOfTemperature.CELSIUS, "Наружная температура (T2)", "mdi:thermometer", True), # Исправлена иконка
        ("t_in", 57, "temp", UnitOfTemperature.CELSIUS, "Температура в помещении", "mdi:home-thermometer", True),
        ("hum", 58, "as_is", PERCENTAGE, "Влажность", "mdi:water-percent", True),
        ("spd", 25, "as_is", None, "Текущая скорость", "mdi:fan-speed-1", True),
        ("spd_set", 32, "as_is", None, "Целевая скорость", "mdi:fan-speed-2", True),
        ("flt", 14, "as_is", PERCENTAGE, "Загрязнение фильтра", "mdi:air-filter", True),
        ("rpm_1", 81, "as_is", "об/мин", "Обороты вентилятора 1", "mdi:fan", False), # Отключено по умолчанию
        ("rpm_2", 82, "as_is", "об/мин", "Обороты вентилятора 2", "mdi:fan", False), # Отключено по умолчанию
        ("timer_sec", 6, "countdown", None, "Таймер операции", "mdi:timer-sand", True),
        ("next_timer", 26, "next_timer", None, "Следующий таймер", "mdi:calendar-clock", True)
    ]
    entities = [GTCSensor(hub, entry, *s) for s in sensors]

    # 2. Текстовые сенсоры процессов (Добавлен флаг enabled_default)
    process_configs = [
        ("pwr", 2, 1, "bit", "Статус: Питание", "Включено", "Ожидание", "mdi:power", True),
        ("trans", 2, 2, "bit", "Статус: Переходный процесс", "Активно", "Покой", "mdi:cog-transfer", True),
        ("heat_av", 2, 64, "bit", "Статус: Нагрев доступен", "Доступен", "Нет", "mdi:fire", True),
        ("d_open", 3, 1, "equal", "Открытие заслонки", "Открывается", "Покой", "mdi:door-open", True),
        ("d_close", 3, 6, "equal", "Закрытие заслонки", "Закрывается", "Покой", "mdi:door-closed", True),
        ("preheat", 3, 2, "equal", "Предподогрев", "Активно", "Покой", "mdi:heating-coil", True),
        ("f_start", 3, 3, "equal", "Запуск вентилятора", "Активно", "Покой", "mdi:fan", True), # Исправлена иконка
        ("f_stop", 3, 5, "equal", "Выбег вентилятора", "Активно", "Покой", "mdi:fan-off", True),
        ("north", 3, 4, "equal", "Северный старт", "Активно", "Покой", "mdi:snowflake-alert", True),
        ("gvs_o", 3, 8, "equal", "Клапан ГВС: Открытие", "Открывается", "Покой", "mdi:water-boiler", False), # Отключено
        ("gvs_c", 3, 9, "equal", "Клапан ГВС: Закрытие", "Закрывается", "Покой", "mdi:water-boiler-off", False), # Отключено
        ("hvs_o", 3, 10, "equal", "Клапан ХВС: Открытие", "Открывается", "Покой", "mdi:water", False), # Отключено
        ("hvs_c", 3, 11, "equal", "Клапан ХВС: Закрытие", "Закрывается", "Покой", "mdi:water-off", False), # Отключено
        ("rotor", 3, 12, "equal", "Разгон ротора", "Активно", "Покой", "mdi:rotate-3d-variant", True),
        ("lock", 5, 64, "bit", "Блокировка пульта", "Заблокировано", "Свободно", "mdi:lock", True)
    ]
    entities.extend([GTCProcessSensor(hub, entry, *c) for c in process_configs])

    async_add_entities(entities, True)


class GTCSensor(SensorEntity):
    _attr_has_entity_name = False
    
    def __init__(self, hub, entry, key, address, mode, unit, friendly_name, icon, enabled_default):
        self._hub = hub
        self._address = address
        self._mode = mode
        self._attr_native_unit_of_measurement = unit
        self._attr_name = friendly_name
        self._attr_icon = icon
        self._attr_unique_id = f"gtc_manual_v1_s_{key}"
        self._attr_entity_registry_enabled_default = enabled_default

    @property
    def device_info(self):
        info = {
            "identifiers": {(DOMAIN, "gtc_syberia")},
            "name": "GTC Syberia 5",
            "manufacturer": "GTC",
            "model": f"Syberia 5 [{self._hub.hw_config}] ({self._hub.host}:{self._hub.port})",
            "configuration_url": f"http://{self._hub.ip}"
        }
        if self._hub.sw_version:
            info["sw_version"] = self._hub.sw_version
        if self._hub.mac:
            import homeassistant.helpers.device_registry as dr
            info["connections"] = {(dr.CONNECTION_NETWORK_MAC, self._hub.mac)}
        return info

    @property
    def native_value(self):
        val = self._hub.data.get(f"in_{self._address}")
        if val is None: return None
        
        if self._mode == "temp":
            if val > 32767: val -= 65536
            return round(float(val) * 0.1, 1)
            
        if self._mode == "stage":
            clean_val = val & 0x1F
            if clean_val == 0:
                pwr = self._hub.data.get("in_2", 0)
                return "Работает" if (pwr & 1) else "Ожидание"
            return STATE_MAP.get(clean_val, f"Код {clean_val}")

        if self._mode == "countdown":
            mins = val >> 8
            secs = val & 0xFF
            if mins == 0 and secs == 0:
                return "Нет активных процессов"
            return f"{mins:02d}:{secs:02d}"

        if self._mode == "next_timer":
            time_val = self._hub.data.get("in_26")
            temp_val = self._hub.data.get("in_27")
            fan_val = self._hub.data.get("in_28")
            
            if time_val is None or temp_val is None or fan_val is None:
                return "Нет данных"
                
            hour = time_val >> 8
            minute = time_val & 0xFF
            
            if hour == 0 and minute == 0 and temp_val == 0:
                return "Расписание выключено"
                
            if temp_val > 32767: temp_val -= 65536
            temp = round(float(temp_val) * 0.1, 1)
            
            return f"В {hour:02d}:{minute:02d} ({temp} °C, Скор. {fan_val})"
            
        return val


class GTCProcessSensor(SensorEntity):
    _attr_has_entity_name = False
    
    def __init__(self, hub, entry, key, address, target, logic, friendly_name, text_on, text_off, icon, enabled_default):
        self._hub = hub
        self._address = address
        self._target = target
        self._logic = logic
        self._text_on = text_on
        self._text_off = text_off
        self._attr_name = friendly_name
        self._attr_icon = icon
        self._attr_unique_id = f"gtc_manual_v1_proc_{key}"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_entity_registry_enabled_default = enabled_default

    @property
    def device_info(self):
        info = {
            "identifiers": {(DOMAIN, "gtc_syberia")},
            "name": "GTC Syberia 5",
            "manufacturer": "GTC",
            "model": f"Syberia 5 [{self._hub.hw_config}] ({self._hub.host}:{self._hub.port})",
            "configuration_url": f"http://{self._hub.ip}"
        }
        if self._hub.sw_version:
            info["sw_version"] = self._hub.sw_version
        if self._hub.mac:
            import homeassistant.helpers.device_registry as dr
            info["connections"] = {(dr.CONNECTION_NETWORK_MAC, self._hub.mac)}
        return info

    @property
    def native_value(self):
        val = self._hub.data.get(f"in_{self._address}", 0)
        is_active = False
        
        if self._logic == "bit":
            is_active = bool(val & self._target)
        elif self._logic == "equal":
            is_active = (val & 0x1F) == self._target
            
        return self._text_on if is_active else self._text_off