import os
import logging
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools import google_search

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.ERROR,
)
logger = logging.getLogger(__name__)

GOOGLE_MODEL = os.getenv("GOOGLE_MODEL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL")

root_agent = LlmAgent(  # Renamed from weather_agent
    name="basic_search_agent",
    model=GOOGLE_MODEL,  # Specifies the underlying LLM
    description="Agent to answer questions using Google Search.",
    instruction="You are an expert researcher. You always stick to the facts",
    tools=[google_search],  # List of tools the agent can use
)
