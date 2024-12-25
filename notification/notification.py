from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Notification(BaseModel):
    id: Optional[int] = None
    recipient_id: int
    type: NotificationType
    subject: str
    content: str
    status: NotificationStatus = NotificationStatus.PENDING
    scheduled_at: Optional[datetime] = None
    created_at: datetime = datetime.now()
    metadata: Optional[dict] = None

app = FastAPI()

# In-memory storage for notifications (replace with database in production)
notifications = {}
notification_id_counter = 1

@app.post("/notifications/", response_model=Notification)
async def send_notification(notification: Notification):
    logger.info(f"Received notification request for recipient {notification.recipient_id}")
    global notification_id_counter
    
    try:
        if notification.recipient_id < 0:
            logger.error(f"Invalid recipient ID: {notification.recipient_id}")
            raise HTTPException(status_code=400, detail="Recipient ID must be greater than 0")
        
        # Assign notification ID
        notification.id = notification_id_counter
        notification_id_counter += 1
        
        # If no scheduled time is set, default to immediate sending
        if not notification.scheduled_at:
            notification.scheduled_at = datetime.now()
            logger.info(f"Setting default schedule time to: {notification.scheduled_at}")
        
        logger.info(f"Storing notification with ID: {notification.id}")
        notifications[notification.id] = notification
        notification.status = NotificationStatus.SENT  # Simulating immediate send
        
        logger.info(f"Successfully processed notification {notification.id}")
        return notification
    except Exception as e:
        logger.error(f"Error processing notification: {str(e)}")
        raise

@app.put("/notifications/{notification_id}/cancel", response_model=Notification)
async def cancel_notification(notification_id: int):
    logger.info(f"Received cancellation request for notification {notification_id}")
    
    try:
        if notification_id not in notifications:
            logger.error(f"Notification not found: {notification_id}")
            raise HTTPException(status_code=404, detail="Notification not found")
        
        notification = notifications[notification_id]
        
        # Can only cancel pending notifications
        if notification.status != NotificationStatus.PENDING:
            logger.error(f"Cannot cancel notification {notification_id} in {notification.status} status")
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel notification in {notification.status} status"
            )
        
        notification.status = NotificationStatus.CANCELLED
        logger.info(f"Successfully cancelled notification {notification_id}")
        return notification
    except Exception as e:
        logger.error(f"Error cancelling notification: {str(e)}")
        raise

@app.post("/notifications/bulk", response_model=List[Notification])
async def send_bulk_notifications(notifications_list: List[Notification]):
    logger.info(f"Received bulk notification request for {len(notifications_list)} notifications")
    results = []
    try:
        for notification in notifications_list:
            result = await send_notification(notification)
            results.append(result)
        logger.info(f"Successfully processed {len(results)} notifications")
        return results
    except Exception as e:
        logger.error(f"Error processing bulk notifications: {str(e)}")
        raise
