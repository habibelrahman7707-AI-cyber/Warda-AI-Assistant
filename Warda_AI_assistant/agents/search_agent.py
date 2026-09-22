from crewai import Agent
from crewai.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from core.llm_config import get_llm

ddg = DuckDuckGoSearchRun()

@tool("Search the Web")
def search_tool(query: str) -> str:
    """
    Search the web for the given query using DuckDuckGo and return the results.
    """
    return ddg.invoke(query)

def get_search_agent():
    return Agent(
        role='Senior Research Analyst',
        goal='Search the web and provide accurate, concise, and summarized answers to the user\'s queries.',
        backstory='You are an expert researcher. You know how to extract the most important information from the web quickly. CRITICAL: Do NOT perform more than 2 searches. As soon as you find ANY relevant information or price, IMMEDIATELY stop searching and provide the Final Answer. Do not over-research.',
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        tools=[search_tool],
        llm=get_llm()
    )
