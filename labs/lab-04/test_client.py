import json
import time

import requests


notes_path = "notes.md"


def test_server():
    try:
        print(f"Reading notes from: {notes_path}")

        with open(notes_path, "r", encoding="utf-8") as file:
            notes_content = file.read()

        payload = {
            "notes": notes_content,
            "cards": 2,
        }

        print("Sending request to server...")
        start_time = time.time()

        response = requests.post(
            "http://localhost:3000/api/generate",
            json=payload,
            timeout=120,
        )

        end_time = time.time()
        print(f"Request took {end_time - start_time:.2f}s")

        if response.status_code != 200:
            print(f"Server error {response.status_code}: {response.text}")
            return

        data = response.json()

        print()
        print("Success! Received Structured Data:")
        print(json.dumps(data, indent=2))

    except FileNotFoundError:
        print(f"Error: Could not find file at {notes_path}")
    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    test_server()