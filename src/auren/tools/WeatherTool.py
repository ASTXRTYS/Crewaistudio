from typing import Optional
from langchain.tools import Tool
from langchain_core.pydantic_v1 import BaseModel, Field
import requests
from pydantic import BaseModel, Field


class WeatherToolInputSchema(BaseModel):
    city: str = Field(..., description="The city name to get weather for")
    country_code: Optional[str] = Field(None, description="Country code (e.g., 'US', 'UK')")


class WeatherToolInput(BaseModel):
    """Input for WeatherTool"""
    query: str = Field(description="Input query")

def weathertool_func(query: str) -> str:
    """WeatherTool tool"""
    pass

weathertool_tool = Tool(
    name="WeatherTool",
    func=weathertool_func,
    description="""WeatherTool tool""",
    args_schema=WeatherToolInput
)