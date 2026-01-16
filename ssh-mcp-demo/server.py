#!/usr/bin/env python3
"""
SSH MCP Server - Upload files and execute remote scripts via SSH
"""
import os
import json
from pathlib import Path
from typing import Optional
import paramiko
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("SSH File Transfer Server")

# Load configuration
CONFIG_FILE = Path(__file__).parent / "config.json"

def load_config() -> dict:
    """Load SSH configuration from config.json"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_ssh_client(host: str, port: int, username: str, password: Optional[str] = None,
                   key_file: Optional[str] = None) -> paramiko.SSHClient:
    """Create and return an SSH client connection"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if key_file and os.path.exists(key_file):
        client.connect(hostname=host, port=port, username=username, key_filename=key_file)
    else:
        client.connect(hostname=host, port=port, username=username, password=password)

    return client

@mcp.tool()
def upload_file(
    local_file: str,
    remote_dir: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    key_file: Optional[str] = None
) -> str:
    """
    Upload a local file to a remote server via SSH/SFTP

    Args:
        local_file: Path to the local file to upload
        remote_dir: Remote directory path (uses config.json default_remote_dir if not provided)
        host: SSH host (uses config.json if not provided)
        port: SSH port (uses config.json if not provided)
        username: SSH username (uses config.json if not provided)
        password: SSH password (optional, uses config.json if not provided)
        key_file: Path to SSH private key file (optional)

    Returns:
        Success message with remote file path
    """
    try:
        # Load config for missing parameters
        config = load_config()
        host = host or config.get('host')
        port = port or config.get('port', 22)
        username = username or config.get('username')
        password = password or config.get('password')
        key_file = key_file or config.get('key_file')
        remote_dir = remote_dir or config.get('default_remote_dir')

        if not all([host, username, local_file, remote_dir]):
            return "Error: Missing required parameters (host, username, local_file, remote_dir)"

        # Check if local file exists
        if not os.path.exists(local_file):
            return f"Error: Local file '{local_file}' does not exist"

        # Get filename
        filename = os.path.basename(local_file)
        remote_file = os.path.join(remote_dir, filename).replace('\\', '/')

        # Connect via SSH
        client = get_ssh_client(host, port, username, password, key_file)
        sftp = client.open_sftp()

        # Create remote directory if it doesn't exist
        try:
            sftp.stat(remote_dir)
        except FileNotFoundError:
            # Try to create the directory
            sftp.mkdir(remote_dir)

        # Upload file
        sftp.put(local_file, remote_file)
        sftp.close()
        client.close()

        return f"Successfully uploaded '{local_file}' to '{remote_file}' on {host}"

    except Exception as e:
        return f"Error uploading file: {str(e)}"

@mcp.tool()
def execute_remote_script(
    script_path: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    key_file: Optional[str] = None,
    args: Optional[str] = None
) -> str:
    """
    Execute a script on the remote server via SSH

    Args:
        script_path: Path to the script on the remote server (uses config.json default_script if not provided)
        host: SSH host (uses config.json if not provided)
        port: SSH port (uses config.json if not provided)
        username: SSH username (uses config.json if not provided)
        password: SSH password (optional, uses config.json if not provided)
        key_file: Path to SSH private key file (optional)
        args: Optional arguments to pass to the script

    Returns:
        Script execution output
    """
    try:
        # Load config for missing parameters
        config = load_config()
        host = host or config.get('host')
        port = port or config.get('port', 22)
        username = username or config.get('username')
        password = password or config.get('password')
        key_file = key_file or config.get('key_file')

        # Use default script from config if not provided
        if not script_path:
            default_remote_dir = config.get('default_remote_dir', '')
            default_script = config.get('default_script', 'run.sh')
            if default_remote_dir:
                script_path = f"{default_remote_dir}/{default_script}".replace('//', '/')
            else:
                script_path = default_script

        if not all([host, username, script_path]):
            return "Error: Missing required parameters (host, username, script_path)"

        # Build command
        command = script_path
        if args:
            command = f"{script_path} {args}"

        # Connect via SSH and execute
        client = get_ssh_client(host, port, username, password, key_file)
        stdin, stdout, stderr = client.exec_command(command)

        # Get output
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        exit_code = stdout.channel.recv_exit_status()

        client.close()

        # Format result
        result = f"=== Script Execution Results ===\n"
        result += f"Command: {command}\n"
        result += f"Exit Code: {exit_code}\n\n"

        if output:
            result += f"=== Standard Output ===\n{output}\n"

        if error:
            result += f"=== Standard Error ===\n{error}\n"

        if not output and not error:
            result += "No output received\n"

        return result

    except Exception as e:
        return f"Error executing script: {str(e)}"

@mcp.tool()
def upload_and_execute(
    local_file: str,
    remote_dir: Optional[str] = None,
    script_path: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    key_file: Optional[str] = None,
    script_args: Optional[str] = None
) -> str:
    """
    Upload a file and execute a remote script in one operation

    Args:
        local_file: Path to the local file to upload
        remote_dir: Remote directory (uses config.json default_remote_dir if not provided)
        script_path: Path to the script to execute (uses config.json default_script if not provided)
        host: SSH host (uses config.json if not provided)
        port: SSH port (uses config.json if not provided)
        username: SSH username (uses config.json if not provided)
        password: SSH password (optional, uses config.json if not provided)
        key_file: Path to SSH private key file (optional)
        script_args: Optional arguments to pass to the script

    Returns:
        Combined result of upload and script execution
    """
    # First, upload the file
    upload_result = upload_file(
        local_file=local_file,
        remote_dir=remote_dir,
        host=host,
        port=port,
        username=username,
        password=password,
        key_file=key_file
    )

    if "Error" in upload_result:
        return upload_result

    # Then execute the script
    exec_result = execute_remote_script(
        script_path=script_path,
        host=host,
        port=port,
        username=username,
        password=password,
        key_file=key_file,
        args=script_args
    )

    # Combine results
    return f"{upload_result}\n\n{exec_result}"

@mcp.tool()
def list_remote_directory(
    remote_dir: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    key_file: Optional[str] = None
) -> str:
    """
    List contents of a remote directory

    Args:
        remote_dir: Remote directory path to list
        host: SSH host (uses config.json if not provided)
        port: SSH port (uses config.json if not provided)
        username: SSH username (uses config.json if not provided)
        password: SSH password (optional, uses config.json if not provided)
        key_file: Path to SSH private key file (optional)

    Returns:
        Directory listing
    """
    try:
        # Load config for missing parameters
        config = load_config()
        host = host or config.get('host')
        port = port or config.get('port', 22)
        username = username or config.get('username')
        password = password or config.get('password')
        key_file = key_file or config.get('key_file')

        if not all([host, username, remote_dir]):
            return "Error: Missing required parameters (host, username, remote_dir)"

        # Connect via SSH
        client = get_ssh_client(host, port, username, password, key_file)
        stdin, stdout, stderr = client.exec_command(f"ls -lah {remote_dir}")

        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        client.close()

        if error:
            return f"Error: {error}"

        return f"Contents of {remote_dir} on {host}:\n\n{output}"

    except Exception as e:
        return f"Error listing directory: {str(e)}"

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
