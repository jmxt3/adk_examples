import os
import logging
from dotenv import load_dotenv
from google.adk.tools import FunctionTool
from google.adk.agents import SequentialAgent, LlmAgent, BaseAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types  # Used for Runner input/output

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


# Tool for the first agent
def process_step_1(tool_context: ToolContext) -> dict:
    """Tool for step 1: Updates state and returns a message."""
    logger.info("Tool 1: Processing and updating state['step1_status']")
    # Access and modify the shared session state via tool_context
    tool_context.state["step1_status"] = "completed"
    tool_context.state["step1_data"] = "Initial data processed"
    return {
        "status": "Step 1 Done",
        "message": "Initial processing complete.",
    }  # Return a result


# Tool for the second agent
def process_step_2(tool_context: ToolContext) -> dict:
    """Tool for step 2: Reads state from step 1, updates state, and returns a message."""
    logger.info(
        "Tool 2: Reading state['step1_data'] and updating state['step2_status']"
    )
    # Tools can read state set by previous steps/agents
    step1_data = tool_context.state.get("step1_data", "No data from step 1")
    logger.info(f"Tool 2: Read step1_data: {step1_data}")

    # Update state for this step
    tool_context.state["step2_status"] = "completed"
    tool_context.state["step2_processed_data"] = f"Processed: {step1_data}"
    return {"status": "Step 2 Done", "message": "Intermediate processing complete."}


# Tool for the third agent
def process_step_3(tool_context: ToolContext) -> dict:
    """Tool for step 3: Reads state from step 2, updates final state, and returns a message."""
    logger.info(
        "Tool 3: Reading state['step2_processed_data'] and updating state['step3_status']"
    )
    # Access state from previous steps
    step2_data = tool_context.state.get("step2_processed_data", "No data from step 2")
    logger.info(f"Tool 3: Read step2_processed_data: {step2_data}")

    # Update the final state before returning control
    # As per ADK's state management, modifying tool_context.state
    # within the tool function ensures the Runner commits these changes
    # when processing the tool's output Event.
    tool_context.state["step3_status"] = "completed"
    tool_context.state["final_result"] = f"Finalized: {step2_data}"
    tool_context.state["workflow_complete"] = True  # Mark workflow as complete

    logger.info("Tool 3: State updated. Workflow complete. Returning final result.")
    return {
        "status": "Step 3 Done",
        "message": "Final processing complete. This is the end of the workflow.",
        "workflow_complete": True,
    }  # Return a result with a signal that this is the final step


tool_1 = FunctionTool(func=process_step_1)
tool_2 = FunctionTool(func=process_step_2)
tool_3 = FunctionTool(func=process_step_3)

# --- Define Sub-Agents (LlmAgents) ---
# Each agent is instructed to use its specific tool

agent_step_1 = LlmAgent(
    name="AgentStep1",
    model=GEMINI_MODEL,
    instruction="You initiate the pipeline. Use the 'process_step_1_tool' to start processing.",
    description="First step agent."
    # output_key could be used here to save the agent's final LLM response to state,
    # but the requirement is for the *tool* to update state.
    ,
    tools=[tool_1],  # Include the tool
)

agent_step_2 = LlmAgent(
    name="AgentStep2",
    model=GEMINI_MODEL,
    instruction="You perform intermediate processing. Use the 'process_step_2_tool'. You have access to results from previous steps in state.",
    description="Second step agent.",
    tools=[tool_2],  # Include the tool
)

agent_step_3 = LlmAgent(
    name="AgentStep3",
    model=GEMINI_MODEL,
    instruction="You are the final agent in the workflow. Use the 'process_step_3_tool' to complete the workflow. You have access to all state from previous steps. After your task completes, the workflow will end.",
    description="Third and final step agent that concludes the workflow.",
    tools=[tool_3],  # Include the tool
)

# --- Define the SequentialAgent (Pipeline) ---
# This agent orchestrates the sub-agents in a fixed order.
# It is NOT an LLM agent for *flow control* [6, 66], but its sub-agents *can* be LLM agents [7, 44, 46].

root_agent = SequentialAgent(
    name="ProcessingPipeline",
    sub_agents=[
        agent_step_1,
        agent_step_2,
        agent_step_3,
    ],  # Agents will run in this exact order
    description="Orchestrates a three-step processing pipeline.",
)


# Function to expose the root agent to the ADK CLI
def get_agent() -> BaseAgent:
    """Returns the root agent for use with the ADK CLI."""
    return root_agent


# Session and Runner
session_service = InMemorySessionService()
session = session_service.create_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
)
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
logger.info(
    f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'"
)

# Simulate a user query to trigger the pipeline
user_query = types.Content(
    role="user", parts=[types.Part(text="Please start the processing pipeline.")]
)

logger.info(f"Starting pipeline with initial state: {session.state}")


# Run the agent asynchronously
async def run_pipeline():
    events = []
    workflow_done = False

    async for event in runner.run_async(
        user_id=session.user_id, session_id=session.id, new_message=user_query
    ):
        events.append(event)
        logger.info(f"Received event: {event}")

        # In a real application, you would process events here (e.g., display content to user)
        if event.is_final_response():
            logger.info(f"Pipeline finished with response: {event.content.parts.text}")
            workflow_done = True

    # After the run, check the session state to confirm workflow completion
    updated_session = session_service.get_session(session.user_id, session.id)

    if workflow_done:
        logger.info("✅ Sequential workflow execution completed successfully")
    else:
        logger.info("⚠️ Sequential workflow might have exited prematurely")

    logger.info(f"Final state after pipeline run: {updated_session.state}")


# Expected state keys: 'step1_status', 'step1_data', 'step2_status', 'step2_processed_data', 'step3_status', 'final_result'

# Only run the pipeline if this script is executed directly
# This prevents the asyncio error when running through ADK CLI
if __name__ == "__main__":
    import asyncio

    asyncio.run(run_pipeline())
