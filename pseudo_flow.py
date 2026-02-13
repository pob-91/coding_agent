messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": issue_description},
]


"""
You must either:
- Call a tool
OR
- Return FINAL_PATCH
"""

while True:
    response = model.chat(messages=messages, tools=tool_definitions)

    if response.tool_call:
        tool_name = response.tool_call.name
        args = response.tool_call.arguments

        validate(tool_name, args)

        result = execute_tool(tool_name, args)

        messages.append({"role": "tool", "name": tool_name, "content": result})

    else:
        final_answer = response.content
        break
