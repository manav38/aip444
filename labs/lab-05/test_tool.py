from tools import read_github_files


def test_single_file() -> None:
    print("TEST 1: Existing GitHub file\n")

    result = read_github_files(
        [
            {
                "owner": "microsoft",
                "repo": "vscode",
                "path": "package.json",
                "ref": "main",
            }
        ]
    )

    print(result)

def test_large_file() -> None:
    print("\n\nTEST 4: Large file truncation\n")

    result = read_github_files(
        [
            {
                "owner": "microsoft",
                "repo": "vscode",
                "path": "src/vs/editor/browser/widget/codeEditor/codeEditorWidget.ts",
                "ref": "main",
            }
        ]
    )

    print(result)

def test_missing_file() -> None:
    print("\n\nTEST 2: Missing GitHub file\n")

    result = read_github_files(
        [
            {
                "owner": "microsoft",
                "repo": "vscode",
                "path": "this-file-does-not-exist.txt",
                "ref": "main",
            }
        ]
    )

    print(result)


def test_multiple_files() -> None:
    print("\n\nTEST 3: Multiple GitHub files\n")

    result = read_github_files(
        [
            {
                "owner": "microsoft",
                "repo": "vscode",
                "path": "README.md",
                "ref": "main",
            },
            {
                "owner": "microsoft",
                "repo": "vscode",
                "path": "package.json",
                "ref": "main",
            },
        ]
    )

    print(result)


if __name__ == "__main__":
    test_single_file()
    test_missing_file()
    test_multiple_files()
    test_large_file()