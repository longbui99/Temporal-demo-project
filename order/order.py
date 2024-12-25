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

class OrderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Order(BaseModel):
    id: Optional[int] = None
    customer_id: int
    product_id: int
    quantity: int
    total_amount: float
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = datetime.now()

app = FastAPI()

# In-memory storage for orders
orders = {}
order_id_counter = 1

@app.post("/orders/", response_model=Order)
async def create_order(order: Order):
    logger.info(f"Received order creation request for customer {order.customer_id}")
    global order_id_counter
    
    try:
        # Assign order ID
        order.id = order_id_counter
        order_id_counter += 1
        
        logger.info(f"Storing order with ID: {order.id}")
        orders[order.id] = order
        
        logger.info(f"Successfully created order {order.id}")
        return order
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise

@app.put("/orders/{order_id}/cancel", response_model=Order)
async def cancel_order(order_id: int):
    logger.info(f"Received cancellation request for order {order_id}")
    
    try:
        if order_id not in orders:
            logger.error(f"Order not found: {order_id}")
            raise HTTPException(status_code=404, detail="Order not found")
        
        order = orders[order_id]
        if order.status == OrderStatus.COMPLETED:
            logger.error(f"Cannot cancel completed order {order_id}")
            raise HTTPException(status_code=400, detail="Cannot cancel completed order")
        
        order.status = OrderStatus.CANCELLED
        logger.info(f"Successfully cancelled order {order_id}")
        return order
    except Exception as e:
        logger.error(f"Error cancelling order: {str(e)}")
        raise
