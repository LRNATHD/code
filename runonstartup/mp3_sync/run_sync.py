import sync_engine
import time

def run_once():
    # Simulate start state
    sync_engine._update_state(
        running=True,
        current_playlist="Starting Sync...",
        tracks_done=0,
        errors=[],
    )
    
    try:
        # Run worker synchronously
        sync_engine._sync_worker()
    except KeyboardInterrupt:
        sync_engine.log_to_manager("Sync interrupted by user")
    finally:
        sync_engine._update_state(running=False)

if __name__ == "__main__":
    run_once()
