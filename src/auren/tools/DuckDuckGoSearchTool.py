from langchain.tools import Tool
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Optional, List
from duckduckgo_search import DDGS
from pydantic import BaseModel, Field, model_validator

class DuckDuckGoSearchToolInputSchema(BaseModel):
    query: str = Field(..., description="The specific query")
    max_results: int = Field(5, description="Maximum results")
    region: str = Field("fr-fr", description="Search region")
    safesearch: str = Field("moderate", description="Safesearch type")

class DuckDuckGoSearchToolInputSchemaFull(DuckDuckGoSearchToolInputSchema):
    domains: Optional[List[str]] = Field(default=None, description="Specific domains to search")
    time: Optional[str] = Field(None, description="Time range for results (d=day, w=week, m=month, y=year)")


class DuckDuckGoSearchToolInput(BaseModel):
    """Input for DuckDuckGoSearchTool"""
    query: str = Field(description="Input query")

def duckduckgosearchtool_func(query: str) -> str:
    """DuckDuckGoSearchTool tool"""
    
        return self._run(
            inputs.query,
            inputs.max_results,
            inputs.region,
            inputs.safesearch
        )

duckduckgosearchtool_tool = Tool(
    name="DuckDuckGoSearchTool",
    func=duckduckgosearchtool_func,
    description="""DuckDuckGoSearchTool tool""",
    args_schema=DuckDuckGoSearchToolInput
)