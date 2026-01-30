"""Weather tool"""
import httpx
from tools.base import BaseTool, ToolResult
from agent.config import settings


class WeatherTool(BaseTool):
    name = "get_weather"
    description = "Get current weather for a city. Use this when user asks about weather."
    parameters = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name, e.g., 'Mumbai', 'Delhi', 'Bangalore'"
            }
        },
        "required": ["city"]
    }
    
    def execute(self, city: str) -> ToolResult:
        """Get weather from OpenWeatherMap"""
        
        if not settings.openweather_api_key:
            return ToolResult(
                success=False,
                error="Weather API not configured"
            )
        
        try:
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": settings.openweather_api_key,
                "units": "metric"
            }
            
            with httpx.Client() as client:
                response = client.get(url, params=params, timeout=5.0)
                response.raise_for_status()
                data = response.json()
            
            weather_data = {
                "city": data["name"],
                "temperature": round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": round(data["wind"]["speed"] * 3.6)  # Convert to km/h
            }
            
            return ToolResult(
                success=True,
                data=weather_data,
                message=f"Weather in {weather_data['city']}: {weather_data['temperature']}°C, {weather_data['description']}"
            )
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return ToolResult(success=False, error=f"City '{city}' not found")
            return ToolResult(success=False, error=f"Weather API error: {e}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
