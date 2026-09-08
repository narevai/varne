from pydantic import BaseModel


class JsonPlaceholderPost(BaseModel):
    body: str
