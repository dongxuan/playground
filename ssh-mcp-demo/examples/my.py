#!/usr/bin/env python3
"""
Example Python script to upload to remote server
"""

def main():
    print("Hello from remote server!")
    print("This is a test script.")

    # Simple calculation
    result = sum(range(1, 11))
    print(f"Sum of 1 to 10: {result}")

    # File operations example
    with open('/tmp/test_output.txt', 'w') as f:
        f.write("Script executed successfully!\n")

    print("Output written to /tmp/test_output.txt")

if __name__ == "__main__":
    main()
