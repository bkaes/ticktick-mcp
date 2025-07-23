# TickTick MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for TickTick that enables interacting with your TickTick task management system directly through Claude and other MCP clients.

## Features

- 📋 View all your TickTick projects and tasks
- ✏️ Create new projects and tasks through natural language
- 🔄 Update existing task details (title, content, dates, priority)
- ✅ Mark tasks as complete
- 🗑️ Delete tasks and projects
- 📝 Create and manage subtasks within tasks
- 🏷️ Add and manage tags on tasks
- 🔄 Full integration with TickTick's open API
- 🔌 Seamless integration with Claude and other MCP clients

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
- TickTick account with API access
- TickTick API credentials (Client ID, Client Secret, Access Token)

## Installation

1. **Clone this repository**:
   ```bash
   git clone https://github.com/jacepark12/ticktick-mcp.git
   cd ticktick-mcp
   ```

2. **Install with uv**:
   ```bash
   # Install uv if you don't have it already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create a virtual environment
   uv venv

   # Activate the virtual environment
   # On macOS/Linux:
   source .venv/bin/activate
   # On Windows:
   .venv\Scripts\activate

   # Install the package
   uv pip install -e .
   ```

3. **Authenticate with TickTick**:
   ```bash
   # Run the authentication flow
   uv run -m ticktick_mcp.cli auth
   ```

   This will:
   - Ask for your TickTick Client ID and Client Secret
   - Open a browser window for you to log in to TickTick
   - Automatically save your access tokens to a `.env` file

4. **Test your configuration**:
   ```bash
   uv run test_server.py
   ```
   This will verify that your TickTick credentials are working correctly.

## Authentication with TickTick

This server uses OAuth2 to authenticate with TickTick. The setup process is straightforward:

1. Register your application at the [TickTick Developer Center](https://developer.ticktick.com/manage)
   - Set the redirect URI to `http://localhost:8000/callback`
   - Note your Client ID and Client Secret

2. Run the authentication command:
   ```bash
   uv run -m ticktick_mcp.cli auth
   ```

3. Follow the prompts to enter your Client ID and Client Secret

4. A browser window will open for you to authorize the application with your TickTick account

5. After authorizing, you'll be redirected back to the application, and your access tokens will be automatically saved to the `.env` file

The server handles token refresh automatically, so you won't need to reauthenticate unless you revoke access or delete your `.env` file.

## Authentication with Dida365

[滴答清单 - Dida365](https://dida365.com/home) is China version of TickTick, and the authentication process is similar to TickTick. Follow these steps to set up Dida365 authentication:

1. Register your application at the [Dida365 Developer Center](https://developer.dida365.com/manage)
   - Set the redirect URI to `http://localhost:8000/callback`
   - Note your Client ID and Client Secret

2. Add environment variables to your `.env` file:
   ```env
   TICKTICK_BASE_URL='https://api.dida365.com/open/v1'
   TICKTICK_AUTH_URL='https://dida365.com/oauth/authorize'
   TICKTICK_TOKEN_URL='https://dida365.com/oauth/token'
   ```

3. Follow the same authentication steps as for TickTick

## Usage with Claude for Desktop

1. Install [Claude for Desktop](https://claude.ai/download)
2. Edit your Claude for Desktop configuration file:

   **macOS**:
   ```bash
   nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

   **Windows**:
   ```bash
   notepad %APPDATA%\Claude\claude_desktop_config.json
   ```

3. Add the TickTick MCP server configuration, using absolute paths:
   ```json
   {
      "mcpServers": {
         "ticktick": {
            "command": "<absolute path to uv>",
            "args": ["run", "--directory", "<absolute path to ticktick-mcp directory>", "-m", "ticktick_mcp.cli", "run"]
         }
      }
   }
   ```

4. Restart Claude for Desktop

Once connected, you'll see the TickTick MCP server tools available in Claude, indicated by the 🔨 (tools) icon.

## Available MCP Tools

### Project Management
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_projects` | List all your TickTick projects | None |
| `get_project` | Get details about a specific project | `project_id` |
| `create_project` | Create a new project | `name`, `color` (optional), `view_mode` (optional) |
| `delete_project` | Delete a project | `project_id` |

### Task Management
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_project_tasks` | List all tasks in a project | `project_id` |
| `get_task` | Get details about a specific task | `project_id`, `task_id` |
| `create_task` | Create a new task or checklist (general purpose) | `title`, `project_id`, `content` (optional for tasks), `desc` (required for checklists), `start_date` (optional), `due_date` (optional), `priority` (optional), `tags` (optional), `items` (optional), `parent_id` (optional) |
| `update_task` | Update an existing task | `task_id`, `project_id`, `title` (optional), `content` (optional), `desc` (optional), `start_date` (optional), `due_date` (optional), `priority` (optional), `tags` (optional), `items` (optional) |
| `complete_task` | Mark a task as complete | `project_id`, `task_id` |
| `delete_task` | Delete a task | `project_id`, `task_id` |

### Specialized Task Creation Tools (Recommended)
These tools make task creation more explicit and less error-prone:

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_basic_task` | Create a simple task (no subtasks/checklists) | `title`, `project_id`, `content` (optional), `start_date` (optional), `due_date` (optional), `priority` (optional), `tags` (optional) |
| `create_subtask` | Create a subtask under an existing task | `title`, `project_id`, `parent_task_id` (required), `content` (optional), `start_date` (optional), `due_date` (optional), `priority` (optional), `tags` (optional) |
| `create_checklist_task` | Create a task with checklist items | `title`, `project_id`, `items` (required - list of strings), `priority` (optional), `tags` (optional) |

## Working with Checklists and Tags

### Creating Checklists with Items
To create a checklist with visible items in TickTick, use `create_task` with these CRITICAL requirements:

1. **MUST use `desc` field** for the checklist description
2. **MUST provide `items` array** with the checklist items
3. **DO NOT use `content` field** - if you include content, the checklist won't work!

#### Correct way to create a checklist:
```python
await create_task(
    title="Shopping List",
    project_id="your_project_id",
    desc="Weekly groceries",  # Required - this makes it a checklist
    items=[
        {"title": "Milk", "status": 0},
        {"title": "Bread", "status": 0},
        {"title": "Eggs", "status": 2}  # Already completed
    ],
    priority=3,
    tags=["shopping", "weekly"]
)
```

#### What NOT to do:
```python
# WRONG - This won't create a proper checklist!
await create_task(
    title="Shopping List",
    content="Weekly groceries",  # NO! Using content breaks checklists
    items=[...]  # Items won't be visible
)
```

### Important Notes on Checklists
- **Status values**: Use `0` for incomplete, `2` for complete (NOT 1!)
- **IDs**: TickTick automatically generates item IDs if not provided
- **The `desc` field is critical**: Using `content` instead of `desc` will create a regular task where items aren't visible
- **Regular tasks vs Checklists**: Regular tasks use `content` field, checklists use `desc` field

### Tags
Tags can be added to tasks to help with organization. Simply provide an array of tag names:
```json
{
  "tags": ["urgent", "personal", "health"]
}
```

## Example Prompts for Claude

Here are some example prompts to use with Claude after connecting the TickTick MCP server:

### Basic Commands
- "Show me all my TickTick projects"
- "List all tasks in my personal project"
- "Mark the task 'Buy groceries' as complete"
- "Create a new project called 'Vacation Planning' with a blue color"
- "When is my next deadline in TickTick?"

### Using Specialized Tools (Recommended)
- "Create a basic task called 'Finish MCP server documentation' in my work project with high priority"
- "Create a subtask 'Review code changes' under the task 'Complete PR #123'"
- "Create a checklist called 'Shopping List' with items: Milk, Bread, Eggs, Butter"
- "Make a morning routine checklist with items: Wake up at 7am, Exercise, Shower, Breakfast"
- "Add a subtask 'Book hotel' to my vacation planning task"

### Working with Tags
- "Create a task 'Prepare presentation' with tags 'urgent' and 'work'"
- "Add tags 'personal' and 'health' to my doctor appointment task"

## Development

### Project Structure

```
ticktick-mcp/
├── .env.template          # Template for environment variables
├── README.md              # Project documentation
├── requirements.txt       # Project dependencies
├── setup.py               # Package setup file
├── test_server.py         # Test script for server configuration
└── ticktick_mcp/          # Main package
    ├── __init__.py        # Package initialization
    ├── authenticate.py    # OAuth authentication utility
    ├── cli.py             # Command-line interface
    └── src/               # Source code
        ├── __init__.py    # Module initialization
        ├── auth.py        # OAuth authentication implementation
        ├── server.py      # MCP server implementation
        └── ticktick_client.py  # TickTick API client
```

### Authentication Flow

The project implements a complete OAuth 2.0 flow for TickTick:

1. **Initial Setup**: User provides their TickTick API Client ID and Secret
2. **Browser Authorization**: User is redirected to TickTick to grant access
3. **Token Reception**: A local server receives the OAuth callback with the authorization code
4. **Token Exchange**: The code is exchanged for access and refresh tokens
5. **Token Storage**: Tokens are securely stored in the local `.env` file
6. **Token Refresh**: The client automatically refreshes the access token when it expires

This simplifies the user experience by handling the entire OAuth flow programmatically.

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
