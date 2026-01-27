import asyncio
import logging
from .hub import GTCVentHub
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "fan", "number", "binary_sensor", "climate", "select"]

async def async_setup_entry(hass, entry):
    host = entry.data["host"]
    port = entry.data.get("port", 502)
    
    hub = GTCVentHub(host, port)
    
    # Сохраняем хаб в hass.data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub
    
    # Пробуем первое чтение (без фанатизма, если ошибка - не страшно, цикл подхватит)
    try:
        await hub.async_update()
    except Exception as e:
        _LOGGER.warning("Первое чтение не удалось (контроллер занят?): %s", e)

    # Фоновая задача
    async def dynamic_poll():
        while True:
            # Динамическая пауза из hub.poll_interval (по умолчанию 5)
            interval = getattr(hub, 'poll_interval', 5)
            
            try:
                await hub.async_update()
            except asyncio.CancelledError:
                raise
            except Exception as err:
                _LOGGER.error("Ошибка в цикле опроса GTC: %s", err)
            
            await asyncio.sleep(interval)

    # Создаем задачу и ПРИКРЕПЛЯЕМ её к объекту hub, чтобы не потерять
    hub.poll_task = hass.async_create_background_task(dynamic_poll(), f"gtc_poll_{entry.entry_id}")
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    # 1. Сначала выгружаем платформы (сенсоры и т.д.)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # 2. Получаем хаб
        hub = hass.data[DOMAIN].pop(entry.entry_id, None)
        
        # 3. Гарантированно убиваем фоновую задачу
        if hub and hub.poll_task:
            hub.poll_task.cancel()
            try:
                # Ждем завершения задачи, чтобы освободить сокет
                await hub.poll_task
            except asyncio.CancelledError:
                pass
            
    return unload_ok
