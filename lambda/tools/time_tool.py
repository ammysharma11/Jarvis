"""Time tool"""
from datetime import datetime
from tools.base import BaseTool, ToolResult


class CurrentTimeTool(BaseTool):
    name = "get_current_time"
    description = "Get the current time and date. Use when user asks what time it is."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    def execute(self) -> ToolResult:
        """Get current time"""
        now = datetime.now()
        
        # Format for voice
        time_str = now.strftime("%I:%M %p")  # 2:30 PM
        date_str = now.strftime("%A, %B %d")  # Thursday, January 30
        
        return ToolResult(
            success=True,
            data={
                "time": time_str,
                "date": date_str,
                "timestamp": now.isoformat()
            },
            message=f"It's {time_str} on {date_str}"
        )
