import os
import logging
from dotenv import load_dotenv
from google.adk.agents import ParallelAgent, LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.ERROR,
)
logger = logging.getLogger(__name__)

GEMINI_MODEL = os.getenv("GOOGLE_MODEL")

# --- Configuration ---
APP_NAME = "stateful_pipeline_app"
USER_ID = "user123"
SESSION_ID = "sessionABC"


# Define your two agents that will run in parallel
agent_for_task_a = LlmAgent(  # Using LlmAgent as it's a common agent type [5, 6, 9]
    name="TaskAgentA",
    model=GEMINI_MODEL,  # Assign a model [5, 6]
    instruction="Perform Task A independently and save result to state.",  # Define specific task instructions
    description="Agent responsible for Task A.",
)

agent_for_task_b = LlmAgent(
    name="TaskAgentB",
    model=GEMINI_MODEL,  # Assign the same or a different model
    instruction="Perform Task B independently and save result to state.",  # Define specific task instructions
    description="Agent responsible for Task B.",
)

# Create a ParallelAgent, listing the two agents in the sub_agents list
root_agent = ParallelAgent(
    name="ConcurrentTasksExecutor",
    sub_agents=[
        agent_for_task_a,
        agent_for_task_b,
    ],  # These agents will run in parallel [Based on description]
    description="Executes TaskAgentA and TaskAgentB concurrently.",
)


# Session and Runner
session_service = InMemorySessionService()
session = session_service.create_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
)
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
