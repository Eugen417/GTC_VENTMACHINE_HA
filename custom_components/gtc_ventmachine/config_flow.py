import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DEFAULT_PORT, DEFAULT_SLAVE_ID, DOMAIN


class GTCConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input["host"].strip()
            port = int(user_input.get("port", DEFAULT_PORT))
            slave_id = int(user_input.get("slave_id", DEFAULT_SLAVE_ID))

            if not host:
                errors["host"] = "invalid_host"
            elif not (1 <= port <= 65535):
                errors["port"] = "invalid_port"
            elif not (1 <= slave_id <= 247):
                errors["slave_id"] = "invalid_slave"
            else:
                user_input["host"] = host
                user_input["port"] = port
                user_input["slave_id"] = slave_id
                return self.async_create_entry(title="GTC Syberia 5", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("host"): str,
                    vol.Optional("port", default=DEFAULT_PORT): int,
                    vol.Optional("slave_id", default=DEFAULT_SLAVE_ID): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return GTCOptionsFlowHandler()


class GTCOptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input["host"].strip()
            port = int(user_input.get("port", DEFAULT_PORT))
            slave_id = int(user_input.get("slave_id", DEFAULT_SLAVE_ID))

            if not host:
                errors["host"] = "invalid_host"
            elif not (1 <= port <= 65535):
                errors["port"] = "invalid_port"
            elif not (1 <= slave_id <= 247):
                errors["slave_id"] = "invalid_slave"
            else:
                user_input["host"] = host
                user_input["port"] = port
                user_input["slave_id"] = slave_id
                return self.async_create_entry(title="", data=user_input)

        current_host = self.config_entry.options.get("host", self.config_entry.data.get("host", ""))
        current_port = self.config_entry.options.get(
            "port", self.config_entry.data.get("port", DEFAULT_PORT)
        )
        current_slave_id = self.config_entry.options.get(
            "slave_id", self.config_entry.data.get("slave_id", DEFAULT_SLAVE_ID)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("host", default=current_host): str,
                    vol.Optional("port", default=current_port): int,
                    vol.Optional("slave_id", default=current_slave_id): int,
                }
            ),
            errors=errors,
        )

