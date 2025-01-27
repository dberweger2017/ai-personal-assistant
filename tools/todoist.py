from todoist_api_python.api_async import TodoistAPIAsync
from todoist_api_python.api import TodoistAPI
from datetime import datetime, timezone
from dateutil import tz
import os

TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")

api = TodoistAPI(TODOIST_API_KEY)

def create_new_task(content, due_string=None, project_id=None, priority=1):
    """
    Create a new task in Todoist.

    Args:
        content (str): The content or title of the task (required).
        due_string (str): Natural language due date (optional, e.g., "tomorrow at 2pm").
        project_id (str): The ID of the project to add the task to (optional).
        priority (int): Priority level of the task (1=low, 4=high).

    Returns:
        dict: The created task details if successful, None otherwise.
    """
    try:
        new_task = api.add_task(
            content=content,
            due_string=due_string,
            project_id=project_id,
            priority=priority
        )
        print(f"Task created successfully: {new_task.content} (ID: {new_task.id})")
        return new_task.to_dict()
    except Exception as e:
        message = f"Error creating task: {e}"
        print(message)
        return {'success': False, 'message': message}
    

def get_filtered_tasks(
    project_id=None, 
    label_ids=None, 
    due_before=None, 
    due_after=None, 
    priority=None, 
    include_completed=False
):
    """
    Retrieve tasks with multiple filters and return them as a dictionary.

    Args:
        project_id (str): Filter tasks by project ID (optional).
        label_ids (list): Filter tasks by label IDs (optional).
        due_before (str): ISO 8601 date to filter tasks due on or before this date (optional).
        due_after (str): ISO 8601 date to filter tasks due on or after this date (optional).
        priority (int): Filter tasks by priority (1=low, 4=high) (optional).
        include_completed (bool): Include completed tasks in the results (optional).

    Returns:
        dict: A dictionary of tasks matching the filters, with task ID as the key.
    """
    try:
        tasks = api.get_tasks()

        print(len(tasks), "tasks retrieved")

        # Convert due_before and due_after to timezone-aware datetime objects
        due_before_dt = datetime.fromisoformat(due_before.replace("Z", "+00:00")) if due_before else None
        due_after_dt = datetime.fromisoformat(due_after.replace("Z", "+00:00")) if due_after else None

        # Filter tasks based on conditions
        filtered_tasks = [
            {
                "completed": task.is_completed,
                "content": task.content,
                "due": str(task.due),
                "priority": task.priority,
                "created_at": task.created_at,
                "url": task.url,
                "duration": task.duration,
                "id": task.id
            }
            for task in tasks
            if (project_id is None or task.project_id == project_id) and
               (label_ids is None or any(label_id in task.label_ids for label_id in label_ids)) and
               (due_before_dt is None or (task.due and datetime.fromisoformat(task.due.date).replace(tzinfo=tz.UTC) <= due_before_dt)) and
               (due_after_dt is None or (task.due and datetime.fromisoformat(task.due.date).replace(tzinfo=tz.UTC) >= due_after_dt)) and
               (priority is None or task.priority == priority) and
               (include_completed or not task.is_completed)
        ]

        print(f"Found {len(filtered_tasks)} task(s) matching the filters.")
        
        # Convert the list of tasks to a dictionary with task ID as the key
        tasks_dict = {task["id"]: task for task in filtered_tasks}
        
        return tasks_dict
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return {'success': False, 'message': str(e)}

if __name__ == "__main__":
    print(get_filtered_tasks())
