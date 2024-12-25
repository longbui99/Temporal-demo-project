from fastapi import FastAPI, HTTPException
from temporalio.client import Client
from temporal.workflows import OrderFulfillmentWorkflow, OrderDetails
from pydantic import BaseModel
import asyncio
import uuid

app = FastAPI()

# Pydantic model for the API request
class OrderRequest(BaseModel):
    customer_id: int
    product_id: int
    quantity: int
    total_amount: float
    shipping_address: str
    carrier: str

# Initialize Temporal client
temporal_client = None

@app.on_event("startup")
async def startup_event():
    global temporal_client
    temporal_client = await Client.connect("localhost:7233")

@app.post("/api/orders/fulfill")
async def start_order_fulfillment(order_request: OrderRequest):
    try:
        # Create OrderDetails from request
        order_details = OrderDetails(
            customer_id=order_request.customer_id,
            product_id=order_request.product_id,
            quantity=order_request.quantity,
            total_amount=order_request.total_amount
        )
        
        # Generate unique workflow ID
        workflow_id = f"order-workflow-{uuid.uuid4()}"
        
        # Start the workflow with args matching the workflow.run method
        handle = await temporal_client.start_workflow(
            OrderFulfillmentWorkflow.run,
            args=[
                order_details,
                order_request.shipping_address,
                order_request.carrier
            ],
            id=workflow_id,
            task_queue="order-fulfillment-queue"
        )
        
        # Wait for the result
        result = await handle.result()
        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}")