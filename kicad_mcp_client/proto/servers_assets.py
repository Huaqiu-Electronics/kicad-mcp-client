from mcp import ListPromptsResult, ListResourcesResult, ListToolsResult
from pydantic import BaseModel


class ServersAssets(BaseModel):
    assets: dict[str, list[ListResourcesResult | ListPromptsResult | ListToolsResult]]
