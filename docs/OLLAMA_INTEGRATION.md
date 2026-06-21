# Ollama Integration Guide — Running GRC_Claw locally with Open Source LLMs

This guide outlines how to:
1. Configure **GRC_Claw** to use local open-source models running on **Ollama** as the LLM provider.
2. Create a custom, pre-prompted **GRC_Claw Agent** directly inside Ollama using a `Modelfile`, making it compatible with any open-source agentic AI framework (e.g. LangGraph, CrewAI, AutoGen).

---

## Part 1: Configuring Ollama as the LLM Provider for GRC_Claw

GRC_Claw features Bring-Your-Own-Connector (BYOC) support. Since Ollama exposes an OpenAI-compatible API endpoint, you can wire it directly into the GRC_Claw connectors configuration.

### 1. Update `connectors.config.json`
Add the Ollama provider to the `llm` block in your `connectors.config.json` file (typically located in your application root or config folder):

```json
{
  "version": 1,
  "llm": [
    {
      "id": "ollama-local",
      "label": "Ollama Local",
      "kind": "openai_compatible",
      "baseUrl": "http://127.0.0.1:11434/v1",
      "apiKeyEnv": "OLLAMA_API_KEY",
      "defaultModel": "qwen2.5:14b"
    }
  ]
}
```

### 2. Set Environment Variables
Ollama does not require an API key by default. However, to satisfy the `apiKeyEnv` resolver in GRC_Claw, add a dummy value to your `.env` file:

```bash
OLLAMA_API_KEY=local_nopass
```

### 3. Pull the Target Model
Ensure your local Ollama server is running, and pull your model of choice (e.g. `qwen2.5:14b` or `llama3.1:8b` which have excellent reasoning capabilities):

```bash
ollama pull qwen2.5:14b
```

---

## Part 2: Creating a Custom GRC_Claw Model inside Ollama

To make any open-source model automatically compatible with GRC_Claw's custom tool-calling format (which uses markdown-anchored `TOOL_CALL` and `FINAL_ANSWER` blocks), you should build a customized Ollama model using a `Modelfile`.

### 1. Create a `Modelfile`
Create a file named `Modelfile` in the root of your GRC_Claw directory:

```dockerfile
# Start from a high-quality base reasoning model
FROM qwen2.5:14b

# Set model configuration options
PARAMETER temperature 0.2
PARAMETER num_ctx 16384

# Embed the GRC_Claw agent system prompt
SYSTEM """
You are a GRC_Claw Autonomous Compliance Agent. You operate inside an agentic gateway environment to discover, monitor, and remediate GRC and IAM controls.

You have access to MCP and connector tools. To invoke a tool, you MUST use the following markdown-anchored format:

TOOL_CALL: { "tool": "connector_id/tool_name", "arguments": { "arg1": "value1" } }

After outputting a TOOL_CALL, you must STOP generating text immediately and wait for the system response containing the tool's output.

Once you have gathered sufficient evidence and completed your task, output your final response in this exact format:

FINAL_ANSWER: Your summary here.

Ensure your reasoning is structured, concise, and focused on gathering inspectable evidence for audit trails.
"""
```

### 2. Build the Custom Model
Run the following command to compile and register your custom model in Ollama:

```bash
ollama create grc-claw-agent -f ./Modelfile
```

### 3. Verify the Model
Test that the model loads and responds in the custom format:

```bash
ollama run grc-claw-agent
>>> "How do you check for unused IAM credentials?"
```

---

## Part 3: Integrating with Open Source Agentic AI Frameworks

Once your custom model `grc-claw-agent` is registered in Ollama, you can call it from any open-source framework.

### CrewAI Integration
```python
from crewai import Agent
from langchain_community.llms import Ollama

# Load the local GRC_Claw-adapted model
llm = Ollama(model="grc-claw-agent")

grc_agent = Agent(
    role="GRC Compliance Officer",
    goal="Identify control drifts and prepare Statement of Applicability",
    backstory="An automated auditor running on GRC_Claw gateway",
    llm=llm
)
```

### LangGraph Integration
```python
from langchain_community.chat_models import ChatOllama

# Initialize the chat model pointing to your local agentic model
model = ChatOllama(
    model="grc-claw-agent",
    temperature=0.2
)
```
