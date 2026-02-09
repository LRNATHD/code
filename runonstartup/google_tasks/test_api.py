import logging
import os
import sys

# Add current directory to path so we can import local modules
sys.path.append(os.getcwd())

from tasks_client import get_tasks_client, get_rules_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_google_tasks_connection():
    try:
        logger.info("Initializing Tasks Client...")
        client = get_tasks_client()
        
        logger.info("Attempting to fetch task lists...")
        task_lists = client.get_task_lists()
        
        if not task_lists:
            logger.warning("No task lists found (or API returned empty list).")
        else:
            logger.info(f"Successfully retrieved {len(task_lists)} task lists:")
            for tl in task_lists:
                logger.info(f" - {tl['title']} (ID: {tl['id']})")
                
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Google Tasks: {e}")
        return False

if __name__ == "__main__":
    if test_google_tasks_connection():
        print("\n[SUCCESS] Connected to Google Tasks API!")
    else:
        print("\n[FAILURE] Could not connect to Google Tasks API.")
