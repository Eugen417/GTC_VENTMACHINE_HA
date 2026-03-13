from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    
    # ФОРМАТ: (ID, Регистр, Бит/Знач, Логика, Имя, ТИП_ТЕКСТА)
    configs = [
        # --- СТАТУСЫ УСТАНОВКИ (in_2 / Регистр 3) ---
        ("pwr", 2, 1, "bit", "Статус: Питание", "pwr"),
        ("trans", 2, 2, "bit", "Статус: Переходный процесс", "move"),
        ("heat_av", 2, 64, "bit", "Статус: Нагрев доступен", "std"),

        # --- ПРОЦЕССЫ (in_3 / Регистр 4, значения 1-12) ---
        ("d_open", 3, 1, "equal", "Открытие заслонки", "open"),
        ("preheat", 3, 2, "equal", "Предподогрев", "heat"),
        ("f_start", 3, 3, "equal", "Запуск вентилятора", "run"),
        ("north", 3, 4, "equal", "Северный старт", "std"),
        ("f_stop", 3, 5, "equal", "Выбег вентилятора", "move"),
        ("d_close", 3, 6, "equal", "Закрытие заслонки", "close"),
        ("gvs_o", 3, 8, "equal", "Клапан ГВС: Открытие", "open"),
        ("gvs_c", 3, 9, "equal", "Клапан ГВС: Закрытие", "close"),
        ("hvs_o", 3, 10, "equal", "Клапан ХВС: Открытие", "open"),
        ("hvs_c", 3, 11, "equal", "Клапан ХВС: Закрытие", "close"),
        ("rotor", 3, 12, "equal", "Разгон ротора", "move"),

        # --- АВАРИИ: Error_Code (in_4 / Регистр 5) ---
        ("err_t1", 4, 1, "bit", "Ошибка: Датчик T1", "err"),
        ("err_t2", 4, 2, "bit", "Ошибка: Датчик T2", "err"),
        ("err_t3", 4, 4, "bit", "Ошибка: Датчик T3", "err"),
        ("err_flt1", 4, 16, "bit", "Авария: 100% Фильтр 1", "err"),
        ("err_water", 4, 32, "bit", "Авария: Нет теплоносителя", "err"),
        ("err_frz_w", 4, 64, "bit", "Угроза: Заморозка (вода)", "err"),
        ("err_frz_a", 4, 256, "bit", "Угроза: Заморозка (воздух)", "err"),
        ("err_fan1", 4, 1024, "bit", "Авария: Вентилятор 1", "err"),
        ("err_fire", 4, 2048, "bit", "Авария: Пожар", "err"),
        ("err_ten", 4, 8192, "bit", "Авария: Перегрев калорифера", "err"),
        
        # --- АВАРИИ: Error_Code_1 (in_5 / Регистр 6) ---
        ("err_ovrht", 5, 16, "bit", "Авария: Перегрев системы", "err"),
        ("err_low", 5, 32, "bit", "Авария: Недогрев системы", "err"),
        ("lock", 5, 64, "bit", "Блокировка пульта (Внеш. контакт)", "lock"),

        # --- АВАРИИ: Error_Code_2 (in_69 / Регистр 70) ---
        ("err_t4", 69, 1, "bit", "Ошибка: Датчик T4", "err"),
        ("err_t5", 69, 2, "bit", "Ошибка: Датчик T5", "err"),
        ("err_flt2", 69, 16, "bit", "Авария: 100% Фильтр 2", "err"),
        ("err_preht", 69, 64, "bit", "Ошибка: Датчик предподогрева", "err"),
        ("err_fan2", 69, 1024, "bit", "Авария: Вентилятор 2", "err"),
        
        # --- АВАРИИ: Error_Code_3 (in_70 / Регистр 71) ---
        ("err_rec", 70, 4, "bit", "Угроза: Заморозка рекуператора", "err")
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
        self._attr_unique_id = f"gtc_manual_v1_b_{key}"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_class = None 

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, "gtc_syberia")}, name="GTC Syberia 5")

    @property
    def is_on(self):
        val = self._hub.data.get(f"in_{self._address}", 0)
        
        if self._logic == "bit":
            return bool(val & self._target)
        elif self._logic == "equal":
            # Выделяем только младшие 5 бит для корректного сравнения статусов
            return (val & 0x1F) == self._target
            
        return False

    @property
    def state(self):
        """Прямая подмена текста состояния"""
        is_active = self.is_on
        if self._type == "err":
            return "АВАРИЯ" if is_active else "ОК"
        if self._type == "pwr":
            return "Работает" if is_active else "Ожидание"
        if self._type == "move":
            return "Изменяется" if is_active else "Покой"
        if self._type == "open":
            return "Открывается" if is_active else "Покой"
        if self._type == "close":
            return "Закрывается" if is_active else "Покой"
        if self._type == "heat":
            return "Нагрев" if is_active else "Покой"
        if self._type == "run":
            return "Активно" if is_active else "Не активно"
        if self._type == "lock":
            return "Заблокировано" if is_active else "Свободно"
        return "Включено" if is_active else "Выключено"
