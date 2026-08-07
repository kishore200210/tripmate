"""
app/modules/ai_agent/service.py

AI Agent Service — orchestrates DB memory, LangChain/LangGraph, and response mapping.
"""

import logging
import uuid
from uuid import UUID

from langchain_core.messages import AIMessage, HumanMessage

from app.modules.ai_agent.graph import compiled_graph
from app.modules.ai_agent.schemas import AgentChatRequest, AgentChatResponse
from app.modules.ai_concierge.enums import MessageRole
from app.modules.ai_concierge.models import ChatMessage
from app.modules.ai_concierge.repository import ChatMessageRepository
from app.modules.users.models import User
from app.shared.service import BaseService

logger = logging.getLogger(__name__)


class AIAgentService(BaseService[ChatMessageRepository]):
    """Service layer for AI Agent operations."""

    def __init__(self, repository: ChatMessageRepository) -> None:
        super().__init__(repository=repository)

    async def chat(
        self, session_id: UUID, payload: AgentChatRequest, current_user: User
    ) -> AgentChatResponse:
        """
        Processes a user message through the LangGraph AI Agent.
        1. Loads memory from DB.
        2. Invokes graph.
        3. Saves user and AI messages back to DB.
        """
        # 1. Fetch DB history for session context
        db_messages = await self.repository.get_session_messages(session_id, current_user.id)
        
        # 2. Map DB messages to LangChain message objects
        langchain_messages = []
        for msg in db_messages:
            if msg.role == MessageRole.USER:
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                langchain_messages.append(AIMessage(content=msg.content))

        # Add the new user message
        new_user_msg = HumanMessage(content=payload.message.strip())
        langchain_messages.append(new_user_msg)
        
        # 3. Save new user message to DB immediately
        user_db_msg = ChatMessage(
            id=uuid.uuid4(),
            user_id=current_user.id,
            session_id=session_id,
            role=MessageRole.USER,
            content=payload.message.strip(),
        )
        await self.repository.create(user_db_msg)

        # 4. Invoke LangGraph
        # LangGraph runs synchronously by default unless using astream/ainvoke with fully async nodes.
        # Since we use ChatOpenAI, `ainvoke` is natively supported.
        initial_state = {"messages": langchain_messages}
        
        try:
            # We use ainvoke for asynchronous execution of the graph
            final_state = await compiled_graph.ainvoke(initial_state)
            
            # The last message in the state is the AI's final response
            final_ai_msg = final_state["messages"][-1]
            ai_response_text = final_ai_msg.content
            
            # Extract tools used
            tools_used = []
            for msg in final_state["messages"][len(langchain_messages):]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for call in msg.tool_calls:
                        tools_used.append(call["name"])
            
            tools_used = list(set(tools_used))
            
        except Exception as e:
            logger.error("LangGraph Agent Error: %s", str(e))
            ai_response_text = "I'm sorry, I encountered an error while processing your request."
            tools_used = []

        # 5. Save AI's response to DB
        ai_db_msg = ChatMessage(
            id=uuid.uuid4(),
            user_id=current_user.id,
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=ai_response_text,
        )
        await self.repository.create(ai_db_msg)

        return AgentChatResponse(response=ai_response_text, tools_used=tools_used)
