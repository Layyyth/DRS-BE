from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.user import User
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_unverified_users():
    """Deletes users who haven't verified their emails within 48 hours."""
    
    db: Session = SessionLocal()
    expiration_time = datetime.now(timezone.utc) - timedelta(hours=48)

    try:
        deleted_users = db.query(User).filter(
            User.is_verified == False,
            User.created_at <= expiration_time
        ).delete(synchronize_session=False)

        if deleted_users > 0:
            logger.info(f"Deleted {deleted_users} unverified users.")

        db.commit()
    except Exception as e:
        logger.error(f"Error deleting unverified users: {e}")
        db.rollback()
    finally:
        db.close()


scheduler = BackgroundScheduler()
scheduler.add_job(delete_unverified_users, IntervalTrigger(hours=1), id="delete_unverified_users", replace_existing=True)
scheduler.start()

def stop_scheduler():
    """Stops the scheduler when the app shuts down."""
    scheduler.shutdown()
