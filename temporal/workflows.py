from datetime import timedelta
from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError  # Add this import
from dataclasses import dataclass
from typing import Optional

# Data models for activities
@dataclass
class OrderDetails:
    customer_id: int
    product_id: int
    quantity: int
    total_amount: float

@dataclass
class ShipmentDetails:
    order_id: int
    shipping_address: str
    carrier: str

@dataclass
class NotificationDetails:
    recipient_id: int
    type: str
    subject: str
    content: str

# Activity definitions
@activity.defn
async def create_order_activity(order_details: OrderDetails) -> dict:
    # Move HTTP client creation and request to here
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/orders/",
            json={
                "customer_id": order_details.customer_id,
                "product_id": order_details.product_id,
                "quantity": order_details.quantity,
                "total_amount": order_details.total_amount
            }
        )
        response.raise_for_status()
        return response.json()

@activity.defn
async def create_shipment_activity(shipment_details: ShipmentDetails) -> dict:
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/shipments/",
            json={
                "order_id": shipment_details.order_id,
                "shipping_address": shipment_details.shipping_address,
                "carrier": shipment_details.carrier
            }
        )
        response.raise_for_status()
        return response.json()

@activity.defn
async def send_notification_activity(notification_details: NotificationDetails) -> dict:
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/notifications/",
            json={
                "recipient_id": notification_details.recipient_id,
                "type": notification_details.type,
                "subject": notification_details.subject,
                "content": notification_details.content
            }
        )
        response.raise_for_status()
        return response.json()

@activity.defn
async def cancel_order_activity(order_id: int) -> dict:
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"http://localhost:8000/orders/{order_id}/cancel"
        )
        response.raise_for_status()
        return response.json()

@activity.defn
async def cancel_shipment_activity(shipment_id: int) -> dict:
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"http://localhost:8001/shipments/{shipment_id}/cancel"
        )
        response.raise_for_status()
        return response.json()

# Workflow definition
@workflow.defn
class OrderFulfillmentWorkflow:
    @workflow.run
    async def run(self, 
                 order_details: OrderDetails, 
                 shipping_address: str,
                 carrier: str) -> dict:
        
        order_result = None
        shipment_result = None
        
        try:
            # Step 1: Create Order
            order_result = await workflow.execute_activity(
                create_order_activity,
                order_details,
                start_to_close_timeout=timedelta(seconds=5),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_attempts=1
                )
            )

            # Step 2: Create Shipment
            shipment_details = ShipmentDetails(
                order_id=order_result["id"],
                shipping_address=shipping_address,
                carrier=carrier
            )
            
            shipment_result = await workflow.execute_activity(
                create_shipment_activity,
                shipment_details,
                start_to_close_timeout=timedelta(seconds=5),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_attempts=3
                )
            )

            # Step 3: Send Notification
            notification_details = NotificationDetails(
                recipient_id=order_details.customer_id,
                type="email",
                subject="Order Confirmation",
                content=f"Your order has been confirmed and shipped. Tracking number: {shipment_result['tracking_number']}"
            )
            
            notification_result = await workflow.execute_activity(
                send_notification_activity,
                notification_details,
                start_to_close_timeout=timedelta(seconds=5),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_attempts=3
                )
            )

            return {
                "order": order_result,
                "shipment": shipment_result,
                "notification": notification_result
            }

        except Exception as e:
            # Compensating transactions
            if shipment_result:
                await workflow.execute_activity(
                    cancel_shipment_activity,
                    shipment_result["id"],
                    start_to_close_timeout=timedelta(seconds=5)
                )
            
            if order_result:
                await workflow.execute_activity(
                    cancel_order_activity,
                    order_result["id"],
                    start_to_close_timeout=timedelta(seconds=5)
                )

            # Send failure notification
            if order_result:
                failure_notification = NotificationDetails(
                    recipient_id=order_details.customer_id,
                    type="email",
                    subject="Order Processing Failed",
                    content="We're sorry, but there was an issue processing your order."
                )
                
                await workflow.execute_activity(
                    send_notification_activity,
                    failure_notification,
                    start_to_close_timeout=timedelta(seconds=5)
                )
            
            raise ApplicationError(f"Workflow failed: {str(e)}") 