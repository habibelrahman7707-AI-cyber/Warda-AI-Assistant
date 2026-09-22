from crewai import Agent
from tools.browser_tools import navigate_to_url, click_element, fill_form_field, extract_page_text, close_browser
from core.llm_config import get_llm

def get_browser_agent():
    return Agent(
        role='Interactive Web Automator',
        goal='Navigate the web, interact with websites, fill out forms, book flights, and scrape data dynamically.',
        backstory='You are an expert at controlling a web browser. You can navigate to any URL, find the right selectors, click buttons, and type into input fields. When booking a flight or a restaurant, you navigate the site step-by-step. ALWAYS use "Extract Page Text" to read the page content before clicking or typing so you know the correct selectors to use. Close the browser when the task is fully complete.',
        verbose=True,
        allow_delegation=False,
        tools=[navigate_to_url, click_element, fill_form_field, extract_page_text, close_browser],
        llm=get_llm()
    )
