import yaml
from typing import Any
from enum import Enum
from dataclasses import dataclass, field, asdict

from templating.yaml_templates import pvc_template

class AccessMode(str, Enum):
    ReadWriteOnce = "ReadWriteOnce"
    ReadOnlyMany = "ReadOnlyMany"
    ReadWriteMany = "ReadWriteMany"
    ReadWriteOncePod = "ReadWriteOncePod"

    def __str__(self) -> str:
        return self.value
    
def get_default_access_modes():
    return [AccessMode.ReadWriteOnce]

@dataclass
class PersistentVolumeClaim:
    storage_size: str
    storage_class: str
    access_modes: list[AccessMode] = field(default_factory=get_default_access_modes)

    @staticmethod
    def from_spec(spec: dict[str, Any], *, access_modes: list[AccessMode] | None = None):
        if access_modes is None:
            return PersistentVolumeClaim(spec['size'], spec['class'])
        else:
            return PersistentVolumeClaim(spec["size"], spec["class"], access_modes)
    
    def to_pvc(self, name: str, namespace: str = "default", labels: dict[str, str] | None = None):
        tmpl = yaml.safe_load(pvc_template)
        tmpl["metadata"]["name"] = name
        tmpl["metadata"]["namespace"] = namespace
        tmpl["metadata"]["labels"] = {} if labels is None else labels
        tmpl["spec"]["storageClassName"] = self.storage_class
        tmpl["spec"]["accessModes"] = [str(a) for a in self.access_modes]
        tmpl["spec"]["resources"]["requests"]["storage"] = self.storage_size
        return tmpl
