import os
import logging
from dotenv import load_dotenv
from google.adk.agents import Agent, LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types  # Needed for types like Content

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


# Define the first agent that produces a result
# This agent's response will be analyzed by the router agent.
agent_one = Agent(
    name="ResultAgent",
    model=GEMINI_MODEL,  # Or your preferred Gemini model
    instruction="""
    You are ResultAgent. Your task is to process the input and provide a specific result indicator.
    If the user query mentions 'option A', respond with 'RESULT: option_A'.
    If the user query mentions 'option B', respond with 'RESULT: option_B'.
    Otherwise, respond with 'RESULT: unknown'.
    Keep your response concise, only providing the 'RESULT: ...' line.
    """,
)

# Define the agent for handling result 'option_A'
left_agent = Agent(
    name="LeftAgent",
    model=GEMINI_MODEL,  # Or your preferred Gemini model
    instruction="""
    You are LeftAgent. You have received control because the previous agent identified 'option A'.
    Confirm that you are handling option A.
    """,
)

# Define the agent for handling result 'option_B'
right_agent = Agent(
    name="RightAgent",
    model=GEMINI_MODEL,  # Or your preferred Gemini model
    instruction="""
    You are RightAgent. You have received control because the previous agent identified 'option B'.
    Confirm that you are handling option B.
    """,
)

# Define a Root LlmAgent that acts as the orchestrator and router.
# An LlmAgent with default flow ('auto') can perform agent transfer [3].
# Its instructions guide it to first call ResultAgent, then route based on the result.
root_agent = LlmAgent(
    name="OrchestratorAgent",
    model=GEMINI_MODEL,  # Or your preferred Gemini model
    instruction="""
    You are OrchestratorAgent. Your role is to direct user queries to the appropriate sub-agent workflow.
    Your available sub-agents are: ResultAgent, LeftAgent, RightAgent.
    
    Workflow:
    1. **Always start by sending the user query to the 'ResultAgent'.** Use the 'transfer_to_agent' tool to do this.
    2. After 'ResultAgent' responds, analyze its last response in the conversation history.
    3. **Based on 'ResultAgent's response, transfer to either 'LeftAgent' or 'RightAgent'.**
       - If 'ResultAgent' responded with 'RESULT: option_A', transfer control to the 'LeftAgent' using the 'transfer_to_agent' tool.
       - If 'ResultAgent' responded with 'RESULT: option_B', transfer control to the 'RightAgent' using the 'transfer_to_agent' tool.
    4. If 'ResultAgent' responded with 'RESULT: unknown' or anything else, inform the user that the request could not be categorized.
    """,
    sub_agents=[
        agent_one,  # The agent that produces the initial result
        left_agent,  # One possible next step
        right_agent,  # The other possible next step
    ],
    # LlmAgent defaults to 'auto' flow, which enables agent transfer [3].
    # The `transfer_to_agent` tool is implicitly available for LlmAgents with transfer enabled [4, 5].
)

# Session and Runner
session_service = InMemorySessionService()
session = session_service.create_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
)
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)


# To run this workflow, you would typically use a Runner:
# from google.adk.runners import InMemoryRunner
# runner = InMemoryRunner(root_agent)

# Example execution (simulated):
# When you run runner.run("Process query for option A"), the flow would be:
# 1. OrchestratorAgent receives input.
# 2. OrchestratorAgent's LLM (guided by instruction) uses 'transfer_to_agent' to call ResultAgent.
# 3. ResultAgent receives input, runs its instruction, and responds with 'RESULT: option_A'.
# 4. Control potentially returns to OrchestratorAgent (due to AutoFlow handling).
# 5. OrchestratorAgent's LLM sees ResultAgent's response in history [7-9].
# 6. OrchestratorAgent's LLM (guided by instruction) uses 'transfer_to_agent' to call LeftAgent.
# 7. LeftAgent receives input, runs its instruction, and responds confirming it's handling option A.
# 8. The workflow ends or control returns based on the flow of LeftAgent and OrchestratorAgent.

# If the input was "Process query for option B", OrchestratorAgent would transfer to RightAgent.
# If the input was "Process query for neither", OrchestratorAgent might respond itself after ResultAgent outputs 'RESULT: unknown'.
