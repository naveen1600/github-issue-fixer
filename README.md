# GitHub Issue Fixer

An AI agent that automatically fixes GitHub issues using Google Gemini. Point it at a GitHub issue and it will clone the repo, analyze the problem, write the fix, and open a pull request.

## How It Works

1. Fetches the issue details from GitHub
2. Detects push access — clones directly or forks if needed
3. Creates an isolated workspace and a fix branch
4. Runs an agentic loop powered by Gemini to read and edit files
5. Commits and pushes the fix
6. Opens a pull request after human review

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
GITHUB_TOKEN=your_github_fine_grained_pat
TRIGGER_LABEL=ai-fix                   # optional, default: ai-fix
BASE_BRANCH=main                        # optional, default: main
REQUIRED_REVIEWERS=["username1"]        # optional, JSON array
MAX_ITERATIONS=30                       # optional
MAX_DURATION_SECONDS=600                # optional
TOKEN_BUDGET=200000                     # optional
```

The GitHub token needs **repo** read/write access (and **fork** access if you plan to fix repos you don't own).

### 3. (Optional) Set up branch protection

Require human approval before any agent PR can be merged:

```bash
python scripts/setup_protection.py --repo owner/repo
python scripts/setup_protection.py --repo owner/repo --branch main
```

## Usage

Provide a GitHub issue URL. The agent runs, shows you a summary, and asks for confirmation before opening the PR.

```bash
python cli.py https://github.com/owner/repo/issues/42
```

Dry run (no push, no PR):

```bash
python cli.py https://github.com/owner/repo/issues/42 --dry-run
```

## Project Structure

```
github-issue-fixer/
├── agent/
│   ├── loop.py          # Agentic loop (Gemini tool-use)
│   ├── orchestrator.py  # Pipeline: fetch → clone → fix → commit → PR
│   └── prompts.py       # System prompt and initial message builder
├── git_ops/
│   ├── brancher.py      # Branch creation
│   ├── cloner.py        # Repo cloning
│   └── committer.py     # Commit and push
├── github_api/
│   ├── client.py        # Authenticated GitHub client
│   ├── fork_manager.py  # Fork detection and creation
│   ├── issue_reader.py  # Issue fetching
│   └── pr_creator.py    # Pull request creation
├── tools/
│   ├── executor.py      # Tool call dispatcher
│   ├── filesystem.py    # File read/write/list tools
│   ├── github_tools.py  # GitHub-specific tools
│   ├── registry.py      # Gemini tool registry
│   └── shell.py         # Shell execution tool
├── utils/
│   ├── logger.py        # Structured JSON logger
│   └── workspace.py     # Temporary workspace management
├── scripts/
│   └── setup_protection.py  # Branch protection setup
├── cli.py               # CLI entry point
└── config.py            # Settings (via pydantic-settings)
```

## Agent Limits

The agent is bounded by three configurable limits to prevent runaway execution:

| Limit | Default | Config key |
|---|---|---|
| Max iterations | 30 | `MAX_ITERATIONS` |
| Max duration | 600s | `MAX_DURATION_SECONDS` |
| Token budget | 200,000 | `TOKEN_BUDGET` |

## Requirements

- Python 3.11+
- Google Gemini API key
- GitHub Fine-Grained Personal Access Token
