import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN

class GTCConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="GTC Syberia 5", data=user_input)
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Optional("port", default=502): int,
                vol.Optional("slave_id", default=1): int,
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        # В новых версиях HA мы возвращаем класс без передачи config_entry
        return GTCOptionsFlowHandler()

class GTCOptionsFlowHandler(config_entries.OptionsFlow):
    # Метод __init__ больше не нужен, self.config_entry формируется автоматически "под капотом"

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Безопасное чтение текущих настроек
        current_host = self.config_entry.options.get("host", self.config_entry.data.get("host", ""))
        current_port = self.config_entry.options.get("port", self.config_entry.data.get("port", 502))
        current_slave_id = self.config_entry.options.get("slave_id", self.config_entry.data.get("slave_id", 1))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("host", default=current_host): str,
                vol.Optional("port", default=current_port): int,
                vol.Optional("slave_id", default=current_slave_id): int,
            }),
        )
