import os
import json
import re

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)


def extract_json(text):

    def escape_control_chars_inside_strings(json_text):

        escaped_chars = []
        in_string = False
        is_escaped = False

        for char in json_text:

            if in_string:

                if is_escaped:
                    escaped_chars.append(char)
                    is_escaped = False
                    continue

                if char == "\\":
                    escaped_chars.append(char)
                    is_escaped = True
                    continue

                if char == '"':
                    escaped_chars.append(char)
                    in_string = False
                    continue

                if char == "\n":
                    escaped_chars.append("\\n")
                    continue

                if char == "\r":
                    escaped_chars.append("\\r")
                    continue

                if char == "\t":
                    escaped_chars.append("\\t")
                    continue

                if ord(char) < 32:
                    escaped_chars.append(f"\\u{ord(char):04x}")
                    continue

                escaped_chars.append(char)
                continue

            if char == '"':
                in_string = True

            escaped_chars.append(char)

        return "".join(escaped_chars)

    try:

        cleaned_text = text.strip()

        if cleaned_text.startswith("```"):
            cleaned_text = re.sub(
                r"^```(?:json)?\s*",
                "",
                cleaned_text,
                flags=re.IGNORECASE
            )
            cleaned_text = re.sub(r"\s*```$", "", cleaned_text)

        match = re.search(
            r"\{.*\}",
            cleaned_text,
            re.DOTALL
        )

        if match:

            json_text = match.group(0)

            json_text = escape_control_chars_inside_strings(json_text)

            return json.loads(json_text)

    except Exception as e:

        print("JSON Extraction Error:", e)

    return {
        "subject": "Parsing Error",
        "body": text,
        "tone": "Unknown",
        "stage": "Unknown"
    }

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

    return extract_json(
        completion.choices[0].message.content
    )