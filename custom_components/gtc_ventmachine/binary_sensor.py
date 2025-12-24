from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.const import STATE_ON, STATE_OFF
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    
    # (ID, Регистр, Бит/Значение, Тип, Русское имя)
    configs = [
        ("gtc_power", 2, 1, "bit", "Питание"),
        ("gtc_heat_mode", 2, 256, "bit", "Режим: Нагрев"),
        ("gtc_gvs_open", 3, 8, "equal", "Клапан ГВС: Открытие"),
        ("gtc_gvs_close", 3, 9, "equal", "Клапан ГВС: Закрытие"),
        ("gtc_hvs_open", 3, 10, "equal", "Клапан ХВС: Открытие"),
        ("gtc_hvs_close", 3, 11, "equal", "Клапан ХВС: Закрытие"),
        ("gtc_error_overheat", 5, 16, "bit", "Ошибка: Перегрев"),
        ("gtc_error_underheat", 5, 32, "bit", "Ошибка: Недогрев"),
        ("gtc_error_frost", 5, 8192, "bit", "Ошибка: Обмерзание"),
        ("gtc_error_t1", 5, 1, "bit", "Датчик T1 (Авария)"),
        ("gtc_error_t2", 5, 2, "bit", "Датчик T2 (Авария)"),
        ("gtc_error_t3", 5, 4, "bit", "Датчик T3 (Авария)"),
    ]
    
    async_add_entities([GTCBitSensor(hub, entry, *c) for c in configs], True)

class GTCBitSensor(BinarySensorEntity):
    # Убираем _attr_has_entity_name, чтобы имя не заменялось на имя устройства
    _attr_has_entity_name = False 

    def __init__(self, hub, entry, translation_key, address, target, logic, friendly_name):
        self._hub = hub
        self._address = address
        self._target = target
        self._logic = logic
        self._attr_translation_key = translation_key
        self._attr_name = friendly_name  # Прямое имя
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_unique_id = f"gtc_final_v14_{address}_{target}"

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, "gtc_syberia")}, name="GTC Syberia 5")

    @property
    def is_on(self):
        val = self._hub.data.get(f"in_{self._address}", 0)
        return bool(val & self._target) if self._logic == "bit" else val == self._target
