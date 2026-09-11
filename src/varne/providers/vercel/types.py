from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class VercelProject(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    id: str
    name: str
    account_id: str = Field(alias="accountId")


class VercelProjectsResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    projects: list[VercelProject]


def parse_projects(payload: str) -> list[VercelProject]:
    response = VercelProjectsResponse.model_validate_json(payload)
    return response.projects
