TASKS = {"qa": "Generate a question-answer pair grounded in the context.", "instruction": "Generate an instruction-following example grounded in the context.", "summary": "Generate a concise summary task for the context.", "chat": "Generate a 3-turn conversation discussing the context.", "extract": "Extract key entities or facts from the context."}
DIFF = {"easy": "Simple, direct, single-hop, basic vocab, short answer.", "medium": "Moderate complexity, multi-step inference, some technical terms.", "hard": "Complex, synthesis, comparison, edge cases, longer analytical answer."}

def build(task, diff, ctx):
    return f"""Context: \"\"\"{ctx}\"\"\"
Task: {TASKS[task]}
Difficulty: {DIFF[diff]}
Output STRICT JSON only: {{\"instruction\": \"...\", \"input\": \"...\", \"output\": \"...\"}}
Rules: stay grounded, no external info, no markdown, no repetition.
JSON:"""

def build_chat(diff, ctx):
    return f"""Context: \"\"\"{ctx}\"\"\"
Generate a 3-turn conversation (user/assistant) about this context.
Difficulty: {DIFF[diff]}
STRICT JSON only: {{\"turns\": [{{\"role\":\"user\",\"content\":\"...\"}}, {{\"role\":\"assistant\",\"content\":\"...\"}}, {{\"role\":\"user\",\"content\":\"...\"}}, {{\"role\":\"assistant\",\"content\":\"...\"}}]}}
JSON:"""
