from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

import kopf
import yaml

from templating import Protocol
from templating.yaml_templates import deployment_template
from utils import keys_to_camel, ommit_none


class RestartPolicy(str, Enum):
    ALWAYS = "Always"
    ON_FAILURE = "OnFailure"
    NEVER = "Never"

    def __str__(self) -> str:
        return self.value


@dataclass
class VolumeMount:
    mount_path: str
    name: str
    read_only: bool | None = None


@dataclass
class PersistentVolumeClaim:
    claim_name: str
    read_only: bool | None = None


@dataclass
class Volume:
    name: str
    persistent_volume_claim: PersistentVolumeClaim


@dataclass
class Resources:
    memory: str
    cpu: str


@dataclass
class ResourceConfig:
    requests: Resources | None = None
    limits: Resources | None = None


@dataclass
class PortConfig:
    container_port: int
    name: str | None = None
    protocol: Protocol = Protocol.TCP
    host_port: int | None = None
    host_ip: str | None = None


@dataclass
class ContainerConfig:
    name: str
    image: str
    ports: list[PortConfig] | None = None
    resources: ResourceConfig | None = None
    volume_mounts: list[VolumeMount] | None = None
    env_from: list = field(default_factory=list)


@dataclass
class DeploymentConfig:
    name: str
    namespace: str
    containers: list[ContainerConfig]
    volumes: list[Volume] | None = None
    restart_policy: RestartPolicy = RestartPolicy.ALWAYS
    replicas: int = 1

    @staticmethod
    def from_spec(name, namespace, spec: dict[str, Any]):
        return DeploymentConfig(
            name=name,
            namespace=namespace,
            containers=[
                ContainerConfig(
                    name=f"{name}-server",
                    image=f"itzg/minecraft-server:{('java' + spec['javaVersion']) if 'javaVersion' in spec else 'latest'}",
                    volume_mounts=[
                        VolumeMount(mount_path="/data", name="server-data-volume")
                    ],
                    env_from=[
                        {"configMapRef": {"name": f"{name}-config"}},
                        {"secretRef": {"name": f"{name}-secret"}},
                    ],
                    ports=[
                        PortConfig(25565, "minecraft", Protocol.TCP),
                        PortConfig(25565, "query", Protocol.UDP),
                    ],
                )
            ],
            volumes=[
                Volume(
                    name="server-data-volume",
                    persistent_volume_claim=PersistentVolumeClaim(
                        claim_name=f"{name}-data"
                    ),
                )
            ],
        )

    def to_deployment(self, labels: dict[str, str] | None = None):
        data = keys_to_camel(ommit_none(asdict(self)))
        if not isinstance(data, dict):
            raise kopf.PermanentError(f"Error parsing deployment {data}")

        tmpl = yaml.safe_load(deployment_template)
        tmpl["metadata"]["name"] = data["name"]
        tmpl["metadata"]["namespace"] = data["namespace"]
        tmpl["metadata"]["labels"] = {} if labels is None else labels
        tmpl["spec"]["replicas"] = data["replicas"]
        tmpl["spec"]["selector"]["matchLabels"] = tmpl["metadata"]["labels"]
        tmpl["spec"]["template"]["metadata"]["labels"] = tmpl["metadata"]["labels"]
        tmpl["spec"]["template"]["spec"]["containers"] = data["containers"]
        tmpl["spec"]["template"]["spec"]["restartPolicy"] = data["restartPolicy"]
        tmpl["spec"]["template"]["spec"]["volumes"] = data["volumes"]
        return tmpl
