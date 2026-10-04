from pydantic import BaseModel


class OsFacts(BaseModel):
    id: str
    version: str


class Facts(BaseModel):
    os: OsFacts
