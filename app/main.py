import argparse
import os
import sys
import json
from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")

TOOL_READ = {
    "type": "function",
    "function": {
        "name": "Read",
        "description": "Read a file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to read"
                }
            },
            "required": ["file_path"]
        }
    }
}

def call_llm(client, messages, tools):
    chat = client.chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        messages=messages,
        tools=tools,
    )
    return chat
   # Sample chat object output:
    # choices: [
    #   {
    #     "message": {
    #       "role": "assistant",
    #       "content": null,
    #       "tool_calls": [
    #         {
    #           "id": "tool_call_id_1",
    #           "function": {
    #             "name": "Read",
    #             "arguments": "{\"file_path\": \"/path/to/file.txt\"}"
    #           }
    #         }
    #       ]
    #     }
    #   }
    # ]
def available_tools():
    return [
        TOOL_READ
    ]

def call_tool(tool_call):
    if tool_call.function.name == "Read":
        file_path = json.loads(tool_call.function.arguments)["file_path"]
        with open(file_path, "r") as f:
            content = f.read()
            return content
    else:
        raise RuntimeError(f"Unknown tool: {tool_call.function.name}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    messages = [{"role": "user", "content": args.p}]
    tools = available_tools()
    while True:
        response = call_llm(client, messages, tools)

        if not response.choices or len(response.choices) == 0:
            raise RuntimeError("no choices in response")

        messages.append({
            "role": "assistant",
            "content": response.choices[0].message.content,
            "tool_calls": response.choices[0].message.tool_calls
        })

        if not response.choices[0].message.tool_calls:
            print(response.choices[0].message.content)
            exit(0)

        tool_calls = response.choices[0].message.tool_calls
        for tool_call in tool_calls:
            tool_result = call_tool(tool_call)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })


if __name__ == "__main__":
    main()
