from crewai import LLM
import os

# Set Groq API Key
os.environ["GROQ_API_KEY"] = "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"
os.environ["GROQ_OPENAI_BASE"] = "https://api.groq.com/openai/v1"

def get_llm():
    """
    Returns a configured LLM instance to connect to our local Auto-Swapping Proxy.
    By mimicking OpenAI, we bypass the cache_breakpoint bug in Litellm/CrewAI.
    """
    return LLM(
        model="openai/openai/gpt-oss-120b",
        api_key="dummy_key_handled_by_proxy",
        base_url="http://127.0.0.1:3003/v1"
    )
