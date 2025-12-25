import asyncio
from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval
from .hub import GTCVentHub
from .const import DOMAIN

# Добавляем "climate" в список
PLATFORMS = ["sensor", "fan", "number", "binary_sensor", "climate"]

async def async_setup_entry(hass, entry):
    host = entry.data["host"]
    port = entry.data.get("port", 502)
    
    hub = GTCVentHub(host, port)
    
    # Первое чтение данных при запуске
    await hub.async_update()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    async def update_data(now):
        await hub.async_update()

    # Сохраняем ссылку на таймер, чтобы его можно было остановить
    remove_interval = async_track_time_interval(hass, update_data, timedelta(seconds=5))
    entry.async_on_unload(remove_interval)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    # Корректное выключение интеграции и всех платформ из списка
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
