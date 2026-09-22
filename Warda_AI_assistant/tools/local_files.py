from crewai.tools import tool
import os
import shutil

@tool("search_file")
def search_file(filename: str, start_path: str = "~") -> str:
    """
    Searches for a file by name recursively starting from the given directory.
    Use this FIRST if you don't know the exact absolute path of a file before attempting to read it.
    
    Args:
        filename (str): The name or part of the name of the file to search for.
        start_path (str): The directory to start searching from. Defaults to '~' (User Home).
        
    Returns:
        str: A list of matching absolute file paths, or an error/not found message.
    """
    try:
        start_path = os.path.expanduser(start_path)
        if not os.path.exists(start_path):
            return f"Error: Start path '{start_path}' does not exist."
            
        matches = []
        # Split filename into keywords to allow fuzzy matching (e.g. ignoring extra spaces)
        keywords = [k.lower() for k in filename.split() if k]
        
        # Prevent searching entire C drive to avoid massive hangs, default to home if too broad
        if start_path == "C:\\" or start_path == "/":
            start_path = os.path.expanduser("~")
            
        for root, dirs, files in os.walk(start_path):
            for file in files:
                file_lower = file.lower()
                if all(k in file_lower for k in keywords):
                    matches.append(os.path.join(root, file))
            if len(matches) >= 15:  # Limit results
                break
                
        if not matches:
            return f"No files found matching '{filename}' in {start_path} or its subdirectories."
        
        return "Found the following files (use these absolute paths for reading/modifying):\n" + "\n".join(matches)
    except Exception as e:
        return f"Error searching for file: {str(e)}"

@tool("list_directory")
def list_directory(path: str) -> str:
    """
    Lists the contents of a directory on the local machine.
    
    Args:
        path (str): The absolute path to the directory.
        
    Returns:
        str: A list of files and folders, or an error message.
    """
    try:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
        items = os.listdir(path)
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@tool("create_directory")
def create_directory(path: str) -> str:
    """
    Creates a new directory (folder) at the specified path.
    
    Args:
        path (str): The absolute path to the new directory.
        
    Returns:
        str: Success or error message.
    """
    try:
        path = os.path.expanduser(path)
        os.makedirs(path, exist_ok=True)
        return f"Successfully created directory at {path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"

@tool("read_file")
def read_file(path: str) -> str:
    """
    Reads the text content of a file on the local machine. Supports plain text files and PDFs.
    
    Args:
        path (str): The absolute path to the file.
        
    Returns:
        str: The content of the file, or an error message.
    """
    try:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
            
        if path.lower().endswith('.pdf'):
            try:
                import PyPDF2
            except ImportError:
                return "Error: PyPDF2 is not installed. Please install it to read PDFs."
                
            text = ""
            with open(path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            # Return first 8000 chars to avoid overwhelming the LLM context if it's too large
            return text[:8000] if text else "PDF appears to be empty or consists only of images."
            
        else:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content[:8000] # Limit content to prevent context overflow
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool("write_file")
def write_file(path: str, content: str) -> str:
    """
    Writes text content to a file on the local machine. Overwrites if it exists.
    
    Args:
        path (str): The absolute path to the file.
        content (str): The text to write.
        
    Returns:
        str: Success or error message.
    """
    try:
        path = os.path.expanduser(path)
        # Ensure the directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool("append_file")
def append_file(path: str, content: str) -> str:
    """
    Appends text content to a file on the local machine. Creates the file if it does not exist.
    
    Args:
        path (str): The absolute path to the file.
        content (str): The text to append.
        
    Returns:
        str: Success or error message.
    """
    try:
        path = os.path.expanduser(path)
        # Ensure the directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'a', encoding='utf-8') as f:
            f.write(content + "\n")
        return f"Successfully appended to {path}"
    except Exception as e:
        return f"Error appending file: {str(e)}"

@tool("delete_item")
def delete_item(path: str) -> str:
    """
    Deletes a file or an entire directory from the local machine.
    
    Args:
        path (str): The absolute path to the file or directory to delete.
        
    Returns:
        str: Success or error message.
    """
    try:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
            
        if os.path.isfile(path):
            os.remove(path)
            return f"Successfully deleted file {path}"
        else:
            shutil.rmtree(path)
            return f"Successfully deleted directory {path}"
    except Exception as e:
        return f"Error deleting item: {str(e)}"

@tool("move_item")
def move_item(source: str, destination: str) -> str:
    """
    Moves or renames a file or directory from source to destination.
    
    Args:
        source (str): The absolute path to the current file/directory.
        destination (str): The absolute path to the new location/name.
        
    Returns:
        str: Success or error message.
    """
    try:
        source = os.path.expanduser(source)
        destination = os.path.expanduser(destination)
        if not os.path.exists(source):
            return f"Error: Source path '{source}' does not exist."
            
        shutil.move(source, destination)
        return f"Successfully moved/renamed {source} to {destination}"
    except Exception as e:
        return f"Error moving item: {str(e)}"

@tool("download_file")
def download_file(url: str, destination: str) -> str:
    """
    Downloads a general file (PDF, Book, Image, zip, etc.) from a direct URL and saves it to the destination path.
    
    Args:
        url (str): The direct URL to the file.
        destination (str): The absolute path where the file should be saved (including filename).
        
    Returns:
        str: Success or error message.
    """
    import urllib.request
    try:
        destination = os.path.expanduser(destination)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        urllib.request.urlretrieve(url, destination)
        return f"Successfully downloaded file to {destination}"
    except Exception as e:
        return f"Error downloading file: {str(e)}"

@tool("download_media")
def download_media(url: str, destination_dir: str) -> str:
    """
    Downloads media (songs, videos, audio) from platforms like YouTube, SoundCloud, etc., using yt-dlp.
    
    Args:
        url (str): The URL of the video or song.
        destination_dir (str): The absolute path to the directory where it should be saved.
        
    Returns:
        str: Success or error message.
    """
    import subprocess
    try:
        destination_dir = os.path.expanduser(destination_dir)
        os.makedirs(destination_dir, exist_ok=True)
        # Use yt-dlp to download and extract audio in the best quality
        cmd = f"yt-dlp -x --audio-format mp3 -o \"{destination_dir}/%(title)s.%(ext)s\" \"{url}\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return f"Successfully downloaded media to {destination_dir}.\nOutput:\n{result.stdout.strip()}"
        else:
            return f"Error downloading media: {result.stderr.strip() or result.stdout.strip()}"
    except Exception as e:
        return f"Exception occurred while downloading media: {str(e)}"
