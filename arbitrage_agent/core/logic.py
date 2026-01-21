import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from .tools import search_internal_news, get_crypto_price

def ask_agent(user_query: str):
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    tools = [search_internal_news, get_crypto_price]

    # NOTE: Using standard ReAct prompt from the community (Reason + Act)
    prompt = hub.pull("hwchase17/react")

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    response = agent_executor.invoke({"input": user_query})

    return response['output']
