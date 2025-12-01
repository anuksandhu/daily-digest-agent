"""
Weather Tool for Daily Digest
Fetches current weather and 5-day forecast using OpenWeather API
"""

import requests
from datetime import datetime
from typing import Dict, Any

from utils.config import get_config
from utils.logging import get_logger
from utils.metrics import get_metrics


logger = get_logger()
metrics = get_metrics()


def get_weather(location: str = None) -> Dict[str, Any]:
    """
    Fetches current weather and 5-day forecast for a location.
    
    This tool calls the OpenWeather API to retrieve factual, current weather data.
    All data includes timestamps and source attribution for validation.
    
    Args:
        location: City name, "City, State", or "City, Country" 
                 (e.g., "San Jose", "San Jose, CA", "London, UK")
                 If not provided, uses default from config.
    
    Returns:
        Dictionary containing:
        - location: Location name
        - current: Current weather conditions (temp, feels_like, humidity, description, icon)
        - forecast: 5-day forecast with daily summaries
        - timestamp: ISO format timestamp when data was fetched
        - source: Data source for validation
        - error: Error message if request failed
    
    Example:
        >>> weather = get_weather("San Jose, CA")
        >>> print(weather['current']['temp'])
        72.5
    """
    config = get_config()
    
    # Use provided location or default
    if location is None:
        location = config.default_location
    
    logger.info(f"Fetching weather data", location=location)
    metrics.start_timer("tool.get_weather")
    
    try:
        api_key = config.openweather_api_key
        base_url = "https://api.openweathermap.org/data/2.5"
        
        # Fetch current weather
        logger.debug("Requesting current weather", location=location)
        current_response = requests.get(
            f"{base_url}/weather",
            params={
                'q': location,
                'appid': api_key,
                'units': 'imperial'  # Fahrenheit
            },
            timeout=10
        )
        current_response.raise_for_status()
        current_data = current_response.json()
        
        # Fetch 5-day forecast
        logger.debug("Requesting 5-day forecast", location=location)
        forecast_response = requests.get(
            f"{base_url}/forecast",
            params={
                'q': location,
                'appid': api_key,
                'units': 'imperial'
            },
            timeout=10
        )
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        
        # Parse and structure the data
        result = {
            'location': current_data.get('name', location),
            'current': {
                'temp': round(current_data['main']['temp'], 1),
                'feels_like': round(current_data['main']['feels_like'], 1),
                'humidity': current_data['main']['humidity'],
                'description': current_data['weather'][0]['description'].capitalize(),
                'icon': current_data['weather'][0]['icon'],
                'wind_speed': round(current_data.get('wind', {}).get('speed', 0), 1)
            },
            'forecast': [],
            'timestamp': datetime.now().isoformat(),
            'source': 'OpenWeather API'
        }
        
        # Process forecast (get one reading per day, at noon)
        seen_dates = set()
        for item in forecast_data['list']:
            date_str = item['dt_txt'].split()[0]  # Get date part
            
            # Only take one reading per day (prefer around noon)
            if date_str not in seen_dates and len(result['forecast']) < 5:
                hour = int(item['dt_txt'].split()[1].split(':')[0])
                if hour >= 11 and hour <= 13:  # Noon reading
                    seen_dates.add(date_str)
                    result['forecast'].append({
                        'date': date_str,
                        'temp': round(item['main']['temp'], 1),
                        'description': item['weather'][0]['description'].capitalize(),
                        'icon': item['weather'][0]['icon']
                    })
        
        # If we didn't get 5 days (due to noon preference), fill with any available data
        if len(result['forecast']) < 5:
            seen_dates.clear()
            result['forecast'] = []
            for item in forecast_data['list'][::8]:  # Every 8th entry (24 hours)
                date_str = item['dt_txt'].split()[0]
                if date_str not in seen_dates and len(result['forecast']) < 5:
                    seen_dates.add(date_str)
                    result['forecast'].append({
                        'date': date_str,
                        'temp': round(item['main']['temp'], 1),
                        'description': item['weather'][0]['description'].capitalize(),
                        'icon': item['weather'][0]['icon']
                    })
        
        duration = metrics.stop_timer("tool.get_weather", {"tool": "get_weather", "type": "tool"})
        logger.info(
            f"Weather data fetched successfully",
            location=location,
            duration_ms=duration
        )
        
        return result
        
    except requests.exceptions.RequestException as e:
        duration = metrics.stop_timer("tool.get_weather", {"tool": "get_weather", "type": "tool"})
        metrics.increment("tool.error", {"tool": "get_weather"})
        
        logger.error(
            f"Failed to fetch weather data",
            exception=e,
            location=location,
            duration_ms=duration
        )
        
        # Return error with enough structure for graceful handling
        return {
            'error': str(e),
            'location': location,
            'timestamp': datetime.now().isoformat(),
            'source': 'OpenWeather API (failed)'
        }


def get_weather_icon_emoji(icon_code: str) -> str:
    """
    Convert OpenWeather icon code to emoji
    
    Args:
        icon_code: OpenWeather icon code (e.g., '01d', '10n')
    
    Returns:
        Emoji representation
    """
    icon_map = {
        '01d': '☀️',  # Clear sky day
        '01n': '🌙',  # Clear sky night
        '02d': '⛅',  # Few clouds day
        '02n': '☁️',  # Few clouds night
        '03d': '☁️',  # Scattered clouds
        '03n': '☁️',
        '04d': '☁️',  # Broken clouds
        '04n': '☁️',
        '09d': '🌧️',  # Shower rain
        '09n': '🌧️',
        '10d': '🌦️',  # Rain day
        '10n': '🌧️',  # Rain night
        '11d': '⛈️',  # Thunderstorm
        '11n': '⛈️',
        '13d': '❄️',  # Snow
        '13n': '❄️',
        '50d': '🌫️',  # Mist
        '50n': '🌫️',
    }
    return icon_map.get(icon_code, '🌤️')
