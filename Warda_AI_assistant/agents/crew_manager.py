import json
import os
import re
from crewai import Crew, Process, Task
from agents.search_agent import get_search_agent
from agents.file_agent import get_file_agent
from agents.comms_agent import get_comms_agent
from agents.system_agent import get_system_agent
from core.llm_config import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

def get_chat_llm():
    """Returns a standard LangChain ChatOpenAI object pointing to our local Auto-Swapping Proxy"""
    return ChatOpenAI(
        model="openai/gpt-oss-120b", 
        api_key="dummy_key_handled_by_proxy",
        base_url="http://127.0.0.1:3003/v1"
    )

def resolve_user_request(user_request: str, chat_history: str) -> str:
    """
    Uses the LLM to rewrite the user request so it stands alone, resolving pronouns from chat_history.
    """
    if not chat_history.strip():
        return user_request
        
    llm = get_chat_llm()
    sys_prompt = """You are a Context Resolver for an AI assistant.
Your ONLY job is to rewrite the user's current request so it is completely standalone.
Replace pronouns (it, this, them, he, she) with the actual entities mentioned in the Chat History.
If the request says 'delete it' and the history talks about 'iphone.txt', output 'delete iphone.txt'.
DO NOT answer the user. DO NOT execute the request. DO NOT write conversational text like "Here is the rewritten request:".
If the current request is already standalone, return it EXACTLY as is.
CRITICAL: Return ONLY the rewritten string, absolutely nothing else."""
    
    human_prompt = f"Chat History:\n{chat_history}\n\nCurrent Request:\n{user_request}\n\nRewritten Standalone Request:"
    
    try:
        response = llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=human_prompt)
        ])
        if isinstance(response.content, list):
            return "".join(b.get("text", "") for b in response.content if isinstance(b, dict)).strip()
        return response.content.strip()
    except Exception as e:
        print(f"Resolving failed: {e}")
        return user_request

def plan_tasks(resolved_request: str) -> list:
    """
    Uses the LLM to parse the resolved user request into a queue of tasks.
    Returns a list of dicts: [{"agent": "search_agent", "task": "..."}, ...]
    """
    llm = get_chat_llm()
    
    # Load learned rules from memory if they exist
    rules_context = ""
    rules_path = os.path.expanduser("~/Desktop/ai-agent/rules.txt")
    if os.path.exists(rules_path):
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                rules_content = f.read().strip()
                if rules_content:
                    rules_context = f"\nUSER PREFERENCES & LEARNED RULES:\n{rules_content}\n"
        except Exception:
            pass
            
    sys_prompt = """You are the orchestration planner for an AI assistant.
Your job is to analyze the user's request and break it down into a JSON array of tasks.

Available agents:
1. search_agent: For simple web searches (questions, prices, info) using DuckDuckGo.
2. file_agent: For creating, reading, moving local files, AND downloading files/media (PDFs, songs, videos) from the web.
3. comms_agent: For sending emails, AND ANYTHING RELATED TO WHATSAPP (reading chats, replying, checking new messages, transcribing voice notes).
4. chat: If the user is just saying 'hi', 'how are you', or asking a general question that DOES NOT require tools.
5. system_agent: For executing local system commands (e.g. open apps) AND installing software via Winget.
6. browser_agent: For complex web interactions, booking flights, reserving restaurants, navigating web pages, and filling forms.

RULES:
- Return ONLY a valid JSON array, nothing else. No markdown blocks like ```json.
- Order matters. Dependencies first.
- WhatsApp tasks MUST go to `comms_agent`. Example: "Check my whatsapp", "Summarize the voice note I got", "Send a message to John on Whatsapp".
- Search queries without transactions go to `search_agent`. DO NOT save results unless asked.
- Downloading songs/videos/books goes to `file_agent`. Use 'download_media' or 'download_file'.
- Installing software/apps goes to `system_agent`. Explicitly tell it to 'Use the Install Software tool'.
- Booking flights/restaurants or navigating specific complex sites interactively goes to `browser_agent`. Explicitly tell the `browser_agent` the starting URL.
- DO NOT use `browser_agent` just to search for information; use `search_agent`.
- STRICT RULE FOR FILE AGENT: When asking to save/create a file, explicitly tell it to use the 'write_file' tool. Deletions MUST use the 'delete_item' tool. To read a file, use the 'read_file' tool.
- STRICT RULE FOR SYSTEM COMMANDS: If the user asks to open an app or folder, route it to 'system_agent' using 'start'.
- STRICT RULE FOR LEARNING: If the user is teaching you a rule, route it to 'file_agent' to append to 'C:\\Users\\Habib\\Desktop\\ai-agent\\rules.txt'.
- STRICT RULE FOR PATHS: The user's name is Habib and their home directory is C:\\Users\\Habib. Use absolute paths.

[RULES_CONTEXT]
Example 1 (Install App):
[
  {"agent": "system_agent", "task": "Use the 'Install Software' tool to install Google Chrome"}
]

Example 2 (Download Song):
[
  {"agent": "file_agent", "task": "Use the 'download_media' tool to download the song 'Shape of You' to C:\\Users\\Habib\\Downloads"}
]

Example 3 (Book a Flight):
[
  {"agent": "browser_agent", "task": "Navigate to a flight booking site like skyscanner, search for flights from NY to LA, and click through the booking process until checkout."}
]
"""
    
    # Inject the rules context safely without f-string JSON formatting errors
    sys_prompt = sys_prompt.replace("[RULES_CONTEXT]", rules_context)

    try:
        response = llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=f"Current User Request: {resolved_request}")
        ])
        
        if isinstance(response.content, list):
            output = "".join(b.get("text", "") for b in response.content if isinstance(b, dict)).strip()
        else:
            output = response.content.strip()
        
        # Robustly extract JSON array using regex in case the model chatters
        match = re.search(r'\[\s*\{.*?\}\s*\]', output, re.DOTALL)
        if match:
            json_str = match.group(0)
            queue = json.loads(json_str)
            return queue
        else:
            raise ValueError(f"No valid JSON array found in output: {output}")
    except Exception as e:
        print(f"Planning failed or output invalid JSON: {e}")
        # Fallback to chat
        return [{"agent": "chat", "task": resolved_request}]

def execute_user_request(user_request: str, chat_history: str = "") -> str:
    """
    Takes a user request, plans a queue of tasks, and runs them sequentially.
    """
    search_agent = get_search_agent()
    file_agent = get_file_agent()
    comms_agent = get_comms_agent()
    system_agent = get_system_agent()
    
    from agents.browser_agent import get_browser_agent
    browser_agent = get_browser_agent()
    
    agent_map = {
        "search_agent": search_agent,
        "file_agent": file_agent,
        "comms_agent": comms_agent,
        "system_agent": system_agent,
        "browser_agent": browser_agent
    }
    
    # 1. Resolve Pronouns using Context Resolver
    resolved_request = resolve_user_request(user_request, chat_history)
    print(f"\n[RESOLVER] Original: {user_request}\n[RESOLVER] Resolved: {resolved_request}\n")
    
    # 2. Generate Queue using the Resolved Request ONLY
    task_queue = plan_tasks(resolved_request)
    print(f"\n[PLANNER] Generated Task Queue: {task_queue}\n")
    
    # Detect user language
    import re
    is_arabic = len(re.findall(r'[\u0600-\u06FF]', user_request)) > 0
    lang_instruction = "Arabic" if is_arabic else "English"
    
    # 3. Check if it's just a conversational chat
    if len(task_queue) == 1 and task_queue[0].get("agent") == "chat":
        llm = get_chat_llm()
        response = llm.invoke([
            SystemMessage(content=f"You are a helpful personal AI assistant. Reply naturally and friendly. Do not mention tasks or tools. CRITICAL: You MUST reply entirely in {lang_instruction}."),
            HumanMessage(content=f"History:\n{chat_history}\n\nUser: {user_request}")
        ])
        if isinstance(response.content, list):
            return "".join(b.get("text", "") for b in response.content if isinstance(b, dict))
        return response.content

    # 3. Build Sequential Tasks
    crew_tasks = []
    crew_agents = []
    
    for i, item in enumerate(task_queue):
        agent_name = item.get("agent")
        task_desc = item.get("task")
        
        if agent_name in agent_map:
            agent_obj = agent_map[agent_name]
            if agent_obj not in crew_agents:
                crew_agents.append(agent_obj)
                
            desc = task_desc
            if i > 0:
                desc += "\n\nCRITICAL INSTRUCTION: You MUST use the output/context provided by the previous task to complete your task IF they are related. If they are completely separate tasks (e.g. creating a folder AND opening an app), ignore the previous output and just execute your task."
                
            crew_tasks.append(
                Task(
                    description=desc,
                    expected_output=f"A summary of the action performed and the result. CRITICAL: You MUST write this final output entirely in {lang_instruction}.",
                    agent=agent_obj
                )
            )
            
    if not crew_tasks:
        return "No valid tasks could be planned based on your request."
        
    # 4. Execute Sequentially
    crew = Crew(
        agents=crew_agents,
        tasks=crew_tasks,
        process=Process.sequential,
        verbose=True
    )
    
    try:
        crew.kickoff()
    except Exception as e:
        print(f"\n[CrewManager] Execution warning/error: {e}")
    
    # 5. Aggregate Results
    final_results = []
    for idx, t in enumerate(crew_tasks):
        if hasattr(t, 'output') and t.output and hasattr(t.output, 'raw'):
            final_results.append(f"Task {idx+1}: {t.output.raw}")
        else:
            final_results.append(f"Task {idx+1}: I could not complete this task.")
            
    # Check if we have any valid results
    if all("I could not complete this task." in r for r in final_results):
        error_msg = "عذراً، لم أتمكن من إتمام هذه المهمة بسبب خطأ تقني." if is_arabic else "Sorry, I couldn't complete this task due to a technical error."
        return error_msg
        
    return "\n\n".join(final_results)
