import operator
from typing import Annotated, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

from django.conf import settings

from .tools import search_internal_news, get_crypto_price

class AgentState(TypedDict):
    # NOTE: 'operator.add' ensures new messages are appended to history, not overwriting it
    messages: Annotated[list[BaseMessage], operator.add]


def build_agent_graph() -> StateGraph:
    def agent_node(state: AgentState) -> AgentState:
        """The thinking step: LLM decides what to do based on history."""
        messages = state['messages']
        response = model.invoke(messages)
        return {"messages": [response]}

    def evaluate_agent_state(state: AgentState) -> str:
        # Evaluate if the LLM wants to call a tool or not
        last_message = state['messages'][-1]

        if last_message.tool_calls:
            return "tools"

        return END

    tools = [search_internal_news, get_crypto_price]
    tool_node = ToolNode(tools)

    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=settings.GEMINI_API_KEY, temperature=0)
    model = model.bind_tools(tools)

    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        evaluate_agent_state
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile()

# Initialize the graph ONCE when the server starts
agent_app = build_agent_graph()

def ask_agent(user_query: str) -> str:
    system_instruction = SystemMessage(content="""
        You are a senior crypto analyst.
        You are skeptical, data-driven, and concise.

        PROTOCOL:
        1. ALWAYS search the internal news database (RAG) first.
        2. If news is relevant, check the current price using the tool.
        3. Synthesize both to answer if there is an opportunity.
        4. If you use a tool, cite it in your final answer.
    """)

    final_state = agent_app.invoke({
        "messages": [
            system_instruction,
            HumanMessage(content=user_query)
        ]
    })

    return final_state["messages"][-1].content
