from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    
    configs = [
        # ТОЛЬКО АВАРИИ И ОШИБКИ (in_4, in_5, in_69, in_70)
        ("err_t1", 4, 1, "bit", "Ошибка: Датчик T1"),
        ("err_t2", 4, 2, "bit", "Ошибка: Датчик T2"),
        ("err_t3", 4, 4, "bit", "Ошибка: Датчик T3"),
        ("err_flt1", 4, 16, "bit", "Авария: 100% Фильтр 1"),
        ("err_water", 4, 32, "bit", "Авария: Нет теплоносителя"),
        ("err_frz_w", 4, 64, "bit", "Угроза: Заморозка (вода)"),
        ("err_frz_a", 4, 256, "bit", "Угроза: Заморозка (воздух)"),
        ("err_fan1", 4, 1024, "bit", "Авария: Вентилятор 1"),
        ("err_fire", 4, 2048, "bit", "Авария: Пожар"),
        ("err_ten", 4, 8192, "bit", "Авария: Перегрев калорифера"),
        ("err_ovrht", 5, 16, "bit", "Авария: Перегрев системы"),
        ("err_low", 5, 32, "bit", "Авария: Недогрев системы"),
        ("err_t4", 69, 1, "bit", "Ошибка: Датчик T4"),
        ("err_t5", 69, 2, "bit", "Ошибка: Датчик T5"),
        ("err_flt2", 69, 16, "bit", "Авария: 100% Фильтр 2"),
        ("err_preht", 69, 64, "bit", "Ошибка: Датчик предподогрева"),
        ("err_fan2", 69, 1024, "bit", "Авария: Вентилятор 2"),
        ("err_rec", 70, 4, "bit", "Угроза: Заморозка рекуператора")
    ]
    
    async_add_entities([GTCErrorSensor(hub, entry, *c) for c in configs], True)


class GTCErrorSensor(BinarySensorEntity):
    _attr_has_entity_name = False 
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    def __init__(self, hub, entry, key, address, target, logic, friendly_name):
        self._hub = hub
        self._address = address
        self._target = target
        self._logic = logic
        self._attr_name = friendly_name
        self._attr_unique_id = f"gtc_manual_v1_err_{key}"

    @property
    def device_info(self):
        info = {
            "identifiers": {(DOMAIN, "gtc_syberia")},
            "name": "GTC Syberia 5",
            "manufacturer": "GTC",
            # Добавляем IP и порт прямо в строку модели для отображения в карточке
            "model": f"Syberia 5 ({self._hub.host}:{self._hub.port})",
            # Эта строка создаст кнопку "Открыть веб-интерфейс" (если он висит на 80 порту)
            "configuration_url": f"http://{self._hub.host}"
        }
        if self._hub.sw_version:
            info["sw_version"] = self._hub.sw_version
        if self._hub.mac:
            import homeassistant.helpers.device_registry as dr
            info["connections"] = {(dr.CONNECTION_NETWORK_MAC, self._hub.mac)}
        return info

    @property
    def is_on(self):
        val = self._hub.data.get(f"in_{self._address}", 0)
        
        if self._logic == "bit":
            return bool(val & self._target)
        elif self._logic == "equal":
            return (val & 0x1F) == self._target
            
        return False