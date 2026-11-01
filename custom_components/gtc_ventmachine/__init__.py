from __future__ import annotations

import asyncio
import logging

from .const import DEFAULT_POLL_INTERVAL, DEFAULT_PORT, DEFAULT_SLAVE_ID, DOMAIN, PLATFORMS
from .hub import GTCVentHub

_LOGGER = logging.getLogger(__name__)


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
    hub.poll_task = hass.async_create_background_task(dynamic_poll(), f"gtc_poll_{entry.entry_id}")

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass, entry):
    """Выгрузка интеграции и остановка фонового опроса."""
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
            hub.close()
    return unload_ok


async def update_listener(hass, entry):
    """Перезагрузка при сохранении новых настроек."""
    await hass.config_entries.async_reload(entry.entry_id)


