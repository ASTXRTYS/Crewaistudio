from typing import Optional
from crewai.tools import BaseTool
import requests
from pydantic import BaseModel, Field


class WeatherToolInputSchema(BaseModel):
    city: str = Field(..., description="The city name to get weather for")
    country_code: Optional[str] = Field(None, description="Country code (e.g., 'US', 'UK')")


class WeatherTool(BaseTool):
    name: str = "Get Weather"
    description: str = "Get current weather information for a specific city"
    args_schema = WeatherToolInputSchema

    def _run(self, city: str, country_code: Optional[str] = None) -> str:
        """
        Get weather information for a city using OpenWeatherMap API
        """
        try:
            # You would need to get an API key from OpenWeatherMap
            # For now, this is a template showing the structure
            api_key = "YOUR_API_KEY_HERE"  # Replace with actual API key
            
            location = f"{city},{country_code}" if country_code else city
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
            
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                weather_info = f"Weather in {city}: {data['weather'][0]['description']}, Temperature: {data['main']['temp']}°C, Humidity: {data['main']['humidity']}%"
                return weather_info
            else:
                return f"Error getting weather for {city}: {response.status_code}"
                
        except Exception as e:
            return f"Error: {str(e)}"

    def run(self, input_data: WeatherToolInputSchema) -> str:
        return self._run(
            city=input_data.city,
            country_code=input_data.country_code
        ) 