#!/bin/bash
# Example script to execute on remote server

echo "================================"
echo "Starting script execution..."
echo "================================"
echo ""

# Show current directory
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -lh

echo ""
echo "================================"

# Check if my.py exists
if [ -f "my.py" ]; then
    echo "Found my.py, executing..."
    python3 my.py
    echo ""
    echo "================================"
    echo "Script execution completed!"
else
    echo "Error: my.py not found in current directory"
    exit 1
fi

# Show system info
echo ""
echo "System Information:"
echo "  Hostname: $(hostname)"
echo "  Date: $(date)"
echo "  User: $(whoami)"
echo ""
echo "================================"
