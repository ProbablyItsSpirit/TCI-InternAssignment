import os
import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

def generate_response(prompt):

    completion = client.chat.completions.create(
        model="meta/llama-3.3-70b-instruct",
        messages=[
            {
                "role": "system",
                "content": "You are a professional finance collections assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=400
    )

    content = completion.choices[0].message.content

    try:
        return json.loads(content)

    except Exception:
        return {
            "subject": "Parsing Error",
            "body": content,
            "tone": "Unknown",
            "stage": "Unknown"
        }