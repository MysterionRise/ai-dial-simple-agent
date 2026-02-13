# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An educational Python project for building an AI-powered agent that integrates with EPAM's DIAL API (OpenAI-compatible) and a mock User Service. The agent uses LLM tool calling to perform CRUD operations on users and web searches.

## Setup & Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker-compose up -d          # starts mock user service on port 8041
DIAL_API_KEY=<key> python -m task.app
```

Requires EPAM VPN for DIAL API access (`https://ai-proxy.lab.epam.com`).

No test suite, linter, or build system is configured.

## Architecture

**Agentic tool-calling loop**: `app.py` runs an interactive REPL that sends conversation history to the DIAL API via `DialClient`. When the LLM responds with `finish_reason: "tool_calls"`, the client executes the requested tools, appends results as `Role.TOOL` messages, and recursively calls the API until `finish_reason: "stop"`.

### Key Components

- **`task/client.py` — `DialClient`**: Manages DIAL API requests, tool dispatch, and the recursive tool-call loop. Holds a `dict[name, BaseTool]` for dispatch and a `list[schema]` for the API request body.
- **`task/models/`**: `Message` (dataclass with `to_dict()` for API serialization), `Conversation` (append-only message list), `Role` (StrEnum: system/user/assistant/tool).
- **`task/tools/base.py` — `BaseTool`**: Abstract interface requiring `name`, `description`, `input_schema`, and `execute(arguments) -> str`. The `schema` property auto-generates the OpenAI-format function tool definition.
- **`task/tools/users/base.py` — `BaseUserServiceTool`**: Extends `BaseTool` with injected `UserClient` dependency.
- **`task/tools/users/user_client.py` — `UserClient`**: REST client for the mock user service (port 8041). Returns pre-formatted strings for LLM consumption.
- **`task/tools/users/models/user_info.py`**: Pydantic models (`UserCreate`, `UserUpdate`, `Address`, `CreditCard`) used for validation in create/update tools.
- **`task/tools/web_search.py` — `WebSearchTool`**: Uses `gemini-2.5-pro` deployment with `google_search` static function tool.
- **`task/prompts.py`**: Holds `SYSTEM_PROMPT` constant.

### Implementation Status

Files marked complete: `role.py`, `message.py`, `conversation.py`, `user_info.py`, `base.py` (both), `user_client.py`.

Files with TODO stubs: `client.py`, `app.py`, `prompts.py`, `web_search.py`, and all five user tool files (`create_user_tool.py`, `update_user_tool.py`, `delete_user_tool.py`, `get_user_by_id_tool.py`, `search_users_tool.py`). Each TODO file contains step-by-step implementation instructions in comments.

### Patterns

- All tools return `str` from `execute()` — results are inserted into conversation as tool messages.
- Tool `input_schema` follows JSON Schema format matching OpenAI function calling spec.
- User tools validate input via Pydantic's `model_validate()` and generate schemas via `model_json_schema()`.
- `tool_call_id` must be preserved in tool response messages to maintain LLM correlation with the originating assistant tool_calls.
