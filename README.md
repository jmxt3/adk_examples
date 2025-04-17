# Agent Development Kit
An open-source AI agent framework integrated with Gemini and Google

## What is Agent Development Kit?¶
Agent Development Kit (ADK) is a flexible and modular framework for developing and deploying AI agents. ADK can be used with popular LLMs and open-source generative AI tools and is designed with a focus on tight integration with the Google ecosystem and Gemini models. ADK makes it easy to get started with simple agents powered by Gemini models and Google AI tools while providing the control and structure needed for more complex agent architectures and orchestration.

https://google.github.io/adk-docs/

## Setup

**Install python UV package manager**
- https://docs.astral.sh/uv/getting-started/installation/

then 👇

**1. Create the Virtual Enviroment**
```console
uv venv
```

**2. Install the Package Dependencies**
```console
uv pip install --upgrade -r pyproject.toml
```

**3. Rename the file .env.example to .env. This new file will hold your secret API keys, which must never be shared**
```console
mv multi_tool_agent/.env.example multi_tool_agent/.env
```

**4. Run the ADK enviroment**
```console
adk web
```