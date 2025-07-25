import asyncio
import json
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from .ticktick_client import TickTickClient

# Set up logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP("ticktick")

# Create TickTick client
ticktick = None

def initialize_client():
    global ticktick
    try:
        # Check if .env file exists with access token
        load_dotenv()
        
        # Check if we have valid credentials
        if os.getenv("TICKTICK_ACCESS_TOKEN") is None:
            logger.error("No access token found in .env file. Please run 'uv run -m ticktick_mcp.cli auth' to authenticate.")
            return False
        
        # Initialize the client
        ticktick = TickTickClient()
        logger.info("TickTick client initialized successfully")
        
        # Test API connectivity
        projects = ticktick.get_projects()
        if 'error' in projects:
            logger.error(f"Failed to access TickTick API: {projects['error']}")
            logger.error("Your access token may have expired. Please run 'uv run -m ticktick_mcp.cli auth' to refresh it.")
            return False
            
        logger.info(f"Successfully connected to TickTick API with {len(projects)} projects")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize TickTick client: {e}")
        return False

# Format a task object from TickTick for better display
def format_task(task: Dict) -> str:
    """Format a task into a human-readable string."""
    formatted = f"ID: {task.get('id', 'No ID')}\n"
    formatted += f"Title: {task.get('title', 'No title')}\n"
    
    # Add project ID
    formatted += f"Project ID: {task.get('projectId', 'None')}\n"
    
    # Add dates if available
    if task.get('startDate'):
        formatted += f"Start Date: {task.get('startDate')}\n"
    if task.get('dueDate'):
        formatted += f"Due Date: {task.get('dueDate')}\n"
    
    # Add priority if available
    priority_map = {0: "None", 1: "Low", 3: "Medium", 5: "High"}
    priority = task.get('priority', 0)
    formatted += f"Priority: {priority_map.get(priority, str(priority))}\n"
    
    # Add status if available
    status = "Completed" if task.get('status') == 2 else "Active"
    formatted += f"Status: {status}\n"
    
    # Add content if available
    if task.get('content'):
        formatted += f"\nContent:\n{task.get('content')}\n"
    
    # Add desc if available (for checklist tasks)
    if task.get('desc'):
        formatted += f"\nDescription:\n{task.get('desc')}\n"
    
    # Add items if available (checklist items/subtasks)
    items = task.get('items', [])
    if items:
        formatted += f"\nChecklist Items ({len(items)}):\n"
        for i, item in enumerate(items, 1):
            status_icon = "✓" if item.get('status', 0) == 2 else "○"
            formatted += f"  {status_icon} {item.get('title', 'Untitled item')}\n"
    
    # Add tags if available
    tags = task.get('tags', [])
    if tags:
        formatted += f"\nTags: {', '.join(tags)}\n"
    
    return formatted

# Format a project object from TickTick for better display
def format_project(project: Dict) -> str:
    """Format a project into a human-readable string."""
    formatted = f"Name: {project.get('name', 'No name')}\n"
    formatted += f"ID: {project.get('id', 'No ID')}\n"
    
    # Add color if available
    if project.get('color'):
        formatted += f"Color: {project.get('color')}\n"
    
    # Add view mode if available
    if project.get('viewMode'):
        formatted += f"View Mode: {project.get('viewMode')}\n"
    
    # Add closed status if available
    if 'closed' in project:
        formatted += f"Closed: {'Yes' if project.get('closed') else 'No'}\n"
    
    # Add kind if available
    if project.get('kind'):
        formatted += f"Kind: {project.get('kind')}\n"
    
    return formatted

# MCP Tools

@mcp.tool()
async def get_projects() -> str:
    """Get all projects from TickTick."""
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        projects = ticktick.get_projects()
        if 'error' in projects:
            return f"Error fetching projects: {projects['error']}"
        
        if not projects:
            return "No projects found."
        
        result = f"Found {len(projects)} projects:\n\n"
        for i, project in enumerate(projects, 1):
            result += f"Project {i}:\n" + format_project(project) + "\n"
        
        return result
    except Exception as e:
        logger.error(f"Error in get_projects: {e}")
        return f"Error retrieving projects: {str(e)}"

@mcp.tool()
async def get_project(project_id: str) -> str:
    """
    Get details about a specific project.
    
    Args:
        project_id: ID of the project
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        project = ticktick.get_project(project_id)
        if 'error' in project:
            return f"Error fetching project: {project['error']}"
        
        return format_project(project)
    except Exception as e:
        logger.error(f"Error in get_project: {e}")
        return f"Error retrieving project: {str(e)}"

@mcp.tool()
async def get_project_tasks(project_id: str) -> str:
    """
    Get all tasks in a specific project.
    
    Args:
        project_id: ID of the project
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        project_data = ticktick.get_project_with_data(project_id)
        if 'error' in project_data:
            return f"Error fetching project data: {project_data['error']}"
        
        tasks = project_data.get('tasks', [])
        if not tasks:
            return f"No tasks found in project '{project_data.get('project', {}).get('name', project_id)}'."
        
        result = f"Found {len(tasks)} tasks in project '{project_data.get('project', {}).get('name', project_id)}':\n\n"
        for i, task in enumerate(tasks, 1):
            result += f"Task {i}:\n" + format_task(task) + "\n"
        
        return result
    except Exception as e:
        logger.error(f"Error in get_project_tasks: {e}")
        return f"Error retrieving project tasks: {str(e)}"

@mcp.tool()
async def get_task(project_id: str, task_id: str) -> str:
    """
    Get details about a specific task.
    
    Args:
        project_id: ID of the project
        task_id: ID of the task
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        task = ticktick.get_task(project_id, task_id)
        if 'error' in task:
            return f"Error fetching task: {task['error']}"
        
        return format_task(task)
    except Exception as e:
        logger.error(f"Error in get_task: {e}")
        return f"Error retrieving task: {str(e)}"

@mcp.tool()
async def create_task(
    title: str, 
    project_id: str, 
    content: str = None,
    desc: str = None, 
    start_date: str = None, 
    due_date: str = None, 
    priority: int = 0,
    tags: List[str] = None,
    items: List[Dict[str, Any]] = None,
    kind: str = None,
    parent_id: str = None
) -> str:
    """
    Create a new task in TickTick.
    
    Args:
        title: Task title
        project_id: ID of the project to add the task to
        content: Task description/content (optional)
        desc: Description of checklist (optional) - use this WITH items to create a checklist (do NOT use content)
        start_date: Start date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
        due_date: Due date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
        priority: Priority level (0: None, 1: Low, 3: Medium, 5: High) (optional)
        tags: List of tags to add to the task (optional)
        items: List of checklist items, each with 'title' and optional 'status' (0: incomplete, 2: complete) (optional)
        kind: Task type - "CHECKLIST" for checklist tasks (optional)
        parent_id: ID of the parent task to create this as a subtask (optional)
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    # Validate priority
    if priority not in [0, 1, 3, 5]:
        return "Invalid priority. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)."
    
    try:
        # Validate dates if provided
        for date_str, date_name in [(start_date, "start_date"), (due_date, "due_date")]:
            if date_str:
                try:
                    # Try to parse the date to validate it
                    datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    return f"Invalid {date_name} format. Use ISO format: YYYY-MM-DDThh:mm:ss+0000"
        
        # For checklists, we should use desc and NOT content
        if desc and items:
            # This is a checklist - don't include content
            task = ticktick.create_task(
                title=title,
                project_id=project_id,
                desc=desc,
                start_date=start_date,
                due_date=due_date,
                priority=priority,
                tags=tags,
                items=items,
                parent_id=parent_id,
                is_all_day=False  # Important for checklists
            )
        else:
            # Regular task
            task = ticktick.create_task(
                title=title,
                project_id=project_id,
                content=content,
                desc=desc,
                start_date=start_date,
                due_date=due_date,
                priority=priority,
                tags=tags,
                items=items,
                kind=kind,
                parent_id=parent_id,
                is_all_day=False
            )
        
        if 'error' in task:
            return f"Error creating task: {task['error']}"
        
        return f"Task created successfully:\n\n" + format_task(task)
    except Exception as e:
        logger.error(f"Error in create_task: {e}")
        return f"Error creating task: {str(e)}"

@mcp.tool()
async def create_checklist(
    title: str,
    project_id: str,
    desc: str,
    items: List[Dict[str, Any]],
    priority: int = 0,
    tags: List[str] = None
) -> str:
    """
    Create a checklist task with visible items in TickTick.
    
    This is a specialized function for creating checklists that ensures all items
    are visible in the TickTick UI.
    
    Args:
        title: Checklist title
        project_id: ID of the project to add the checklist to
        desc: Description of the checklist (required for checklists)
        items: List of checklist items, each with 'title' and optional 'status' (0: incomplete, 2: complete)
        priority: Priority level (0: None, 1: Low, 3: Medium, 5: High) (optional)
        tags: List of tags to add to the checklist (optional)
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        # Create the checklist - use desc instead of content for checklists
        task = ticktick.create_task(
            title=title,
            project_id=project_id,
            desc=desc,  # desc makes it a checklist
            priority=priority,
            tags=tags,
            items=items,
            is_all_day=False  # Important for checklists
        )
        
        if 'error' in task:
            return f"Error creating checklist: {task['error']}"
        
        return f"Checklist created successfully:\n\n" + format_task(task)
    except Exception as e:
        logger.error(f"Error in create_checklist: {e}")
        return f"Error creating checklist: {str(e)}"

@mcp.tool()
async def create_basic_task(
    title: str, 
    project_id: str, 
    content: str = None,
    start_date: str = None, 
    due_date: str = None, 
    priority: int = 0,
    tags: List[str] = None
) -> str:
    """
    Create a basic task (no subtasks or checklists).
    
    Args:
        title: Task title
        project_id: ID of the project to add the task to
        content: Task description/content (optional)
        start_date: Start date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
        due_date: Due date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
        priority: Priority level (0: None, 1: Low, 3: Medium, 5: High) (optional)
        tags: List of tags to add to the task (optional)
    """
    return await create_task(
        title=title,
        project_id=project_id,
        content=content,
        start_date=start_date,
        due_date=due_date,
        priority=priority,
        tags=tags
    )

@mcp.tool()
async def create_subtask(
    title: str,
    project_id: str,
    parent_task_id: str,
    content: str = None,
    start_date: str = None,
    due_date: str = None,
    priority: int = 0,
    tags: List[str] = None
) -> str:
    """
    Create a subtask under an existing task.
    
    Args:
        title: Task title
        project_id: ID of the project
        parent_task_id: ID of the parent task (required)
        content: Task description/content (optional)
        start_date: Start date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
        due_date: Due date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
        priority: Priority level (0: None, 1: Low, 3: Medium, 5: High) (optional)
        tags: List of tags to add to the task (optional)
    """
    return await create_task(
        title=title,
        project_id=project_id,
        parent_id=parent_task_id,
        content=content,
        start_date=start_date,
        due_date=due_date,
        priority=priority,
        tags=tags
    )

@mcp.tool()
async def create_checklist_task(
    title: str,
    project_id: str,
    items: List[str],
    priority: int = 0,
    tags: List[str] = None
) -> str:
    """
    Create a task with a checklist. Accepts a simple list of strings for checklist items.
    
    Args:
        title: Task title
        project_id: ID of the project to add the checklist to
        items: List of checklist item titles (as strings)
        priority: Priority level (0: None, 1: Low, 3: Medium, 5: High) (optional)
        tags: List of tags to add to the checklist (optional)
    """
    # Convert simple string list to proper item format
    formatted_items = [{"title": item, "status": 0} for item in items]
    
    return await create_checklist(
        title=title,
        project_id=project_id,
        desc=title,  # Use title as description for consistency
        items=formatted_items,
        priority=priority,
        tags=tags
    )

@mcp.tool()
async def update_task(
    task_id: str,
    project_id: str,
    title: str = None,
    content: str = None,
    desc: str = None,
    start_date: str = None,
    due_date: str = None,
    priority: int = None,
    tags: List[str] = None,
    items: List[Dict[str, Any]] = None
) -> str:
    """
    Update an existing task in TickTick.
    
    Args:
        task_id: ID of the task to update
        project_id: ID of the project the task belongs to
        title: New task title (optional)
        content: New task description/content (optional)
        desc: New checklist description (optional) - use this for checklist tasks
        start_date: New start date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
        due_date: New due date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
        priority: New priority level (0: None, 1: Low, 3: Medium, 5: High) (optional)
        tags: New list of tags for the task (optional)
        items: New list of checklist items, each with 'title' and optional 'status' (0: incomplete, 2: complete) (optional)
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    # Validate priority if provided
    if priority is not None and priority not in [0, 1, 3, 5]:
        return "Invalid priority. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)."
    
    try:
        # Validate dates if provided
        for date_str, date_name in [(start_date, "start_date"), (due_date, "due_date")]:
            if date_str:
                try:
                    # Try to parse the date to validate it
                    datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    return f"Invalid {date_name} format. Use ISO format: YYYY-MM-DDThh:mm:ss+0000"
        
        task = ticktick.update_task(
            task_id=task_id,
            project_id=project_id,
            title=title,
            content=content,
            desc=desc,
            start_date=start_date,
            due_date=due_date,
            priority=priority,
            tags=tags,
            items=items
        )
        
        if 'error' in task:
            return f"Error updating task: {task['error']}"
        
        return f"Task updated successfully:\n\n" + format_task(task)
    except Exception as e:
        logger.error(f"Error in update_task: {e}")
        return f"Error updating task: {str(e)}"

@mcp.tool()
async def complete_task(project_id: str, task_id: str) -> str:
    """
    Mark a task as complete.
    
    Args:
        project_id: ID of the project
        task_id: ID of the task
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        result = ticktick.complete_task(project_id, task_id)
        if 'error' in result:
            return f"Error completing task: {result['error']}"
        
        return f"Task {task_id} marked as complete."
    except Exception as e:
        logger.error(f"Error in complete_task: {e}")
        return f"Error completing task: {str(e)}"

@mcp.tool()
async def delete_task(project_id: str, task_id: str) -> str:
    """
    Delete a task.
    
    Args:
        project_id: ID of the project
        task_id: ID of the task
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        result = ticktick.delete_task(project_id, task_id)
        if 'error' in result:
            return f"Error deleting task: {result['error']}"
        
        return f"Task {task_id} deleted successfully."
    except Exception as e:
        logger.error(f"Error in delete_task: {e}")
        return f"Error deleting task: {str(e)}"

@mcp.tool()
async def create_project(
    name: str,
    color: str = "#F18181",
    view_mode: str = "list"
) -> str:
    """
    Create a new project in TickTick.
    
    Args:
        name: Project name
        color: Color code (hex format) (optional)
        view_mode: View mode - one of list, kanban, or timeline (optional)
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    # Validate view_mode
    if view_mode not in ["list", "kanban", "timeline"]:
        return "Invalid view_mode. Must be one of: list, kanban, timeline."
    
    try:
        project = ticktick.create_project(
            name=name,
            color=color,
            view_mode=view_mode
        )
        
        if 'error' in project:
            return f"Error creating project: {project['error']}"
        
        return f"Project created successfully:\n\n" + format_project(project)
    except Exception as e:
        logger.error(f"Error in create_project: {e}")
        return f"Error creating project: {str(e)}"

@mcp.tool()
async def delete_project(project_id: str) -> str:
    """
    Delete a project.
    
    Args:
        project_id: ID of the project
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        result = ticktick.delete_project(project_id)
        if 'error' in result:
            return f"Error deleting project: {result['error']}"
        
        return f"Project {project_id} deleted successfully."
    except Exception as e:
        logger.error(f"Error in delete_project: {e}")
        return f"Error deleting project: {str(e)}"

def main():
    """Main entry point for the MCP server."""
    # Initialize the TickTick client
    if not initialize_client():
        logger.error("Failed to initialize TickTick client. Please check your API credentials.")
        return
    
    # Run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()