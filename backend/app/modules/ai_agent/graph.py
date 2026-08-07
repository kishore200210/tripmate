"""
app/modules/ai_agent/graph.py

LangGraph compilation for the AI Agent.
"""

import logging
import os
from typing import Annotated

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from app.core.config import get_settings
from app.modules.ai_agent.tools import (
    get_currency_tool,
    get_weather_tool,
    generate_itinerary_pdf_tool,
    search_knowledge_base_tool,
    get_ml_recommendations_tool,
    analyze_image_tool,
)

logger = logging.getLogger(__name__)

AGENT_PROMPT = """You are TripMate's Smart AI Assistant.
You have access to powerful tools to assist users with their travel planning.
Follow these strict rules:
1. WEATHER: If the user asks about the weather, temperature, or rain, use `get_weather_tool`.
2. CURRENCY: If the user asks to convert money or budgets, use `get_currency_tool`.
3. PDF ITINERARY: If the user asks to generate, create, or export an itinerary PDF, use `generate_itinerary_pdf_tool`.
4. DESTINATION KNOWLEDGE: If the user asks about foods to try, packing lists, culture, or attractions, use `search_knowledge_base_tool`. 
5. ML RECOMMENDATIONS: If the user asks for trip ideas, destination recommendations, or says things like "I have $2000 and 5 days, where should I go?", use `get_ml_recommendations_tool`.
6. IMAGE ANALYSIS: If the user provides a photo URL or asks "Where is this image from?", use `analyze_image_tool`.
7. If a tool fails, inform the user gracefully.
Keep your responses helpful, engaging, and directly related to the user's travel needs.
"""

# 1. Define State
class AgentState(TypedDict):
    """The state of the AI Agent graph."""
    # add_messages appends new messages rather than overwriting
    messages: Annotated[list[BaseMessage], add_messages]


# 2. Configure Tools and Model
tools = [get_weather_tool, get_currency_tool, generate_itinerary_pdf_tool, search_knowledge_base_tool, get_ml_recommendations_tool, analyze_image_tool]

settings = get_settings()
api_key = settings.GROQ_API_KEY.strip() if settings.GROQ_API_KEY else ""

is_loaded = bool(api_key and api_key != "dummy-key" and api_key != "dummy-key-for-tests")
prefix = api_key[:6] if len(api_key) >= 6 else api_key
suffix = api_key[-4:] if len(api_key) >= 10 else ""
logger.info(
    "AI Agent ChatGroq Init — Loaded GROQ API Key: %s | Prefix: %s...%s | Length: %d",
    is_loaded, prefix, suffix, len(api_key)
)

llm = ChatGroq(
    model=settings.GROQ_MODEL, 
    temperature=0, 
    groq_api_key=api_key
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
