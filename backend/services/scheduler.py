"""
SCHEDULER SERVICE - Automated task scheduling
- Uses APScheduler to run daily stock price updates
- Runs daily at 4:30 PM ET (after NYSE market close)
- Can also be triggered manually via API endpoint
"""

import logging
import threading
import pytz
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Configure logging
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None
is_scheduler_running = False
_update_lock = threading.Lock()
_update_state = {
    "running": False,
    "last_started_at": None,
    "last_finished_at": None,
    "last_trigger": None,
    "last_result": None,
}


def _run_daily_update_with_state(trigger: str):
    """Run daily update and track execution state for cron/status endpoints."""
    if not _update_lock.acquire(blocking=False):
        return {
            "success": False,
            "status": "already_running",
            "message": "Daily update is already in progress"
        }

    _update_state["running"] = True
    _update_state["last_started_at"] = datetime.now().isoformat()
    _update_state["last_trigger"] = trigger

    try:
        logger.info(f"[SCHEDULER] Starting daily update job at {datetime.now()} (trigger={trigger})")

        # Import here to avoid circular imports
        from scripts.daily_update import run_daily_update

        result = run_daily_update()
        _update_state["last_result"] = result

        if result.get("success"):
            logger.info(
                f"[SCHEDULER] Daily update completed: "
                f"{result['updated']} updated, "
                f"{result['current']} current, "
                f"{result['failed']} failed"
            )
        else:
            logger.error(f"[SCHEDULER] Daily update failed: {result.get('error')}")

        return result
    except Exception as e:
        logger.error(f"[SCHEDULER] Daily update job error: {e}", exc_info=True)
        error_result = {"success": False, "error": str(e)}
        _update_state["last_result"] = error_result
        return error_result
    finally:
        _update_state["running"] = False
        _update_state["last_finished_at"] = datetime.now().isoformat()
        _update_lock.release()


def init_scheduler():
    """
    Initialize and start the background scheduler.
    This runs daily at 4:30 PM ET (after NYSE market close).
    """
    global scheduler, is_scheduler_running
    
    try:
        if scheduler is not None:
            logger.warning("Scheduler already initialized")
            return scheduler
        
        # Create background scheduler
        scheduler = BackgroundScheduler()
        
        # Set timezone to Eastern Time (NYSE timezone)
        eastern = pytz.timezone('US/Eastern')
        
        # Schedule daily update at 4:30 PM ET
        # This is after NYSE closes (4:00 PM ET)
        scheduler.add_job(
            run_daily_update_job,
            trigger=CronTrigger(hour=16, minute=30, timezone=eastern),
            id='daily_stock_update',
            name='Daily Stock Price Update',
            replace_existing=True,
            max_instances=1,  # Prevent concurrent runs
        )
        
        # Start the scheduler
        scheduler.start()
        is_scheduler_running = True
        
        logger.info("✓ Scheduler initialized and started")
        logger.info("  Job: Daily Stock Price Update")
        logger.info("  Time: 4:30 PM ET (Mon-Sun)")
        logger.info("  Timezone: US/Eastern")
        
        return scheduler
        
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}", exc_info=True)
        return None


def stop_scheduler():
    """Stop the background scheduler."""
    global scheduler, is_scheduler_running
    
    try:
        if scheduler is not None:
            scheduler.shutdown()
            is_scheduler_running = False
            logger.info("✓ Scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}", exc_info=True)


def run_daily_update_job():
    """
    Wrapper function to run the daily update job.
    Called by the scheduler at scheduled times.
    """
    return _run_daily_update_with_state("scheduler")


def trigger_daily_update_background(trigger: str = "api-cron"):
    """
    Trigger daily update in a background thread and return immediately.
    Useful for external cron endpoints that should not block on long tasks.
    """
    if _update_state["running"]:
        return {
            "success": False,
            "status": "already_running",
            "message": "Daily update is already in progress",
            "state": dict(_update_state),
        }

    thread = threading.Thread(
        target=_run_daily_update_with_state,
        args=(trigger,),
        daemon=True,
    )
    thread.start()

    return {
        "success": True,
        "status": "started",
        "message": "Daily update started in background",
        "state": dict(_update_state),
    }


def get_scheduler_status():
    """Get current scheduler status."""
    global scheduler, is_scheduler_running
    
    if scheduler is None:
        return {
            "running": False,
            "message": "Scheduler not initialized"
        }
    
    jobs = scheduler.get_jobs()
    
    return {
        "running": is_scheduler_running,
        "update_job": dict(_update_state),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in jobs
        ]
    }


def trigger_daily_update_now():
    """
    Manually trigger the daily update job immediately.
    Useful for testing and immediate updates.
    """
    try:
        logger.info("[MANUAL] Triggering daily update...")
        result = run_daily_update_job()
        return result
    except Exception as e:
        logger.error(f"Failed to trigger daily update: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
