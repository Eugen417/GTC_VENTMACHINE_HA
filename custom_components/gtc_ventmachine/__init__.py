from __future__ import annotations

import asyncio
import logging

from homeassistant.helpers import entity_registry as er

from .const import DEFAULT_POLL_INTERVAL, DEFAULT_PORT, DEFAULT_SLAVE_ID, DOMAIN, PLATFORMS
from .hub import GTCVentHub

_LOGGER = logging.getLogger(__name__)


def _sync_hardware_entities(hass, entry, hub: GTCVentHub) -> None:
    """Автоматически скрывает или включает сущности в реестре HA по автоопределённой комплектации."""
    if not hub.hw_detected:
        return

    ent_reg = er.async_get(hass)
    rules = {
        ("number", f"{entry.entry_id}_supply_speed"): hub.separate_fans,
        ("number", f"{entry.entry_id}_exhaust_speed"): hub.separate_fans,
        ("sensor", "gtc_manual_v1_s_spd_exh"): hub.has_exhaust_fan,
        ("sensor", "gtc_manual_v1_s_t_water"): hub.has_water_heater,
        ("sensor", "gtc_manual_v1_s_t_recup"): hub.has_recup,
        ("sensor", "gtc_manual_v1_proc_gvs_o"): hub.has_water_heater,
        ("sensor", "gtc_manual_v1_proc_gvs_c"): hub.has_water_heater,
        ("sensor", "gtc_manual_v1_proc_rotor"): hub.has_rotor,
        ("binary_sensor", "gtc_manual_v1_err_err_t2"): hub.has_water_heater,
        ("binary_sensor", "gtc_manual_v1_err_err_water"): hub.has_water_heater,
        ("binary_sensor", "gtc_manual_v1_err_err_frz_w"): hub.has_water_heater,
        ("binary_sensor", "gtc_manual_v1_err_err_t5"): hub.has_recup,
        ("binary_sensor", "gtc_manual_v1_err_err_preht"): hub.has_recup,
        ("binary_sensor", "gtc_manual_v1_err_err_rec"): hub.has_recup,
        ("binary_sensor", "gtc_manual_v1_err_err_fan2"): hub.has_exhaust_fan,
        ("binary_sensor", "gtc_manual_v1_err_err_flt2"): hub.has_exhaust_fan,
    }

    for (domain, unique_id), should_enable in rules.items():
        entity_id = ent_reg.async_get_entity_id(domain, DOMAIN, unique_id)
        if not entity_id:
            continue
        reg_entry = ent_reg.async_get(entity_id)
        if not reg_entry:
            continue
        # Не трогаем сущности, которые пользователь вручную включил или отключил в UI
        if reg_entry.disabled_by == er.RegistryEntryDisabler.USER:
            continue
        if not should_enable and reg_entry.disabled_by is None:
            ent_reg.async_update_entry(
                entity_id, disabled_by=er.RegistryEntryDisabler.INTEGRATION
            )
        elif should_enable and reg_entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION:
            ent_reg.async_update_entry(entity_id, disabled_by=None)


async def async_setup_entry(hass, entry):
    """Настройка интеграции GTC Ventmachine из ConfigEntry."""
    host = entry.options.get("host", entry.data.get("host"))
    port = entry.options.get("port", entry.data.get("port", DEFAULT_PORT))
    slave_id = entry.options.get("slave_id", entry.data.get("slave_id", DEFAULT_SLAVE_ID))

    hub = GTCVentHub(host, port, slave_id)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    # Запрашиваем прошивку, MAC и конфигурацию железа для карточки устройства
    await hub.async_init_device_info()

    try:
        await hub.async_update()
    except Exception as err:
        _LOGGER.warning("Первое чтение не удалось (контроллер занят?): %s", err)

    async def dynamic_poll():
        while True:
            interval = getattr(hub, "poll_interval", DEFAULT_POLL_INTERVAL)
            await asyncio.sleep(interval)
            try:
                await hub.async_update()
            except asyncio.CancelledError:
                raise
            except Exception as err:
                _LOGGER.error("Ошибка в цикле опроса GTC: %s", err)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _sync_hardware_entities(hass, entry, hub)

    hub.poll_task = hass.async_create_background_task(dynamic_poll(), f"gtc_poll_{entry.entry_id}")

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass, entry):
    """Выгрузка интеграции и закрытие сокета."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hub: GTCVentHub | None = hass.data[DOMAIN].pop(entry.entry_id, None)
        if hub:
            if hub.poll_task:
                hub.poll_task.cancel()
                try:
                    await hub.poll_task
                except asyncio.CancelledError:
                    pass
            await asyncio.to_thread(hub.close)
    return unload_ok


async def update_listener(hass, entry):
    """Перезагрузка при сохранении новых настроек."""
    await hass.config_entries.async_reload(entry.entry_id)

