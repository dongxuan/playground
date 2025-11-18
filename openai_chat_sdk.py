#!/usr/bin/env python3
"""
OpenAI 命令行对话程序 (使用官方SDK) - 修复版
支持连续对话和流式输出
"""

import sys

try:
    from openai import OpenAI
except ImportError:
    print("错误: 请先安装 OpenAI SDK")
    print("运行: pip install openai")
    sys.exit(1)

# OpenAI API配置
API_KEY = "your-api-key-here"  # 请替换为你的API密钥
MODEL = "gpt-4o-mini"  # 可选: gpt-4o, gpt-4o-mini, gpt-3.5-turbo 等


def stream_chat(client, messages):
    """发送请求并流式接收响应"""
    try:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            stream=True
        )
        
        assistant_reply = ""
        for chunk in stream:
            # 检查 delta 是否存在以及是否有 content
            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end='', flush=True)
                assistant_reply += content
        
        return assistant_reply
                
    except Exception as e:
        print(f"\n错误: {str(e)}", file=sys.stderr)
        return ""


def main():
    """主程序"""
    print("=" * 50)
    print(f"OpenAI 对话程序 (模型: {MODEL})")
    print("=" * 50)
    print("输入 'exit' 或 'quit' 退出程序")
    print("输入 'clear' 清空对话历史")
    print("=" * 50)
    print()
    
    # 初始化客户端
    client = OpenAI(api_key=API_KEY)
    
    # 对话历史
    messages = []
    
    while True:
        try:
            # 获取用户输入
            user_input = input("你: ").strip()
            
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
            
            # 获取AI回复
            assistant_reply = stream_chat(client, messages)
            
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
        print("错误: 请先在代码中设置你的 OpenAI API 密钥")
        print("修改 API_KEY = 'your-api-key-here' 为你的实际密钥")
        sys.exit(1)
    
    main()
