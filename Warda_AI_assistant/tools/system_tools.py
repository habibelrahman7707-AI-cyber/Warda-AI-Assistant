from crewai.tools import tool
import os
import subprocess

@tool("Execute System Command")
def execute_system_command(command: str) -> str:
    """
    Executes a shell command on the local Windows system.
    Use this to open applications (e.g., 'start spotify', 'start notepad', 'start chrome'), or run safe system queries.
    
    Args:
        command (str): The command to execute.
        
    Returns:
        str: Success or error message.
    """
    try:
        # Use subprocess for all commands to capture stdout/stderr
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0 and not result.stderr.strip():
            return f"Success: {result.stdout.strip() or 'Command executed successfully.'}"
        else:
            # Sometimes 'start' returns 0 but prints error to stderr
            err_msg = result.stderr.strip() or result.stdout.strip()
            return f"Error executing command: {err_msg}"
    except Exception as e:
        return f"Failed to execute command: {str(e)}"

@tool("Install Software")
def install_software_tool(package_name: str) -> str:
    """
    Installs applications and software using Windows Package Manager (winget).
    This automatically searches the Microsoft Store and web repositories.
    If it fails because multiple packages match, it will return the error with package IDs.
    
    Args:
        package_name (str): The name or ID of the software to install.
        
    Returns:
        str: Success or error message.
    """
    try:
        install_cmd = f"winget install \"{package_name}\" --silent --accept-package-agreements --accept-source-agreements"
        result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return f"Successfully installed {package_name}.\nOutput:\n{result.stdout.strip()}"
        else:
            return f"Failed to install {package_name}.\nError:\n{result.stderr.strip() or result.stdout.strip()}"
    except Exception as e:
        return f"Exception occurred while installing {package_name}: {str(e)}"
