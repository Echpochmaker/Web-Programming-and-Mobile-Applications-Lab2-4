import asyncio 
from app.core.queue import QueueService 
asyncio.run(QueueService.connect()) 
print("OK") 
