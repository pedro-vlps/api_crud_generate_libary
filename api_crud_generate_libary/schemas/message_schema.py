"""Response contract for an explicitly configured DELETE message."""

from pydantic import BaseModel, ConfigDict


class MessageSchema(BaseModel):
    """Wrap a successful operation's message."""

    model_config = ConfigDict(from_attributes=True)
    message: str
