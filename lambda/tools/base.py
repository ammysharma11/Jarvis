"""Base class for tools"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ToolResult(BaseModel):
    """Standard tool result"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None  # Human-readable message


class BaseTool(ABC):
    """Base class for all tools"""
    
    name: str = ""
    description: str = ""
    parameters: Dict = {}
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool"""
        pass
    
    @classmethod
    def get_definition(cls) -> Dict:
        """Get OpenAI function definition"""
        return {
            "type": "function",
            "function": {
                "name": cls.name,
                "description": cls.description,
                "parameters": cls.parameters
            }
        }
