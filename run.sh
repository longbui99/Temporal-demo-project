# Terminal 1 - Order Service
uvicorn order.order:app --port 8000

# Terminal 2 - Shipment Service
uvicorn shipment.shipment:app --port 8001

# Terminal 3 - Notification Service
uvicorn notification.notification:app --port 8002

# Terminal 4 - Temporal Worker
python temporal/worker.py

# Terminal 5 - Start workflow
uvicorn temporal.starter:app --port 8003