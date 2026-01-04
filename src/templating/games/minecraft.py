import random
import string
from dataclasses import asdict, dataclass, field, fields
from typing import Any

import yaml

from templating.yaml_templates import config_map_template, secret_template
from utils import ommit_empty, ommit_none


@dataclass
class MinecraftServerConfig:
    MOTD: str
    SERVER_NAME: str
    MEMORY: str
    MAX_MEMORY: str
    MAX_PLAYERS: int
    TYPE: str
    ENABLE_WHITELIST: bool = False
    ICON: str | None = None
    OVERRIDE_ICON: bool = False
    SERVER_PORT: int = 25565
    QUERY_PORT: int = 25565
    RCON_PORT: int = 25575
    CF_SERVER_MOD: str | None = None
    VERSION: str | None = None
    FORGE_VERSION: str | None = None
    TZ: str = "UTC"
    LEVEL: str = "world"
    PLUGINS: list[str] = field(default_factory=list)
    SPIGET_RESOURCES: list[str] = field(default_factory=list)
    USE_SIMD_FLAGS: bool = True
    MODRINTH_PROJECTS: list[str] = field(default_factory=list)
    extra_env: dict[str, str] = field(default_factory=dict)
    EULA: bool = True
    ENABLE_RCON: bool = True
    ENABLE_QUERY: bool = True
    SNOOPER_ENABLED: bool = False

    @staticmethod
    def from_spec(spec: dict[str, Any]):
        items: dict[str, Any] = {
            "MOTD": spec.get("motd"),
            "SERVER_NAME": spec.get("name"),
            "MEMORY": spec.get("memory"),
            "MAX_MEMORY": spec.get("maxMemory"),
            "MAX_PLAYERS": spec.get("maxPlayers"),
            "TYPE": spec.get("serverType"),
            "ENABLE_WHITELIST": spec.get("whitelist"),
            "VERSION": spec.get("version"),
            "TZ": spec.get("timeZone"),
            "LEVEL": spec.get("level"),
        }
        return MinecraftServerConfig(**items)

    def to_env(self) -> dict[str, str]:
        env_dict: dict[str, str] = {}
        for f in fields(self):
            if f.name != "extra_env":
                value = getattr(self, f.name)
                if isinstance(value, list):
                    env_dict[f.name] = ",".join(value)
                elif isinstance(value, bool):
                    env_dict[f.name] = "true" if value else "false"
                else:
                    if value:
                        env_dict[f.name] = str(value)
                    else:
                        env_dict[f.name] = value
        env_dict.update(self.extra_env)
        return ommit_empty(ommit_none(env_dict))

    def to_config_map(
        self,
        name: str,
        namespace: str = "default",
        labels: dict[str, str] | None = None,
    ):
        tmpl = yaml.safe_load(config_map_template)
        tmpl["metadata"]["name"] = name
        tmpl["metadata"]["namespace"] = namespace
        tmpl["metadata"]["labels"] = {} if labels is None else labels
        tmpl["data"] = self.to_env()
        return tmpl


@dataclass
class MinecraftServerSecrets:
    @staticmethod
    def generate_rcon_password(length: int = 32) -> str:
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    RCON_PASSWORD: str = generate_rcon_password()

    def to_secret(
        self,
        name: str,
        namespace: str = "default",
        labels: dict[str, str] | None = None,
    ):
        tmpl = yaml.safe_load(secret_template)
        tmpl["metadata"]["name"] = name
        tmpl["metadata"]["namespace"] = namespace
        tmpl["metadata"]["labels"] = {} if labels is None else labels
        tmpl["stringData"] = asdict(self)
        return tmpl
