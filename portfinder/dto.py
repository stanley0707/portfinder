from dataclasses import dataclass
from enum import StrEnum


class IpVersion(StrEnum):
    IPV4 = "ipv4"
    IPV6 = "ipv6"


class Protocol(StrEnum):
    TCP = "tcp"
    UDP = "udp"
    HTTP = "http"
    HTTPS = "https"


@dataclass
class Result:
    host: str
    port: int
    ip_version: IpVersion
    protocols: list[Protocol]

    def to_dict(self):
        return {"host": self.host, "port": self.port, "ip_version": self.ip_version, "protocols": [self.protocols]}

    def __str__(self):
        return f"{self.host}:{self.port} [{self.ip_version}] ({','.join(self.protocols)})"

    def __repr__(self):
        return self.__str__()
