"""Request payloads for API commands."""

from pydantic import BaseModel


class PublishMessagePayload(BaseModel):
    topic: str = "temperature"
    message: str
