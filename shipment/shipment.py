from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
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

class ShipmentStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Shipment(BaseModel):
    id: Optional[int] = None
    order_id: int
    tracking_number: str = "N/A"
    shipping_address: str
    carrier: str
    status: ShipmentStatus = ShipmentStatus.PENDING
    created_at: datetime = datetime.now()

app = FastAPI()

# In-memory storage for shipments
shipments = {}
shipment_id_counter = 1

@app.post("/shipments/", response_model=Shipment)
async def create_shipment(shipment: Shipment):
    logger.info(f"Received shipment creation request for order {shipment.order_id}")
    global shipment_id_counter
    
    try:
        if shipment.shipping_address == "":
            logger.error("Empty shipping address provided")
            raise HTTPException(status_code=400, detail="Shipping address is required")
            
        # Assign shipment ID
        shipment.id = shipment_id_counter
        shipment_id_counter += 1
        
        # Generate tracking number
        shipment.tracking_number = f"SHIP{shipment.id:06d}"
        logger.info(f"Generated tracking number: {shipment.tracking_number}")
        
        logger.info(f"Storing shipment with ID: {shipment.id}")
        shipments[shipment.id] = shipment
        
        logger.info(f"Successfully created shipment {shipment.id}")
        return shipment
    except Exception as e:
        logger.error(f"Error creating shipment: {str(e)}")
        raise

@app.put("/shipments/{shipment_id}/cancel", response_model=Shipment)
async def cancel_shipment(shipment_id: int):
    logger.info(f"Received cancellation request for shipment {shipment_id}")
    
    try:
        if shipment_id not in shipments:
            logger.error(f"Shipment not found: {shipment_id}")
            raise HTTPException(status_code=404, detail="Shipment not found")
        
        shipment = shipments[shipment_id]
        if shipment.status == ShipmentStatus.DELIVERED:
            logger.error(f"Cannot cancel delivered shipment {shipment_id}")
            raise HTTPException(status_code=400, detail="Cannot cancel delivered shipment")
        
        shipment.status = ShipmentStatus.CANCELLED
        logger.info(f"Successfully cancelled shipment {shipment_id}")
        return shipment
    except Exception as e:
        logger.error(f"Error cancelling shipment: {str(e)}")
        raise
