import argparse
import json
import os
import sys
from typing import Any, Dict, List

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from image_utils import format_bytes, process_image
from prompts import SYSTEM_PROMPT
from web_search import lookup_error


VISION_MODEL = "google/gemini-3-flash-preview"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_error",
            "description": "Searches the web for technical documentation, coding errors, framework changes, and debugging information based on the screenshot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to use based on the screenshot error.",
                    }
                },
                "required": ["query"],
            },
        },
    }
]


def load_openrouter_client() -> OpenAI:
    load_dotenv(find_dotenv())

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not found in .env file.")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def run_tool_call(tool_call: Any) -> Dict[str, Any]:
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments or "{}")

    if name == "lookup_error":
        query = args.get("query", "")
        print(f"[tool] lookup_error query: {query}", file=sys.stderr)
        return lookup_error(query)

    return {"error": f"Unknown tool: {name}"}


def analyze_image(image_path: str, user_prompt: str) -> str:
    image_data = process_image(image_path)

    print("[image] Optimization stats:", file=sys.stderr)
    print(
        f"[image] Original size: {format_bytes(image_data['original_size'])}",
        file=sys.stderr,
    )
    print(
        f"[image] Processed JPEG size: {format_bytes(image_data['processed_size'])}",
        file=sys.stderr,
    )
    print(
        f"[image] Base64 string length: {image_data['base64_size']} characters",
        file=sys.stderr,
    )
    print(
        f"[image] Original dimensions: {image_data['original_dimensions']}",
        file=sys.stderr,
    )
    print(
        f"[image] Processed dimensions: {image_data['processed_dimensions']}",
        file=sys.stderr,
    )

    client = load_openrouter_client()

    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data['base64']}"
                    },
                },
            ],
        },
    ]

    print("[model] Sending screenshot to vision model...", file=sys.stderr)

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    assistant_message = response.choices[0].message
    messages.append(assistant_message.model_dump())

    if assistant_message.tool_calls:
        print(
            f"[model] Tool calls requested: {len(assistant_message.tool_calls)}",
            file=sys.stderr,
        )

        for tool_call in assistant_message.tool_calls:
            tool_result = run_tool_call(tool_call)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": json.dumps(tool_result, indent=2),
                }
            )

        print("[model] Sending tool results back to model...", file=sys.stderr)

        final_response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="none",
        )

        return final_response.choices[0].message.content or ""

    return assistant_message.content or ""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="img-debug: Analyze developer screenshots using a vision LLM and Tavily web search."
    )

    parser.add_argument(
        "image",
        help="Path to screenshot image.",
    )

    parser.add_argument(
        "-p",
        "--prompt",
        default="Analyze this developer error screenshot and tell me how to fix it. Use web search if current documentation is needed.",
        help="Optional prompt to send with the screenshot.",
    )

    args = parser.parse_args()

    try:
        answer = analyze_image(args.image, args.prompt)
        print()
        print(answer)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()