import os
import sys
import subprocess
from datetime import datetime

from dotenv import load_dotenv, find_dotenv
from openai import OpenAI


STUDENT_NAME = "Manav"
STUDENT_ID = "174134239"


def print_header():
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"git-cm: Developed by {STUDENT_NAME} - {STUDENT_ID}")
    print(f"Run Date: {run_date}")
    print("--------------------------------------------------------------")


def load_api_key():
    load_dotenv(find_dotenv())

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("Error: OPENROUTER_API_KEY not found")
        sys.exit(1)

    return api_key


def get_staged_diff():
    try:
        result = subprocess.run(
            ["git", "diff", "--staged"],
            capture_output=True,
            text=True,
            check=True
        )

        diff = result.stdout.strip()

        if not diff:
            print("No staged changes found")
            sys.exit(1)

        print(f"Diff found: {len(diff)} characters")
        return diff

    except subprocess.CalledProcessError:
        print("Not a git repo")
        sys.exit(1)


def generate_commit_message(api_key, diff, is_creative):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    if is_creative:
        system_prompt = (
            "You are an LLM running in a CLI tool that writes creative git commit messages. "
            "You will be given a git diff. Output ONLY one commit message. "
            "Use Gitmoji and write the commit message using 17th Century pirate slang. "
            "Do not use Markdown. Do not explain your answer. Do not include quotation marks."
        )
        temperature = 1.2
    else:
        system_prompt = (
            "You are an LLM running in a CLI tool that writes semantic git commit messages. "
            "You will be given a git diff. Output ONLY one commit message using the "
            "Conventional Commits format, such as 'feat: add git diff support' or "
            "'fix(api): handle missing token'. Do not use Markdown. Do not explain your answer. "
            "Do not include quotation marks."
        )
        temperature = 0.1

    try:
        response = client.chat.completions.create(
            model="google/gemma-4-31b-it:free",
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": diff}
            ]
        )

        commit_message = response.choices[0].message.content.strip()

        print()
        print("Generated Commit Message:")
        print(commit_message)

    except Exception as error:
        print("Error while calling OpenRouter API")
        print(error)
        sys.exit(1)


def main():
    print_header()

    is_creative = "--creative" in sys.argv

    api_key = load_api_key()
    diff = get_staged_diff()
    generate_commit_message(api_key, diff, is_creative)


if __name__ == "__main__":
    main()