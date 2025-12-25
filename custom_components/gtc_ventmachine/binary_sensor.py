from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    
    # ID, Рег, Бит, Логика, Имя, ТИП (для текста)
    configs = [
        ("gtc_power", 2, 1, "bit", "Питание", "pwr"),
        ("gtc_heat_avail", 2, 2, "bit", "Доступность нагрева", "pwr"),
        ("gtc_cool_avail", 2, 4, "bit", "Доступность охлаждения", "pwr"),
        ("gtc_day_timer", 2, 8, "bit", "Таймер на сутки", "tmr"),
        ("gtc_week_timer", 2, 16, "bit", "Таймер на неделю", "tmr"),
        ("gtc_heat_mode", 2, 256, "bit", "Режим работы", "heat"),

        ("gtc_gvs_open", 3, 8, "equal", "Клапан ГВС (открытие)", "pwr"),
        ("gtc_gvs_close", 3, 9, "equal", "Клапан ГВС (закрытие)", "pwr"),
        ("gtc_hvs_open", 3, 10, "equal", "Клапан ХВС (открытие)", "pwr"),
        ("gtc_hvs_close", 3, 11, "equal", "Клапан ХВС (закрытие)", "pwr"),

        ("gtc_error_t1", 5, 1, "bit", "Ошибка: Датчик T1", "err"),
        ("gtc_error_t2", 5, 2, "bit", "Ошибка: Датчик T2", "err"),
        ("gtc_error_t3", 5, 4, "bit", "Ошибка: Датчик T3", "err"),
        ("gtc_error_d5", 5, 8, "bit", "Ошибка: Давление D5", "err"),
        ("gtc_error_overheat", 5, 16, "bit", "Авария: Перегрев", "err"),
        ("gtc_error_underheat", 5, 32, "bit", "Авария: Недогрев", "err"),
        ("gtc_lock", 5, 64, "bit", "Блокировка управления", "lock"),
        ("gtc_north_start", 5, 2048, "bit", "Режим: Северный старт", "pwr"),
        ("gtc_error_frost", 5, 8192, "bit", "Авария: Обмерзание", "err"),
    ]
    
    async_add_entities([GTCBitSensor(hub, entry, *c) for c in configs], True)

class GTCBitSensor(BinarySensorEntity):
    _attr_has_entity_name = False 

    def __init__(self, hub, entry, key, address, target, logic, friendly_name, sensor_type):
        self._hub = hub
        self._address = address
        self._target = target
        self._logic = logic
        self._type = sensor_type
        self._attr_name = friendly_name
        self._attr_unique_id = f"gtc_final_v5_{key}"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        
        if sensor_type == "err":
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, "gtc_syberia")}, name="GTC Syberia 5")

    @property
    def is_on(self):
        val = self._hub.data.get(f"in_{self._address}", 0)
        return bool(val & self._target) if self._logic == "bit" else val == self._target

    @property
    def state(self):
        """Переопределяем отображение состояния текстом"""
        on = self.is_on
        if self._type == "heat":
            return "Нагрев" if on else "Охлаждение"
        if self._type == "err":
            return "АВАРИЯ" if on else "ОК"
        if self._type == "tmr":
            return "Активен" if on else "Выключен"
        if self._type == "lock":
            return "Заблокировано" if on else "Разблокировано"
        return "Включено" if on else "Выключено"
