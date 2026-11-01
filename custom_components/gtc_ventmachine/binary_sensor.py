from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import GTCBaseEntity


async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]

    # ФОРМАТ: (ID, Регистр 0-based (PDF - 1), Битовая маска, Логика, Имя, Включен по умолчанию)
    configs = [
        ("err_t1", 4, 1, "bit", "Ошибка: Датчик T1", True),
        ("err_t2", 4, 2, "bit", "Ошибка: Датчик T2", True),
        ("err_t3", 4, 4, "bit", "Ошибка: Датчик T3", True),
        ("err_flt1", 4, 16, "bit", "Авария: 100% Фильтр 1", True),
        ("err_water", 4, 32, "bit", "Авария: Нет теплоносителя", False),
        ("err_frz_w", 4, 64, "bit", "Угроза: Заморозка (вода)", True),
        ("err_frz_cap", 4, 128, "bit", "Угроза: Заморозка (капилляр)", False),
        ("err_frz_a", 4, 256, "bit", "Угроза: Заморозка (воздух)", True),
        ("err_fan1", 4, 1024, "bit", "Авария: Вентилятор 1", True),
        ("err_fire", 4, 2048, "bit", "Авария: Пожар", True),
        ("err_ten", 4, 8192, "bit", "Авария: Перегрев калорифера", True),
        ("err_kkb1", 4, 16384, "bit", "Авария: Давление ККБ 1", False),
        ("err_kkb2", 4, 32768, "bit", "Авария: Давление ККБ 2", False),
        ("err_ovrht", 5, 16, "bit", "Авария: Перегрев системы", True),
        ("err_low", 5, 32, "bit", "Авария: Недогрев системы", True),
        ("err_t4", 69, 1, "bit", "Ошибка: Датчик T4", True),
        ("err_t5", 69, 2, "bit", "Ошибка: Датчик T5", True),
        ("err_flt2", 69, 16, "bit", "Авария: 100% Фильтр 2", True),
        ("err_preht", 69, 64, "bit", "Ошибка: Датчик предподогрева", True),
        ("err_fan2", 69, 1024, "bit", "Авария: Вентилятор 2", True),
        ("err_rec", 70, 4, "bit", "Угроза: Заморозка рекуператора", True),
    ]

    async_add_entities([GTCErrorSensor(hub, entry, *c) for c in configs])


class GTCErrorSensor(GTCBaseEntity, BinarySensorEntity):
    _attr_has_entity_name = False
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hub, entry, key, address, target, logic, friendly_name, enabled_default):
        super().__init__(hub)
        self._address = address
        self._target = target
        self._logic = logic
        self._attr_name = friendly_name
        self._attr_unique_id = f"gtc_manual_v1_err_{key}"
        self._attr_entity_registry_enabled_default = enabled_default

    @property
    def is_on(self) -> bool:
        val = self._hub.data.get(f"in_{self._address}", 0)

        if self._logic == "bit":
            return bool(val & self._target)
        if self._logic == "equal":
            return (val & 0x1F) == self._target

        return False
