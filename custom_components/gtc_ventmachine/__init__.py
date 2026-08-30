import asyncio
import logging
from .hub import GTCVentHub
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "fan", "number", "binary_sensor", "climate", "select"]

async def async_setup_entry(hass, entry):
    # Пытаемся получить параметры из измененных опций, если их нет - берем из базовой даты
    host = entry.options.get("host", entry.data.get("host"))
    port = entry.options.get("port", entry.data.get("port", 502))
    slave_id = entry.options.get("slave_id", entry.data.get("slave_id", 1))
    
    hub = GTCVentHub(host, port, slave_id)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub
    
    # Запрашиваем MAC и прошивку для карточки устройства
    await hub.async_init_device_info()
    
    try:
        await hub.async_update()
    except Exception as e:
        _LOGGER.warning("Первое чтение не удалось (контроллер занят?): %s", e)

    async def dynamic_poll():
        while True:
            interval = getattr(hub, 'poll_interval', 5)
            try:
                await hub.async_update()
            except asyncio.CancelledError:
                raise
            except Exception as err:
                _LOGGER.error("Ошибка в цикле опроса GTC: %s", err)
            await asyncio.sleep(interval)

    hub.poll_task = hass.async_create_background_task(dynamic_poll(), f"gtc_poll_{entry.entry_id}")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Добавляем слушатель, который будет реагировать на изменение настроек
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    return True

async def async_unload_entry(hass, entry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hub = hass.data[DOMAIN].pop(entry.entry_id, None)
        if hub and hub.poll_task:
            hub.poll_task.cancel()
            try:
                await hub.poll_task
            except asyncio.CancelledError:
                pass
    return unload_ok

async def update_listener(hass, entry):
    """Перезагрузка при сохранении новых настроек."""
    await hass.config_entries.async_reload(entry.entry_id)
