import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflows import (
    OrderFulfillmentWorkflow,
    create_order_activity,
    create_shipment_activity,
    send_notification_activity,
    cancel_order_activity,
    cancel_shipment_activity
)

async def run_worker():
    client = await Client.connect("localhost:7233")
    
    worker = Worker(
        client,
        task_queue="order-fulfillment-queue",
        workflows=[OrderFulfillmentWorkflow],
        activities=[
            create_order_activity,
            create_shipment_activity,
            send_notification_activity,
            cancel_order_activity,
            cancel_shipment_activity
        ]
    )
    
    print("Worker started, waiting for tasks...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(run_worker()) 