"""Reminder tools"""
from datetime import datetime, timedelta
from typing import Optional
import re

from tools.base import BaseTool, ToolResult
from memory.models import Reminder


class SetReminderTool(BaseTool):
    name = "set_reminder"
    description = "Set a reminder for the user. Use when they want to be reminded about something."
    parameters = {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "What to remind about"
            },
            "time": {
                "type": "string",
                "description": "When to remind. Can be relative ('in 30 minutes', 'tomorrow at 9am') or absolute ('5pm', '8:00 PM')"
            },
            "repeat": {
                "type": "string",
                "enum": ["none", "daily", "weekly"],
                "description": "Whether to repeat the reminder"
            },
            "category": {
                "type": "string",
                "enum": ["medicine", "task", "event", "other"],
                "description": "Category of reminder"
            }
        },
        "required": ["message", "time"]
    }
    
    def __init__(self, storage, user_id: str):
        self.storage = storage
        self.user_id = user_id
    
    def execute(
        self,
        message: str,
        time: str,
        repeat: str = "none",
        category: str = "other"
    ) -> ToolResult:
        """Set a reminder"""
        
        try:
            remind_at = self._parse_time(time)
            
            if remind_at < datetime.utcnow():
                return ToolResult(
                    success=False,
                    error="Cannot set reminder in the past"
                )
            
            reminder = Reminder(
                user_id=self.user_id,
                message=message,
                remind_at=remind_at,
                repeat_pattern=repeat if repeat != "none" else None,
                category=category
            )
            
            saved = self.storage.add_reminder(reminder)
            
            # Format time for response
            time_str = remind_at.strftime("%I:%M %p on %B %d")
            
            return ToolResult(
                success=True,
                data={
                    "reminder_id": saved.id,
                    "message": message,
                    "remind_at": remind_at.isoformat(),
                    "repeat": repeat
                },
                message=f"Reminder set for {time_str}: {message}"
            )
            
        except ValueError as e:
            return ToolResult(success=False, error=str(e))
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to set reminder: {str(e)}")
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse natural language time to datetime"""
        now = datetime.utcnow()
        time_lower = time_str.lower().strip()
        
        # Relative times
        if "minute" in time_lower:
            match = re.search(r'(\d+)\s*minute', time_lower)
            if match:
                return now + timedelta(minutes=int(match.group(1)))
        
        if "hour" in time_lower:
            match = re.search(r'(\d+)\s*hour', time_lower)
            if match:
                return now + timedelta(hours=int(match.group(1)))
        
        if "tomorrow" in time_lower:
            base = now + timedelta(days=1)
            # Try to extract time
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_lower)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                period = time_match.group(3)
                if period == "pm" and hour != 12:
                    hour += 12
                elif period == "am" and hour == 12:
                    hour = 0
                return base.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return base.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Absolute times like "5pm", "8:30 AM"
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            period = time_match.group(3)
            
            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0
            
            result = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If time has passed today, set for tomorrow
            if result <= now:
                result += timedelta(days=1)
            
            return result
        
        raise ValueError(f"Could not understand time: {time_str}")


class GetRemindersTool(BaseTool):
    name = "get_reminders"
    description = "Get upcoming reminders for the user"
    parameters = {
        "type": "object",
        "properties": {
            "hours_ahead": {
                "type": "integer",
                "description": "How many hours ahead to look (default 24)"
            }
        },
        "required": []
    }
    
    def __init__(self, storage, user_id: str):
        self.storage = storage
        self.user_id = user_id
    
    def execute(self, hours_ahead: int = 24) -> ToolResult:
        """Get upcoming reminders"""
        
        try:
            reminders = self.storage.get_upcoming_reminders(
                self.user_id,
                hours_ahead=hours_ahead
            )
            
            if not reminders:
                return ToolResult(
                    success=True,
                    data={"reminders": []},
                    message="No upcoming reminders"
                )
            
            reminder_list = []
            for r in reminders:
                time_str = r.remind_at.strftime("%I:%M %p") if hasattr(r.remind_at, 'strftime') else str(r.remind_at)
                reminder_list.append({
                    "message": r.message,
                    "time": time_str,
                    "category": r.category
                })
            
            return ToolResult(
                success=True,
                data={"reminders": reminder_list},
                message=f"You have {len(reminders)} upcoming reminder(s)"
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))
