#!/usr/bin/env python3
"""
TestCase Generator MCP Server
Auto-generate test cases for code files
"""

import os
import sys
import subprocess
import platform
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Windows console encoding fix
if platform.system() == "Windows":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 创建 FastMCP 实例
mcp = FastMCP("testcase-generator")


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.json"

    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config.json: {e}", file=sys.stderr)

    return {}


def get_script_command():
    """获取测试用例生成脚本的路径

    优先级：
    1. 环境变量 TESTCASE_SCRIPT_PATH
    2. config.json 中的 script_path
    3. 默认路径（当前目录下的脚本）
    """
    # 1. 检查环境变量
    env_script = os.environ.get('TESTCASE_SCRIPT_PATH')
    if env_script:
        script_path = Path(env_script)
        if script_path.exists():
            return str(script_path)
        else:
            print(f"Warning: TESTCASE_SCRIPT_PATH points to non-existent file: {env_script}", file=sys.stderr)

    # 2. 检查配置文件
    config = load_config()
    if 'script_path' in config:
        script_path = Path(config['script_path']).expanduser()
        if script_path.exists():
            return str(script_path)
        else:
            print(f"Warning: Configured script_path does not exist: {config['script_path']}", file=sys.stderr)

    # 3. 使用默认路径
    if platform.system() == "Windows":
        script_path = Path(__file__).parent / "gen_testcase.cmd"
    else:
        script_path = Path(__file__).parent / "gen_testcase.sh"

    return str(script_path)


@mcp.tool()
def generate_testcase(path: str) -> str:
    """
    为指定的文件或文件夹生成测试用例

    Args:
        path: 文件或文件夹的路径

    Returns:
        生成结果的描述信息
    """
    # 验证路径是否存在
    target_path = Path(path).resolve()
    if not target_path.exists():
        return f"错误：路径不存在: {path}"

    # 获取脚本命令
    script_cmd = get_script_command()

    if not Path(script_cmd).exists():
        return f"错误：测试用例生成脚本不存在: {script_cmd}"

    try:
        # 调用脚本生成测试用例
        # 始终使用 bash 执行（即使在 Windows 上，如果脚本是 .sh）
        script_ext = Path(script_cmd).suffix.lower()

        if script_ext == '.sh':
            # 使用 bash 执行 .sh 脚本（Linux 原生，Windows 通过 WSL 或 Git Bash）
            result = subprocess.run(
                ["bash", script_cmd, str(target_path)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
        elif script_ext == '.cmd' or script_ext == '.bat':
            # 使用 cmd 执行 .cmd/.bat 脚本（Windows）
            result = subprocess.run(
                [script_cmd, str(target_path)],
                capture_output=True,
                text=True,
                shell=True,
                encoding='utf-8',
                errors='ignore'
            )
        else:
            # 尝试直接执行（假设有执行权限）
            result = subprocess.run(
                [script_cmd, str(target_path)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else "Unknown error"
            return f"Generation failed:\n{error_msg}"

        output = result.stdout if result.stdout else "No output"
        return f"Test cases generated successfully!\n\n{output}"

    except Exception as e:
        return f"Error executing script: {str(e)}"


@mcp.tool()
def list_generated_testcases(directory: str = ".") -> str:
    """
    列出指定目录下所有生成的测试用例文件

    Args:
        directory: 要搜索的目录路径，默认为当前目录

    Returns:
        测试用例文件列表
    """
    dir_path = Path(directory).resolve()

    if not dir_path.exists():
        return f"错误：目录不存在: {directory}"

    if not dir_path.is_dir():
        return f"错误：{directory} 不是一个目录"

    # 查找所有 *-test.* 文件
    test_files = []
    for file in dir_path.rglob("*-test.*"):
        if file.is_file():
            test_files.append(str(file.relative_to(dir_path)))

    if not test_files:
        return f"在 {directory} 目录下未找到测试用例文件"

    return "找到以下测试用例文件:\n" + "\n".join(f"  - {f}" for f in sorted(test_files))


@mcp.resource("info://testcase-generator")
def get_server_info() -> str:
    """获取服务器信息"""
    return f"""TestCase Generator MCP Server

当前操作系统: {platform.system()}
使用的脚本: {get_script_command()}
工作目录: {os.getcwd()}

可用工具:
- generate_testcase: 为文件或文件夹生成测试用例
- list_generated_testcases: 列出已生成的测试用例文件
"""


def test_mode(target_path=None):
    """Test mode: Verify functionality

    Args:
        target_path: Optional path to test (file or directory)
    """
    print("=== TestCase Generator MCP Server - Test Mode ===\n")

    # 1. Check if script exists
    script_cmd = get_script_command()
    print(f"1. Checking script: {script_cmd}")
    if Path(script_cmd).exists():
        print("   [OK] Script exists\n")
    else:
        print(f"   [FAIL] Script not found\n")
        return

    # If user provided a path, use it directly
    if target_path:
        target = Path(target_path).resolve()

        if not target.exists():
            print(f"   [FAIL] Path does not exist: {target_path}\n")
            return

        print(f"2. Using provided path: {target}")

        if target.is_file():
            print("   [INFO] Target is a file\n")
            print(f"3. Generating test case for file: {target}")
            result = generate_testcase(str(target))
            print(f"   Result: {result}\n")

            # List test cases in the same directory
            print(f"4. Listing test cases in: {target.parent}")
            result = list_generated_testcases(str(target.parent))
            print(f"   {result}\n")
        else:
            print("   [INFO] Target is a directory\n")
            print(f"3. Generating test cases for directory: {target}")
            result = generate_testcase(str(target))
            print(f"   Result: {result}\n")

            # List generated test cases
            print(f"4. Listing test cases in: {target}")
            result = list_generated_testcases(str(target))
            print(f"   {result}\n")

        print("=== Test completed ===")
        return

    # Original demo mode - create test files
    print("2. Running demo mode (no path provided)\n")

    test_dir = Path("test_demo")
    test_dir.mkdir(exist_ok=True)

    test_file = test_dir / "example.py"
    test_file.write_text("""def hello():
    print("Hello, World!")

def add(a, b):
    return a + b
""")
    print(f"3. Created test file: {test_file}")
    print("   [OK] File created successfully\n")

    # Test single file generation
    print(f"4. Testing single file generation: {test_file}")
    result = generate_testcase(str(test_file))
    print(f"   Result: {result}\n")

    # Create multiple test files
    test_file2 = test_dir / "utils.js"
    test_file2.write_text("""function multiply(a, b) {
    return a * b;
}
""")
    print(f"5. Created second test file: {test_file2}")
    print("   [OK] File created successfully\n")

    # Test directory generation
    print(f"6. Testing directory generation: {test_dir}")
    result = generate_testcase(str(test_dir))
    print(f"   Result: {result}\n")

    # List generated test cases
    print(f"7. Listing generated test cases:")
    result = list_generated_testcases(str(test_dir))
    print(f"   {result}\n")

    print("=== Test completed ===")


if __name__ == "__main__":
    # 检查是否为测试模式
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # 检查是否提供了路径参数
        test_path = sys.argv[2] if len(sys.argv) > 2 else None
        test_mode(test_path)
    elif len(sys.argv) > 1 and sys.argv[1] == "--check-env":
        # 环境检查模式
        print("=== Environment Check ===\n")
        print(f"Operating System: {platform.system()}")
        print(f"Platform: {platform.platform()}")
        print(f"Python Version: {platform.python_version()}")
        print(f"Working Directory: {os.getcwd()}\n")

        # 配置信息
        print("Configuration:")
        env_script = os.environ.get('TESTCASE_SCRIPT_PATH')
        print(f"  TESTCASE_SCRIPT_PATH env: {env_script if env_script else '(not set)'}")

        config = load_config()
        config_script = config.get('script_path')
        print(f"  config.json script_path: {config_script if config_script else '(not set)'}\n")

        # 实际使用的脚本
        script_cmd = get_script_command()
        print(f"Script to use: {script_cmd}")
        script_path = Path(script_cmd)
        print(f"Script exists: {script_path.exists()}")
        if script_path.exists():
            print(f"Script resolved path: {script_path.resolve()}")
            print(f"Script extension: {script_path.suffix}")

        print("\n=== Check completed ===")
    else:
        # 正常运行 MCP server
        mcp.run()
