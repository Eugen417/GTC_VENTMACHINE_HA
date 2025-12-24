import asyncio
from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval
from .hub import GTCVentHub
from .const import DOMAIN

# Платформы, которые мы поддерживаем
PLATFORMS = ["sensor", "fan", "number", "binary_sensor"]

async def async_setup_entry(hass, entry):
    # Извлекаем хост и порт из конфигурации (если порта нет, ставим 502)
    host = entry.data["host"]
    port = entry.data.get("port", 502)
    
    hub = GTCVentHub(host, port)
    
    # Первое чтение данных при запуске
    await hub.async_update()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    async def update_data(now):
        await hub.async_update()

    # Интервал обновления - 5 секунд. Слишком часто запрашивать нельзя, 
    # иначе Wi-Fi модуль GTC начнет выдавать ошибки.
    async_track_time_interval(hass, update_data, timedelta(seconds=5))
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    # Корректное выключение интеграции
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
