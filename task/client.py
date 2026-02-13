import json
import sys
from typing import Any

import requests

from task.models.message import Message
from task.models.role import Role
from task.tools.base import BaseTool


class DialClient:

    def __init__(
            self,
            endpoint: str,
            deployment_name: str,
            api_key: str,
            tools: list[BaseTool] | None = None
    ):
        if not api_key:
            raise ValueError("API key is required")
        self.__endpoint = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions"
        self.__api_key = api_key
        self.__tools_dict: dict[str, BaseTool] = {tool.name: tool for tool in (tools or [])}
        self.__tools_schemas = [tool.schema for tool in (tools or [])]
        print(f"Endpoint: {self.__endpoint}")
        print(f"Tools: {[s['function']['name'] for s in self.__tools_schemas]}")


    def get_completion(self, messages: list[Message], print_request: bool = True) -> Message:
        headers = {
            "api-key": self.__api_key,
            "Content-Type": "application/json"
        }
        request_data = {
            "messages": [msg.to_dict() for msg in messages],
            "tools": self.__tools_schemas,
            "stream": True
        }
        if print_request:
            print(f"\n{'='*50}\nRequest messages: {[msg.to_dict() for msg in messages]}\n{'='*50}")
        response = requests.post(url=self.__endpoint, headers=headers, json=request_data, stream=True)
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} {response.text}")

        content = ""
        tool_calls: list[dict[str, Any]] = []
        finish_reason = None

        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data = line[len("data: "):]
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            choice = chunk["choices"][0]
            if choice.get("finish_reason"):
                finish_reason = choice["finish_reason"]
            delta = choice.get("delta", {})

            # Accumulate content and print in real-time
            if delta.get("content"):
                content += delta["content"]
                sys.stdout.write(delta["content"])
                sys.stdout.flush()

            # Accumulate tool calls
            if delta.get("tool_calls"):
                for tc_delta in delta["tool_calls"]:
                    idx = tc_delta["index"]
                    # Extend the list if needed
                    while len(tool_calls) <= idx:
                        tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                    if tc_delta.get("id"):
                        tool_calls[idx]["id"] = tc_delta["id"]
                    if tc_delta.get("function", {}).get("name"):
                        tool_calls[idx]["function"]["name"] = tc_delta["function"]["name"]
                    if tc_delta.get("function", {}).get("arguments"):
                        tool_calls[idx]["function"]["arguments"] += tc_delta["function"]["arguments"]

        ai_response = Message(
            role=Role.AI,
            content=content or None,
            tool_calls=tool_calls or None
        )

        if finish_reason == "tool_calls":
            messages.append(ai_response)
            tool_messages = self._process_tool_calls(tool_calls)
            messages.extend(tool_messages)
            return self.get_completion(messages, print_request)

        return ai_response


    def _process_tool_calls(self, tool_calls: list[dict[str, Any]]) -> list[Message]:
        """Process tool calls and add results to messages."""
        tool_messages = []
        for tool_call in tool_calls:
            tool_call_id = tool_call["id"]
            function = tool_call["function"]
            function_name = function["name"]
            arguments = json.loads(function["arguments"])
            tool_execution_result = self._call_tool(function_name, arguments)
            tool_messages.append(Message(
                role=Role.TOOL,
                name=function_name,
                tool_call_id=tool_call_id,
                content=tool_execution_result
            ))
            print(f"FUNCTION '{function_name}'\n{tool_execution_result}\n{'-'*50}")

        return tool_messages

    def _call_tool(self, function_name: str, arguments: dict[str, Any]) -> str:
        tool = self.__tools_dict.get(function_name)
        if tool:
            return tool.execute(arguments)
        return f"Unknown function: {function_name}"
