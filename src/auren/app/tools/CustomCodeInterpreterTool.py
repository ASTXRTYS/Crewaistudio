import os
from typing import Optional, Type
from langchain.tools import Tool
from langchain_core.pydantic_v1 import BaseModel, Field
import importlib.util
#from pydantic.v1 import BaseModel, Field,root_validator
from pydantic import BaseModel, Field
import docker
import base64

class CustomCodeInterpreterSchema(BaseModel):
    """Input for CustomCodeInterpreterTool."""
    code: Optional[str] = Field(
        None,
        description="Python3 code used to be interpreted in the Docker container. ALWAYS PRINT the final result and the output of the code",
    )

    run_script: Optional[str] = Field(
        None,
        description="Relative path to the script to run in the Docker container. The script should contain the code to be executed.",
    )

    libraries_used: str = Field(
        ...,
        description="List of libraries used in the code with proper installing names separated by commas. Example: numpy,pandas,beautifulsoup4",
    )

    def check_code_or_run_script(cls, values):
        code = values.get('code')
        run_script = values.get('run_script')
        if not code and not run_script:
            raise ValueError('Either code or run_script must be provided')
        if code and run_script:
            raise ValueError('Only one of code or run_script should be provided')
        return values

class CustomCodeInterpreterToolInput(BaseModel):
    """Input for CustomCodeInterpreterTool"""
    query: str = Field(description="Input query")

def customcodeinterpretertool_func(query: str) -> str:
    """CustomCodeInterpreterTool tool"""
    pass

customcodeinterpretertool_tool = Tool(
    name="CustomCodeInterpreterTool",
    func=customcodeinterpretertool_func,
    description="""CustomCodeInterpreterTool tool""",
    args_schema=CustomCodeInterpreterToolInput
)