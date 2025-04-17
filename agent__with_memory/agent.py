import os
import warnings
import logging
import datetime
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm  # For multi-model support
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types  # For creating message Content/Parts

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.ERROR,
)
logger = logging.getLogger(__name__)

# Ignore all warnings
# warnings.filterwarnings("ignore")

GOOGLE_MODEL = os.getenv("GOOGLE_MODEL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL")


# @title Define the get_weather Tool
def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city (e.g., "New York", "London", "Tokyo").

    Returns:
        dict: A dictionary containing the weather information.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'report' key with weather details.
              If 'error', includes an 'error_message' key.
    """
    # Best Practice: Log tool execution for easier debugging
    print(f"--- Tool: get_weather called for city: {city} ---")
    city_normalized = city.lower().replace(" ", "")  # Basic input normalization

    # Mock weather data for simplicity
    mock_weather_db = {
        "newyork": {
            "status": "success",
            "report": "The weather in New York is sunny with a temperature of 25°C.",
        },
        "london": {
            "status": "success",
            "report": "It's cloudy in London with a temperature of 15°C.",
        },
        "tokyo": {
            "status": "success",
            "report": "Tokyo is experiencing light rain and a temperature of 18°C.",
        },
    }

    # Best Practice: Handle potential errors gracefully within the tool
    if city_normalized in mock_weather_db:
        return mock_weather_db[city_normalized]
    else:
        return {
            "status": "error",
            "error_message": f"Sorry, I don't have weather information for '{city}'.",
        }


# @title Define the Weather Agent
# Use one of the model constants defined earlier
AGENT_MODEL = GOOGLE_MODEL  # Starting with a powerful Gemini model

root_agent = Agent(  # Renamed from weather_agent
    name="weather_agent_v1",
    model=AGENT_MODEL,  # Specifies the underlying LLM
    description="Provides weather information for specific cities.",  # Crucial for delegation later
    instruction="You are a helpful weather assistant. Your primary goal is to provide current weather reports. "
    "When the user asks for the weather in a specific city, "
    "you MUST use the 'get_weather' tool to find the information. "
    "Analyze the tool's response: if the status is 'error', inform the user politely about the error message. "
    "If the status is 'success', present the weather 'report' clearly and concisely to the user. "
    "Only use the tool when a city is mentioned for a weather request.",
    tools=[get_weather],  # Make the tool available to this agent
)
