from typing import Optional, Dict, Any
from langchain.tools import Tool
from langchain_core.pydantic_v1 import BaseModel, Field
import requests
from pydantic.v1 import BaseModel, Field


class CustomApiToolInputSchema(BaseModel):
    endpoint: str = Field(..., description="The specific endpoint for the API call")
    method: str = Field(..., description="HTTP method to use (GET, POST, PUT, DELETE)")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers to include in the request")
    query_params: Optional[Dict[str, Any]] = Field(None, description="Query parameters for the request")
    body: Optional[Dict[str, Any]] = Field(None, description="Body of the request for POST/PUT methods")

class CustomApiToolInput(BaseModel):
    """Input for CustomApiTool"""
    query: str = Field(description="Input query")

def customapitool_func(query: str) -> str:
    """CustomApiTool tool"""
    pass

customapitool_tool = Tool(
    name="CustomApiTool",
    func=customapitool_func,
    description="""CustomApiTool tool""",
    args_schema=CustomApiToolInput
)