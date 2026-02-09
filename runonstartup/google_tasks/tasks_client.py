"""Google Tasks API Client with custom automation features."""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config


class TaskRule:
    """A rule for automating task modifications."""
    
    def __init__(self, rule_id: str, name: str, task_pattern: str, 
                 task_list_id: str, increment_type: str, increment_value: float,
                 enabled: bool = True):
        self.rule_id = rule_id
        self.name = name
        self.task_pattern = task_pattern  # Regex pattern to match task titles
        self.task_list_id = task_list_id
        self.increment_type = increment_type  # 'time_seconds', 'count', 'duration_format'
        self.increment_value = increment_value  # Amount to increment
        self.enabled = enabled
    
    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "task_pattern": self.task_pattern,
            "task_list_id": self.task_list_id,
            "increment_type": self.increment_type,
            "increment_value": self.increment_value,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TaskRule':
        return cls(
            rule_id=data["rule_id"],
            name=data["name"],
            task_pattern=data["task_pattern"],
            task_list_id=data["task_list_id"],
            increment_type=data["increment_type"],
            increment_value=data["increment_value"],
            enabled=data.get("enabled", True)
        )


def parse_duration(duration_str: str) -> Optional[int]:
    """Parse a duration string like '1:30' or '2:05' into total seconds."""
    # Match patterns like "1:30", "02:05", "1:00"
    match = re.match(r'^(\d+):(\d{2})$', duration_str.strip())
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        return minutes * 60 + seconds
    return None


def format_duration(total_seconds: int) -> str:
    """Format total seconds into 'M:SS' format."""
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"


def extract_and_increment_value(title: str, pattern: str, increment_type: str, 
                                  increment_value: float) -> Optional[str]:
    """Extract a value from a task title and return the incremented version."""
    try:
        regex = re.compile(pattern)
        match = regex.search(title)
        
        if not match:
            return None
        
        if increment_type == 'duration_format':
            # Find duration pattern like "1:30" in the title
            duration_match = re.search(r'(\d+:\d{2})', title)
            if duration_match:
                current_duration = duration_match.group(1)
                total_seconds = parse_duration(current_duration)
                if total_seconds is not None:
                    new_seconds = total_seconds + int(increment_value)
                    new_duration = format_duration(new_seconds)
                    return title.replace(current_duration, new_duration)
        
        elif increment_type == 'count':
            # Find a number in the matched portion
            if match.groups():
                for group in match.groups():
                    if group and group.isdigit():
                        old_value = int(group)
                        new_value = old_value + int(increment_value)
                        return title.replace(str(old_value), str(new_value), 1)
        
        elif increment_type == 'time_seconds':
            # Similar to duration_format but specified in seconds
            duration_match = re.search(r'(\d+:\d{2})', title)
            if duration_match:
                current_duration = duration_match.group(1)
                total_seconds = parse_duration(current_duration)
                if total_seconds is not None:
                    new_seconds = total_seconds + int(increment_value)
                    new_duration = format_duration(new_seconds)
                    return title.replace(current_duration, new_duration)
    
    except re.error:
        pass
    
    return None


class TasksClient:
    """Client for interacting with Google Tasks API."""
    
    def __init__(self):
        self.creds = None
        self.service = None
        self._load_credentials()
    
    def _load_credentials(self):
        """Load or refresh OAuth credentials."""
        if config.GOOGLE_TOKEN_FILE.exists():
            self.creds = Credentials.from_authorized_user_file(
                str(config.GOOGLE_TOKEN_FILE), config.SCOPES
            )
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not config.GOOGLE_CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(
                        f"Google credentials file not found at {config.GOOGLE_CREDENTIALS_FILE}. "
                        "Please download your OAuth credentials from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(config.GOOGLE_CREDENTIALS_FILE), config.SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            config.GOOGLE_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(config.GOOGLE_TOKEN_FILE, 'w') as token:
                token.write(self.creds.to_json())
        
        self.service = build('tasks', 'v1', credentials=self.creds)
    
    def is_authenticated(self) -> bool:
        """Check if we have valid credentials."""
        return self.creds is not None and self.creds.valid
    
    def get_task_lists(self) -> list[dict]:
        """Get all task lists."""
        try:
            results = self.service.tasklists().list().execute()
            return results.get('items', [])
        except Exception as e:
            print(f"Error getting task lists: {e}")
            return []
    
    def get_tasks(self, task_list_id: str, show_completed: bool = False,
                  show_hidden: bool = False) -> list[dict]:
        """Get all tasks from a specific task list."""
        try:
            results = self.service.tasks().list(
                tasklist=task_list_id,
                showCompleted=show_completed,
                showHidden=show_hidden
            ).execute()
            return results.get('items', [])
        except Exception as e:
            print(f"Error getting tasks: {e}")
            return []
    
    def get_task(self, task_list_id: str, task_id: str) -> Optional[dict]:
        """Get a specific task."""
        try:
            return self.service.tasks().get(
                tasklist=task_list_id,
                task=task_id
            ).execute()
        except Exception as e:
            print(f"Error getting task: {e}")
            return None
    
    def update_task(self, task_list_id: str, task_id: str, 
                    updates: dict) -> Optional[dict]:
        """Update a task with the given updates."""
        try:
            task = self.get_task(task_list_id, task_id)
            if not task:
                return None
            
            task.update(updates)
            return self.service.tasks().update(
                tasklist=task_list_id,
                task=task_id,
                body=task
            ).execute()
        except Exception as e:
            print(f"Error updating task: {e}")
            return None
    
    def create_task(self, task_list_id: str, title: str, 
                    due: Optional[datetime] = None,
                    notes: Optional[str] = None) -> Optional[dict]:
        """Create a new task."""
        try:
            body = {"title": title}
            if due:
                body["due"] = due.isoformat() + "Z"
            if notes:
                body["notes"] = notes
            
            return self.service.tasks().insert(
                tasklist=task_list_id,
                body=body
            ).execute()
        except Exception as e:
            print(f"Error creating task: {e}")
            return None
    
    def complete_task(self, task_list_id: str, task_id: str) -> Optional[dict]:
        """Mark a task as completed."""
        return self.update_task(task_list_id, task_id, {"status": "completed"})
    
    def delete_task(self, task_list_id: str, task_id: str) -> bool:
        """Delete a task."""
        try:
            self.service.tasks().delete(
                tasklist=task_list_id,
                task=task_id
            ).execute()
            return True
        except Exception as e:
            print(f"Error deleting task: {e}")
            return False

    def check_daily_progressions(self, rules_manager: 'RulesManager') -> list[str]:
        """
        Check for completed tasks that match rules and create the next iteration.
        Returns a list of messages about actions taken.
        """
        messages = []
        rules = rules_manager.get_all_rules()
        
        # Group rules by task list to minimize API calls
        rules_by_list = {}
        for rule in rules:
            if not rule.enabled:
                continue
            if rule.task_list_id not in rules_by_list:
                rules_by_list[rule.task_list_id] = []
            rules_by_list[rule.task_list_id].append(rule)
            
        for list_id, list_rules in rules_by_list.items():
            # fetch both Completed (to see what was done) and Active (to see if next exists)
            tasks = self.get_tasks(list_id, show_completed=True, show_hidden=True)
            
            for rule in list_rules:
                # Find all tasks matching this rule
                matching_tasks = []
                regex = re.compile(rule.task_pattern)
                
                for task in tasks:
                    if regex.search(task['title']):
                        matching_tasks.append(task)
                
                if not matching_tasks:
                    continue
                    
                # Sort by updated time (most recent first)
                matching_tasks.sort(key=lambda x: x.get('updated', ''), reverse=True)
                
                print(f"[Debug] Found {len(matching_tasks)} matches for rule '{rule.name}': {[t['title'] for t in matching_tasks[:3]]}") # Debug log
                
                # Iterate through recent matching tasks to find one that needs a successor
                # We check the top 5 most recent tasks to avoid getting blocked by 
                # a recently updated task that doesn't strictly match the increment format
                # or is already handled.
                for latest_task in matching_tasks[:5]:
                    # If the task is NOT completed, it's the current active one. 
                    # We don't need to do anything yet.
                    if latest_task.get('status') != 'completed':
                        continue
                        
                    # Calculate next title
                    next_title = extract_and_increment_value(
                        latest_task['title'],
                        rule.task_pattern,
                        rule.increment_type,
                        rule.increment_value
                    )
                    
                    if not next_title:
                        # This task matched the regex but failed the increment logic 
                        # (e.g. matched "plank" but had no time "60s" vs "1:00")
                        continue
                        
                    # Check if next task already exists (in active or completed)
                    successor_status = None # 'active', 'completed', or None
                    
                    for t in tasks: # Check against ALL tasks in list
                        if t['title'] == next_title:
                            if t['status'] != 'completed':
                                successor_status = 'active'
                                break
                            else:
                                # It was completed. Was it completed recently?
                                # If it was completed recently, it counts as "existing" for the purpose of the chain.
                                completed_date_str = t.get('completed')
                                if completed_date_str:
                                     completed_date = datetime.fromisoformat(completed_date_str.replace('Z', '+00:00')).date()
                                     today = datetime.now().date()
                                     if completed_date >= today:
                                         successor_status = 'completed'
                                         # Don't break yet, keep looking for an active one if duplicates exist
                                         # But we can prioritize active.
                    
                    if successor_status == 'active':
                        # The successor is active, waiting for user. 
                        # The chain is healthy and up-to-date.
                        # Stop checking to avoid creating duplicates or traversing further back.
                        break
                    
                    if successor_status == 'completed':
                        # The successor exists but is already done.
                        # This current task is NOT the tip of the spear.
                        # We should continue the loop to find the task that IS the tip (likely the successor itself).
                        continue
                    
                    # If we get here, successor_status is None.
                    # The successor does NOT exist. Create it!
                    
                    # Determine due date
                    completed_date_str = latest_task.get('completed')
                    if completed_date_str:
                         completed_date = datetime.fromisoformat(completed_date_str.replace('Z', '+00:00'))
                         completed_date_day = completed_date.date()
                         today = datetime.now().date()
                         
                         if completed_date_day == today:
                             due_date = datetime.now() + timedelta(days=1)
                         else:
                             # If it was completed yesterday (or earlier), the new one is due today
                             due_date = datetime.now()
                    else:
                        due_date = datetime.now()
                         
                    new_task = self.create_task(
                        list_id,
                        next_title,
                        due=due_date,
                        notes=f"Auto-generated from rule: {rule.name}"
                    )
                    
                    if new_task:
                        messages.append(f"Created '{next_title}' based on completed '{latest_task['title']}'")
                        # We handled the valid chain gap, so stop.
                        break
        
        return messages


class RulesManager:
    """Manager for task automation rules."""
    
    def __init__(self):
        self.rules: list[TaskRule] = []
        self._load_rules()
    
    def _load_rules(self):
        """Load rules from file."""
        if config.RULES_FILE.exists():
            try:
                with open(config.RULES_FILE, 'r') as f:
                    data = json.load(f)
                    self.rules = [TaskRule.from_dict(r) for r in data.get('rules', [])]
            except Exception as e:
                print(f"Error loading rules: {e}")
                self.rules = []
    
    def _save_rules(self):
        """Save rules to file."""
        try:
            with open(config.RULES_FILE, 'w') as f:
                json.dump({
                    'rules': [r.to_dict() for r in self.rules],
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving rules: {e}")
    
    def add_rule(self, rule: TaskRule):
        """Add a new rule."""
        self.rules.append(rule)
        self._save_rules()
    
    def update_rule(self, rule_id: str, updates: dict) -> bool:
        """Update an existing rule."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                self._save_rules()
                return True
        return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule."""
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.rule_id != rule_id]
        if len(self.rules) < initial_count:
            self._save_rules()
            return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[TaskRule]:
        """Get a rule by ID."""
        return next((r for r in self.rules if r.rule_id == rule_id), None)
    
    def get_all_rules(self) -> list[TaskRule]:
        """Get all rules."""
        return self.rules
    
    def get_matching_rules(self, task_title: str, task_list_id: str) -> list[TaskRule]:
        """Get all rules that match a given task."""
        matching = []
        for rule in self.rules:
            if not rule.enabled:
                continue
            if rule.task_list_id and rule.task_list_id != task_list_id:
                continue
            try:
                if re.search(rule.task_pattern, task_title):
                    matching.append(rule)
            except re.error:
                continue
        return matching


# Singleton instances
_tasks_client: Optional[TasksClient] = None
_rules_manager: Optional[RulesManager] = None


def get_tasks_client() -> TasksClient:
    """Get or create the TasksClient singleton."""
    global _tasks_client
    if _tasks_client is None:
        _tasks_client = TasksClient()
    return _tasks_client


def get_rules_manager() -> RulesManager:
    """Get or create the RulesManager singleton."""
    global _rules_manager
    if _rules_manager is None:
        _rules_manager = RulesManager()
    return _rules_manager
