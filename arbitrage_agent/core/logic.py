import operator
from typing import Annotated, TypedDict, Union

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

from django.conf import settings

# Import your tools from the other file
from .tools import search_internal_news, get_crypto_price

# --- 1. DEFINE STATE ---
# This is the "Memory" of the agent. It holds the conversation history.
class AgentState(TypedDict):
    # 'operator.add' ensures new messages are appended to history, not overwriting it
    messages: Annotated[list[BaseMessage], operator.add]

# --- 2. SETUP GRAPH ---
def build_agent_graph():
    # A. Define Tools & Model
    tools = [search_internal_news, get_crypto_price]

    # Use Gemini 1.5 Flash (Fast & Cheap) or Pro (Smarter)
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=settings.GEMINI_API_KEY, temperature=0)

    # B. Bind Tools
    # This replaces the old "ReAct Prompt". It tells Gemini:
    # "Here are functions you can call natively."
    model_with_tools = model.bind_tools(tools)

    # C. Define Nodes (The Steps)

    def call_model(state: AgentState):
        """The thinking step: LLM decides what to do based on history."""
        messages = state['messages']
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

    # LangGraph has a prebuilt node for running tools!
    tool_node = ToolNode(tools)

    # D. Define Edges (The Logic Flow)

    def should_continue(state: AgentState):
        """Decides: Do we need to run a tool, or are we done?"""
        last_message = state['messages'][-1]

        # If the LLM wants to call a tool, go to 'tools' node
        if last_message.tool_calls:
            return "tools"

        # Otherwise, stop
        return END

    # E. Build the Graph
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")

    # Conditional Edge: From 'agent', go to 'tools' or 'END'
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        ["tools", END]
    )

    # Automatic Edge: After running a tool, ALWAYS go back to agent to think again
    workflow.add_edge("tools", "agent")

    return workflow.compile()

# Initialize the graph ONCE when the server starts
agent_app = build_agent_graph()

# --- 3. THE PUBLIC FUNCTION ---
def ask_agent(user_query: str) -> str:
    """
    The entry point for your Django View.
    """

    # Define the "Persona" using a System Message
    system_instruction = SystemMessage(content="""
        You are a senior crypto analyst.
        You are skeptical, data-driven, and concise.

        PROTOCOL:
        1. ALWAYS search the internal news database (RAG) first.
        2. If news is relevant, check the current price using the tool.
        3. Synthesize both to answer if there is an opportunity.
        4. If you use a tool, cite it in your final answer.
    """)

    # Run the graph
    # We pass the System Instruction + User Query as the initial state
    final_state = agent_app.invoke({
        "messages": [
            system_instruction,
            HumanMessage(content=user_query)
        ]
    })

    # Return only the final text from the AI
    return final_state["messages"][-1].content
