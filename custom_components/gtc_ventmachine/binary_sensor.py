from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    
    # Список всех бинарных сенсоров:
    # (Ключ перевода/ID, Регистр, Значение, Тип проверки, Класс устройства)
    # Тип "bit": проверяем наличие бита (val & target)
    # Тип "equal": проверяем точное совпадение (val == target)
    configs = [
        # --- Статусы из регистра 2 (State 0) ---
        ("gtc_power", 2, 1, "bit", BinarySensorDeviceClass.POWER),
        ("gtc_heat_mode", 2, 256, "bit", None),
        
        # --- Клапаны и заслонки из регистра 3 (State 1) ---
        # Используем RUNNING, так как HA не поддерживает OPENING для binary_sensor
        ("gtc_gvs_open", 3, 8, "equal", BinarySensorDeviceClass.RUNNING),
        ("gtc_gvs_close", 3, 9, "equal", BinarySensorDeviceClass.RUNNING),
        ("gtc_hvs_open", 3, 10, "equal", BinarySensorDeviceClass.RUNNING),
        ("gtc_hvs_close", 3, 11, "equal", BinarySensorDeviceClass.RUNNING),
        ("gtc_damper_open", 3, 1, "equal", BinarySensorDeviceClass.RUNNING),
        ("gtc_damper_close", 3, 6, "equal", BinarySensorDeviceClass.RUNNING),
        
        # --- Ошибки из регистра 5 (Error Code 1) ---
        ("gtc_error_t1", 5, 1, "bit", BinarySensorDeviceClass.PROBLEM),
        ("gtc_error_t2", 5, 2, "bit", BinarySensorDeviceClass.PROBLEM),
        ("gtc_error_t3", 5, 4, "bit", BinarySensorDeviceClass.PROBLEM),
        ("gtc_error_overheat", 5, 16, "bit", BinarySensorDeviceClass.PROBLEM),
        ("gtc_error_underheat", 5, 32, "bit", BinarySensorDeviceClass.PROBLEM),
        ("gtc_error_frost", 5, 8192, "bit", BinarySensorDeviceClass.PROBLEM),
    ]
    
    entities = [GTCBitSensor(hub, entry, *c) for c in configs]
    async_add_entities(entities, True)

class GTCBitSensor(BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, hub, entry, translation_key, address, target, logic, dev_class):
        self._hub = hub
        self._address = address
        self._target = target
        self._logic = logic
        
        # translation_key связывает сенсор с именем в ru.json
        self._attr_translation_key = translation_key
        self._attr_device_class = dev_class
        
        # Помещаем всё в диагностику, чтобы не захламлять главный экран
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_unique_id = f"gtc_bin_v10_{address}_{target}_{logic}"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, "gtc_syberia")},
            name="GTC Syberia 5"
        )

    @property
    def is_on(self):
        """Проверка состояния сенсора в зависимости от типа логики."""
        val = self._hub.data.get(f"in_{self._address}", 0)
        
        if self._logic == "bit":
            # Проверка конкретного бита
            return bool(val & self._target)
        
        # Проверка точного значения (для регистра 3)
        return val == self._target
