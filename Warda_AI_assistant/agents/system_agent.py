from crewai import Agent
from tools.system_tools import execute_system_command, install_software_tool
from core.llm_config import get_llm

def get_system_agent():
    return Agent(
        role='System Operations Specialist',
        goal='Execute local system commands on Windows safely based on user instructions, such as opening applications and installing software.',
        backstory='You are a system administrator for the local machine. You can execute commands (e.g., "start spotify") and install software using winget via the Install Software tool.',
        verbose=True,
        allow_delegation=False,
        tools=[execute_system_command, install_software_tool],
        llm=get_llm()
    )
