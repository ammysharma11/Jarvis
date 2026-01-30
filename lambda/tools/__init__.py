"""Tools registry"""
from typing import Dict, List, Any

from tools.base import BaseTool, ToolResult
from tools.weather import WeatherTool
from tools.calculator import CalculatorTool
from tools.time_tool import CurrentTimeTool
from tools.reminders import SetReminderTool, GetRemindersTool
from tools.grocery import AddToGroceryListTool, ViewGroceryListTool, CreateOrderRequestTool


# Stateless tools (no user context needed)
STATELESS_TOOLS = {
    "get_weather": WeatherTool,
    "calculator": CalculatorTool,
    "get_current_time": CurrentTimeTool,
}


def get_tool_definitions(user_id: str, storage) -> List[Dict[str, Any]]:
    """Get all tool definitions for OpenAI"""
    
    definitions = []
    
    # Add stateless tools
    for tool_cls in STATELESS_TOOLS.values():
        definitions.append(tool_cls.get_definition())
    
    # Add user-context tools
    definitions.extend([
        SetReminderTool.get_definition(),
        GetRemindersTool.get_definition(),
        AddToGroceryListTool.get_definition(),
        ViewGroceryListTool.get_definition(),
        CreateOrderRequestTool.get_definition(),
    ])
    
    return definitions


def get_tool_registry(user_id: str, storage) -> Dict[str, BaseTool]:
    """Get tool instances for execution"""
    
    registry = {}
    
    # Stateless tools
    for name, tool_cls in STATELESS_TOOLS.items():
        registry[name] = tool_cls()
    
    # User-context tools
    registry["set_reminder"] = SetReminderTool(storage, user_id)
    registry["get_reminders"] = GetRemindersTool(storage, user_id)
    registry["add_to_grocery_list"] = AddToGroceryListTool(storage, user_id, user_id)
    registry["view_grocery_list"] = ViewGroceryListTool(storage, user_id)
    registry["create_order_request"] = CreateOrderRequestTool(storage, user_id, user_id)
    
    return registry


__all__ = [
    "BaseTool", "ToolResult",
    "get_tool_definitions", "get_tool_registry",
    "WeatherTool", "CalculatorTool", "CurrentTimeTool",
    "SetReminderTool", "GetRemindersTool",
    "AddToGroceryListTool", "ViewGroceryListTool", "CreateOrderRequestTool",
]
