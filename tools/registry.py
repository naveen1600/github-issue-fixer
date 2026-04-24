from __future__ import annotations

from google.genai import types

GEMINI_TOOLS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="read_file",
            description=(
                "Read the contents of a file in the repository. "
                "Use this to understand existing code before modifying it. "
                "Optionally specify start_line and end_line (1-indexed, inclusive) to read a range."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "path": types.Schema(type=types.Type.STRING, description="Path relative to repository root, e.g. 'src/utils/helper.py'"),
                    "start_line": types.Schema(type=types.Type.INTEGER, description="First line to read (1-indexed). Omit for full file."),
                    "end_line": types.Schema(type=types.Type.INTEGER, description="Last line to read (inclusive). Omit for full file."),
                },
                required=["path"],
            ),
        ),
        types.FunctionDeclaration(
            name="write_file",
            description=(
                "Write or overwrite a file in the repository with new content. "
                "This is how you apply fixes. Always read the file first. "
                "Creates the file and any missing parent directories."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "path": types.Schema(type=types.Type.STRING, description="Path relative to repository root"),
                    "content": types.Schema(type=types.Type.STRING, description="Complete new content for the file"),
                },
                required=["path", "content"],
            ),
        ),
        types.FunctionDeclaration(
            name="list_directory",
            description=(
                "List files and subdirectories at a given path. "
                "Use to explore the repository structure before reading files."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "path": types.Schema(type=types.Type.STRING, description="Path relative to repository root. Use '.' for root."),
                    "recursive": types.Schema(type=types.Type.BOOLEAN, description="If true, list all nested files. Default false."),
                },
                required=["path"],
            ),
        ),
        types.FunctionDeclaration(
            name="search_code",
            description=(
                "Search for a regex pattern across all files in the repository. "
                "Returns file paths and matching lines with line numbers. "
                "Use to find where a symbol, function, or string is defined or used."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "pattern": types.Schema(type=types.Type.STRING, description="Regex pattern, e.g. 'def process_payment'"),
                    "file_glob": types.Schema(type=types.Type.STRING, description="Optional glob to restrict search, e.g. '*.py'"),
                    "case_sensitive": types.Schema(type=types.Type.BOOLEAN, description="Default true. Set false for case-insensitive search."),
                },
                required=["pattern"],
            ),
        ),
        types.FunctionDeclaration(
            name="run_tests",
            description=(
                "Run the project's test suite and return stdout/stderr. "
                "Use after making changes to verify nothing is broken. Timeout: 120 seconds."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "test_path": types.Schema(type=types.Type.STRING, description="Optional specific test file or directory"),
                    "extra_args": types.Schema(type=types.Type.STRING, description="Optional extra CLI args, e.g. '-k test_refund -v'"),
                },
                required=[],
            ),
        ),
        types.FunctionDeclaration(
            name="get_issue_comments",
            description="Fetch all comments on the GitHub issue being fixed.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
                required=[],
            ),
        ),
    ]
)
