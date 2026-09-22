from crewai import Agent
from tools.local_files import list_directory, create_directory, read_file, write_file, append_file, delete_item, move_item, download_file, download_media, search_file
from core.llm_config import get_llm

def get_file_agent():
    return Agent(
        role='Local File System Manager',
        goal='Read, write, organize, move, and delete files and folders on the local computer safely, and download files or media from the web based on user instructions.',
        backstory='You are a meticulous file manager. You know how to read files, understand their contents, create new folders, move files around, delete items, and download items. CRITICAL: If you don\'t know the exact absolute path of a file, ALWAYS use the "search_file" tool first instead of list_directory. When asked to "download a book" or general file, use the "download_file" tool. When asked to download a song or video, use the "download_media" tool. When asked to "save", "store", or "create" a file, you ALWAYS use the "write_file" tool. When asked to "append" or "learn a rule", you ALWAYS use the "append_file" tool. CRITICAL: When you provide the Final Answer, DO NOT attempt to call any tools.',
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        tools=[list_directory, create_directory, read_file, write_file, append_file, delete_item, move_item, download_file, download_media, search_file],
        llm=get_llm()
    )
