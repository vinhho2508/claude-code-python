from app import tools
from app.llm import LLM
from app.skills.registry import format_skills_prompt, expand_skill_command


def run_agent(llm: LLM, prompt: str, max_turns: int=50) -> str:
    messages: list[dict] = []
    skills_prompt = format_skills_prompt()
    if skills_prompt:
        messages.append({"role": "system", "content": skills_prompt})

    
    messages.append({"role": "user", "content": expand_skill_command(prompt)})

    for _ in range(max_turns):
        response = llm.chat(messages, tools.schemas())

        if not response.choices:
            raise RuntimeError("no choices in response")
        
        message = response.choices[0].message
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": message.tool_calls
        })

        if not message.tool_calls:
            return message.content or ""
        
        for call in message.tool_calls:
            result = tools.run_tool(call.function.name, call.function.arguments)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result })
    raise RuntimeError(f"agent did not finish within {max_turns} turns")
