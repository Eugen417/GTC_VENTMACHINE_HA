from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    
    # ФОРМАТ: (ID, Регистр, Бит/Знач, Логика, Имя, ТИП_ТЕКСТА)
    configs = [
        # --- СТАТУСЫ ---
        ("pwr", 2, 1, "bit", "Статус: Питание", "pwr"),             # Работает / Ожидание
        ("trans", 2, 2, "bit", "Статус: Переходный процесс", "move"), # Изменяется / Покой
        ("heat_av", 2, 64, "bit", "Статус: Нагрев доступен", "std"),  # Включено / Выключено

        # --- ПРОЦЕССЫ ---
        ("f_start", 3, 3, "equal", "Запуск вентилятора", "run"),      # Активно / Не активно
        ("d_open", 3, 1, "equal", "Открытие заслонки", "open"),       # Открывается / Покой
        ("d_close", 3, 6, "equal", "Закрытие заслонки", "close"),     # Закрывается / Покой
        ("preheat", 3, 2, "equal", "Предподогрев", "heat"),           # Нагрев / Покой
        ("north", 3, 4, "equal", "Северный старт", "std"),            # Включено / Выключено
        ("f_stop", 3, 5, "equal", "Выбег вентилятора", "move"),       # Изменяется / Покой

        # --- КЛАПАНЫ ---
        ("gvs_o", 3, 256, "bit", "Клапан ГВС: Открытие", "open"),
        ("gvs_c", 3, 512, "bit", "Клапан ГВС: Закрытие", "close"),
        ("hvs_o", 3, 1024, "bit", "Клапан ХВС: Открытие", "open"),
        ("hvs_c", 3, 2048, "bit", "Клапан ХВС: Закрытие", "close"),

        # --- АВАРИИ ---
        ("err_fire", 4, 1, "bit", "Авария: Пожар", "err"),
        ("err_ext", 4, 2, "bit", "Авария: Внешняя", "err"),
        ("err_frz", 4, 4, "bit", "Авария: Заморозка", "err"),
        ("err_ten", 4, 8, "bit", "Авария: Перегрев ТЭН", "err"),
        ("err_fan1", 4, 16, "bit", "Авария: Вентилятор 1", "err"),
        ("err_trm", 4, 32, "bit", "Авария: Термоконтакт", "err"),
        ("err_sns", 4, 64, "bit", "Авария: Датчик темп.", "err"),
        
        ("err_t1", 5, 1, "bit", "Ошибка: Датчик T1", "err"),
        ("err_t2", 5, 2, "bit", "Ошибка: Датчик T2", "err"),
        ("err_t3", 5, 4, "bit", "Ошибка: Датчик T3", "err"),
        ("err_low", 5, 32, "bit", "Авария: Недогрев", "err"),
        ("lock", 5, 64, "bit", "Блокировка пульта", "lock"),

        ("err_fan2", 69, 1024, "bit", "Авария: Вентилятор 2", "err"),
        ("err_flt2", 69, 2048, "bit", "Авария: Фильтр 2", "err"),
        ("err_t4", 70, 1, "bit", "Ошибка: Датчик T4", "err"),
        ("err_t5", 70, 2, "bit", "Ошибка: Датчик T5", "err"),
        ("err_rec", 70, 4, "bit", "Авария: Рекуператор", "err")
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
        self._attr_unique_id = f"gtc_manual_v1_{key}"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_class = None 

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, "gtc_syberia")}, name="GTC Syberia 5")

    @property
    def is_on(self):
        val = self._hub.data.get(f"in_{self._address}", 0)
        return bool(val & self._target) if self._logic == "bit" else val == self._target

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
