# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a TickTick MCP (Model Context Protocol) server that provides tools for interacting with the TickTick task management service through Claude Desktop. The server implements OAuth2 authentication and offers comprehensive task and project management capabilities.

## Key Commands

```bash
# Install dependencies (using uv package manager)
uv pip install -e .

# Run authentication flow
uv run -m ticktick_mcp.cli auth

# Start the MCP server
uv run -m ticktick_mcp.cli run

# Test server configuration and API connectivity
uv run test_server.py

# Alternative: Install with pip
pip install -e .
python -m ticktick_mcp.cli auth
python -m ticktick_mcp.cli run
```

## Architecture

The codebase follows a modular structure:

- **Entry Points**: 
  - `ticktick_mcp/cli.py` - Main CLI interface with `run` and `auth` subcommands
  - `ticktick_mcp/authenticate.py` - Standalone authentication utility

- **Core Components**:
  - `ticktick_mcp/src/server.py` - FastMCP-based server implementing 15 MCP tools
  - `ticktick_mcp/src/ticktick_client.py` - TickTick API client with OAuth2 token management
  - `ticktick_mcp/src/auth.py` - OAuth2 flow implementation

## MCP Tools Structure

The server provides these tool categories:

1. **Project Management**: get_projects, get_project, create_project, delete_project
2. **Task Operations**: get_task, create_task, update_task, complete_task, delete_task
3. **Specialized Creation**: create_basic_task, create_subtask, create_checklist, create_checklist_task
4. **Project Tasks**: get_project_tasks

Each tool is implemented as an async function decorated with `@mcp.tool()` in server.py.

## Environment Configuration

Required environment variables (stored in .env):
- `TICKTICK_CLIENT_ID` - OAuth application client ID
- `TICKTICK_CLIENT_SECRET` - OAuth application client secret
- `TICKTICK_ACCESS_TOKEN` - Auto-populated by auth flow
- `TICKTICK_REFRESH_TOKEN` - Auto-populated by auth flow

For Dida365 (Chinese version), additional variables can be set:
- `TICKTICK_BASE_URL`
- `TICKTICK_AUTH_URL`
- `TICKTICK_TOKEN_URL`

## Key Implementation Details

- **Authentication**: OAuth2 flow with automatic token refresh in ticktick_client.py
- **Date Handling**: All dates use ISO format YYYY-MM-DDThh:mm:ss+0000
- **Priority Levels**: 0 (None), 1 (Low), 3 (Medium), 5 (High)
- **Task Status**: 0 (incomplete), 2 (complete) for checklist items
- **Error Handling**: Comprehensive try-catch blocks with detailed error messages
- **Logging**: Uses Python logging module for debugging

## Testing

Run `test_server.py` to verify:
- Environment variables are correctly set
- OAuth tokens are valid
- API connectivity is working
- Basic project listing functionality

## Integration with Claude Desktop

The server is configured via Claude Desktop's JSON configuration file, typically at:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Configuration format:
```json
{
  "mcpServers": {
    "ticktick": {
      "command": "uv",
      "args": ["run", "-m", "ticktick_mcp.cli", "run"]
    }
  }
}
```