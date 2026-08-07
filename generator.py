import os
import json
import time
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

INPUT_FILE = "chunks.jsonl"
OUTPUT_FILE = "dataset.jsonl"
MODEL = "gemini-2.5-flash"

def generate_example(chunk):
    prompt = f"""
You are creating a high-quality supervised fine-tuning dataset.

Read the passage and create one useful instruction/question and its answer.

Requirements:
- The question must be answerable from the passage.
- The question should require understanding rather than copying a sentence.
- The answer must use only information supported by the passage.
- Do not introduce outside facts.
- Do not mention the passage.
- Avoid trivial questions such as "What is this passage about?"

Return valid JSON with exactly these fields:
{{
  "question": "...",
  "answer": "...",
  "type": "factual|explanation|why|how|application|summary"
}}

PASSAGE:
{chunk}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )

    return json.loads(response.text)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    chunks = [json.loads(line) for line in f]

with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for i, item in enumerate(chunks):
        try:
            result = generate_example(item["text"])

            example = {
                "source_id": item["id"],
                "type": result["type"],
                "messages": [
                    {
                        "role": "user",
                        "content": result["question"]
                    },
                    {
                        "role": "assistant",
                        "content": result["answer"]
                    }
                ]
            }

            out.write(json.dumps(example, ensure_ascii=False) + "\n")
            out.flush()

            print(f"{i + 1}/{len(chunks)}")

            time.sleep(1)

        except Exception as e:
            print(f"Failed on {item.get('id')}: {e}")