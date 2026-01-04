from dataclasses import dataclass, asdict, field
from enum import Enum

import yaml
import kopf

from templating import Protocol
from utils import keys_to_camel, ommit_none
from templating.yaml_templates import node_port_service_template

class ServiceType(str, Enum):
    NodePort = "NodePort"
    LoadBalancer = "LoadBalancer"

    def __str__(self) -> str:
        return self.value

@dataclass
class NodePort:
    name: str
    port: int
    protocol: Protocol = Protocol.TCP
    target_port: int | str | None = None

@dataclass
class Service:
    type: ServiceType = ServiceType.LoadBalancer
    ports: list[NodePort] = field(default_factory=list)

    def to_service(self, name: str, namespace: str, app: str):
        data = keys_to_camel(ommit_none(asdict(self)))
        if not isinstance(data, dict):
            raise kopf.PermanentError(f"Error parsing deployment {data}")

        tmpl = yaml.safe_load(node_port_service_template)
        tmpl["metadata"]["name"] = name
        tmpl["metadata"]["namespace"] = namespace
        tmpl["spec"]["selector"]["app"] = app
        tmpl["spec"]["type"] = data["type"]
        tmpl["spec"]["ports"] = data["ports"]

        return tmpl
