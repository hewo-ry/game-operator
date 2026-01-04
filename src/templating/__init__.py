from enum import Enum

class Protocol(str, Enum):
    TCP = 'TCP'
    UDP = 'UDP'
    SCTP = "SCTP"

    def __str__(self) -> str:
        return self.value