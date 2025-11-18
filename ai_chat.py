#!/usr/bin/env python3
"""
DeepSeek 命令行对话程序
支持连续对话和流式输出
"""

import json
import sys
import urllib.request
import urllib.error

# DeepSeek API配置
API_KEY = ""  # 请替换为你的API密钥
API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"


def stream_chat(messages):
    """发送请求并流式接收响应"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    data = {
        "model": MODEL,
        "messages": messages,
        "stream": True
    }
    
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(data).encode('utf-8'),
        headers=headers
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            for line in response:
                line = line.decode('utf-8').strip()
                if not line or line == "data: [DONE]":
                    continue
                    
                if line.startswith("data: "):
                    try:
                        json_data = json.loads(line[6:])
                        delta = json_data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            print(content, end='', flush=True)
                            yield content
                    except json.JSONDecodeError:
                        continue
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"\n错误: {e.code} - {error_msg}", file=sys.stderr)
        return
    except Exception as e:
        print(f"\n错误: {str(e)}", file=sys.stderr)
        return


def main():
    """主程序"""
    print("=" * 50)
    print("DeepSeek 对话程序")
    print("=" * 50)
    print("输入 'exit' 或 'quit' 退出程序")
    print("输入 'clear' 清空对话历史")
    print("=" * 50)
    print()
    
    # 对话历史
    messages = []
    
    while True:
        try:
            # 获取用户输入
            user_input = input("我: ").strip()
            
            if not user_input:
                continue
            
            # 处理特殊命令
            if user_input.lower() in ['exit', 'quit']:
                print("\n再见!")
                break
            
            if user_input.lower() == 'clear':
                messages = []
                print("对话历史已清空\n")
                continue
            
            # 添加用户消息
            messages.append({"role": "user", "content": user_input})
            
            # 显示AI回复
            print("AI: ", end='', flush=True)
            
            # 收集AI回复
            assistant_reply = ""
            for chunk in stream_chat(messages):
                assistant_reply += chunk
            
            print()  # 换行
            
            # 添加AI回复到历史
            if assistant_reply:
                messages.append({"role": "assistant", "content": assistant_reply})
            
            print()  # 空行分隔
            
        except KeyboardInterrupt:
            print("\n\n程序已中断")
            break
        except Exception as e:
            print(f"\n发生错误: {str(e)}", file=sys.stderr)
            continue


if __name__ == "__main__":
    if API_KEY == "your-api-key-here":
        print("错误: 请先在代码中设置你的 DeepSeek API 密钥")
        print("修改 API_KEY = 'your-api-key-here' 为你的实际密钥")
        sys.exit(1)
    
    main()
