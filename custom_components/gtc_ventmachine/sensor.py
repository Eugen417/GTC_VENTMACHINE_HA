from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from .const import DOMAIN

STATE_MAP = {
    0: "Ожидание", 1: "Открытие заслонки", 2: "Предподогрев",
    3: "Работа", 4: "Северный старт", 5: "Выбег",
    6: "Закрытие заслонки", 7: "Продувка", 12: "Разгон ротора"
}

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    sensors = [
        ("stg", 3, "stage", None, "Состояние Уст."),
        ("t_cur", 7, "temp", UnitOfTemperature.CELSIUS, "Текущая температура"),
        ("t_set", 31, "temp", UnitOfTemperature.CELSIUS, "Целевая температура"),
        ("t_out", 11, "temp", UnitOfTemperature.CELSIUS, "Наружная температура (T2)"),
        ("t_in", 57, "temp", UnitOfTemperature.CELSIUS, "Температура в помещении"),
        ("hum", 58, "as_is", PERCENTAGE, "Влажность"),
        ("spd", 25, "as_is", None, "Текущая скорость"),
        ("spd_set", 32, "as_is", None, "Целевая скорость"),
        ("flt", 14, "as_is", PERCENTAGE, "Загрязнение фильтра")
    ]
    async_add_entities([GTCSensor(hub, entry, *s) for s in sensors], True)

class GTCSensor(SensorEntity):
    _attr_has_entity_name = False
    def __init__(self, hub, entry, key, address, mode, unit, friendly_name):
        self._hub = hub
        self._address = address
        self._mode = mode
        self._attr_native_unit_of_measurement = unit
        self._attr_name = friendly_name
        self._attr_unique_id = f"gtc_manual_v1_s_{key}"

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, "gtc_syberia")}, name="GTC Syberia 5")

    @property
    def native_value(self):
        val = self._hub.data.get(f"in_{self._address}")
        if val is None: return None
        if self._mode == "temp":
            if val > 32767: val -= 65536
            return round(float(val) * 0.1, 1)
        if self._mode == "stage":
            if val == 0:
                pwr = self._hub.data.get("in_2", 0)
                return "Работа" if (pwr & 1) else "Ожидание"
            return STATE_MAP.get(val, f"Код {val}")
        return val
