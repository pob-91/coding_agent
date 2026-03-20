from typing import Any

from model.channel_message import ChannelMessage


def convert_channel_messages(
    messages: list[ChannelMessage],
    flatten_tools: bool = False,
) -> list[Any]:
    historic_messages: list[Any] = []
    for msg in messages:
        if msg.role == "user":
            historic_messages.append({"role": "user", "content": msg.body})
        elif msg.role == "assistant":
            historic_messages.append({"role": "assistant", "content": msg.body})
        elif msg.role == "tool_call":
            if flatten_tools:
                historic_messages.append(
                    {
                        "role": "assistant",
                        "content": f"[Tool call: {msg.tool_name}] {msg.body}",
                    }
                )
            else:
                historic_messages.append(
                    {
                        "type": "function_call",
                        "call_id": msg.call_id,
                        "name": msg.tool_name,
                        "arguments": msg.body,
                    }
                )
        elif msg.role == "tool_output":
            if flatten_tools:
                historic_messages.append(
                    {
                        "role": "assistant",
                        "content": f"[Tool output] {msg.body}",
                    }
                )
            else:
                historic_messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": msg.call_id,
                        "output": msg.body,
                    }
                )

    return historic_messages
