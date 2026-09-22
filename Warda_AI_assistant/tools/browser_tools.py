from crewai.tools import tool
from playwright.sync_api import sync_playwright, Page
import time

class BrowserSession:
    _playwright = None
    _browser = None
    _page = None

    @classmethod
    def get_page(cls) -> Page:
        if not cls._page:
            cls._playwright = sync_playwright().start()
            cls._browser = cls._playwright.chromium.launch(headless=False)
            cls._page = cls._browser.new_page()
        return cls._page

    @classmethod
    def close(cls):
        if cls._browser:
            cls._browser.close()
            cls._browser = None
        if cls._playwright:
            cls._playwright.stop()
            cls._playwright = None
        cls._page = None

@tool("Navigate to URL")
def navigate_to_url(url: str) -> str:
    """
    Navigates the browser to a specific URL.
    
    Args:
        url (str): The URL to navigate to (e.g., 'https://www.skyscanner.com').
        
    Returns:
        str: Success or error message.
    """
    try:
        if not url.startswith("http"):
            url = "https://" + url
        page = BrowserSession.get_page()
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        return f"Successfully navigated to {url}. Page title is '{page.title()}'"
    except Exception as e:
        return f"Error navigating to {url}: {str(e)}"

@tool("Click Element")
def click_element(selector: str) -> str:
    """
    Clicks an element on the current webpage using a CSS selector or text.
    
    Args:
        selector (str): Playwright selector (e.g., 'text="Search"', 'button.submit', '#id').
        
    Returns:
        str: Success or error message.
    """
    try:
        page = BrowserSession.get_page()
        page.locator(selector).first.click(timeout=10000)
        page.wait_for_load_state("networkidle")
        return f"Successfully clicked element: {selector}"
    except Exception as e:
        return f"Error clicking element '{selector}': {str(e)}"

@tool("Fill Form Field")
def fill_form_field(selector: str, text: str) -> str:
    """
    Fills an input field on the current webpage with the given text.
    
    Args:
        selector (str): Playwright selector for the input field.
        text (str): The text to type into the field.
        
    Returns:
        str: Success or error message.
    """
    try:
        page = BrowserSession.get_page()
        page.locator(selector).first.fill(text, timeout=10000)
        return f"Successfully filled '{selector}' with '{text}'"
    except Exception as e:
        return f"Error filling field '{selector}': {str(e)}"

@tool("Extract Page Text")
def extract_page_text() -> str:
    """
    Extracts all visible text from the current webpage.
    Useful for reading search results, checking if a booking succeeded, or reading articles.
    
    Returns:
        str: The visible text of the webpage.
    """
    try:
        page = BrowserSession.get_page()
        text = page.evaluate("document.body.innerText")
        # Return first 5000 characters to avoid context overflow
        return text[:5000]
    except Exception as e:
        return f"Error extracting text: {str(e)}"

@tool("Close Browser")
def close_browser() -> str:
    """
    Closes the interactive browser session when the task is fully complete.
    """
    try:
        BrowserSession.close()
        return "Browser successfully closed."
    except Exception as e:
        return f"Error closing browser: {str(e)}"
