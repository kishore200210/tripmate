"""
app/modules/ai_agent/graph.py

LangGraph compilation for the AI Agent.
"""

import logging
import os
from typing import Annotated

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from app.modules.ai_agent.tools import get_currency_tool, get_weather_tool

logger = logging.getLogger(__name__)

AGENT_PROMPT = """You are TripMate's AI Assistant Agent.
You are equipped with tools to fetch the weather and calculate currency exchange rates.
Always use your tools to provide accurate, real-time-like information when users ask about weather or currency.
If a tool fails, inform the user gracefully.
Keep your responses helpful, engaging, and directly related to the user's travel needs.
"""

# 1. Define State
class AgentState(TypedDict):
    """The state of the AI Agent graph."""
    # add_messages appends new messages rather than overwriting
    messages: Annotated[list[BaseMessage], add_messages]


# 2. Configure Tools and Model
tools = [get_weather_tool, get_currency_tool]
# Use API key from env or dummy for tests
llm = ChatOpenAI(
    model="gpt-3.5-turbo", 
    temperature=0, 
    api_key=os.environ.get("OPENAI_API_KEY", "dummy-key-for-tests")
)
llm_with_tools = llm.bind_tools(tools)


# 3. Define Nodes
def call_model(state: AgentState) -> dict:
    """Invokes the LLM with the current state (message history)."""
    messages = state["messages"]
    
    # Ensure the system prompt is always present if not already
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=AGENT_PROMPT)] + messages
        
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# 4. Compile Graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
# ToolNode executes the tools requested by the LLM (handles parsing tool calls natively)
workflow.add_node("tools", ToolNode(tools))

workflow.add_edge(START, "agent")
# Conditional edge: if LLM returned tool calls, go to tools. Otherwise, END.
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

compiled_graph = workflow.compile()
