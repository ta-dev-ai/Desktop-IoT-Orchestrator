"""Device models for the MQTT device registry."""

from pydantic import BaseModel


class DeviceCreatePayload(BaseModel):
    name: str
    device_type: str = "generic"
    host: str = ""
    role: str = "subscriber"
    topics_sub: str = ""
    topics_pub: str = ""
    notes: str = ""
