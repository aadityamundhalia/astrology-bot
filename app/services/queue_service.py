"""RabbitMQ Queue Service for processing astrology requests"""
import logging
import json
import asyncio
from aio_pika import connect_robust, Message, DeliveryMode
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class QueueService:
    def __init__(self):
        self.connection: AbstractConnection = None
        self.channel: AbstractChannel = None
        self.queue: AbstractQueue = None
        self.is_processing = False
    
    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            logger.info(f"🐰 Connecting to RabbitMQ at {settings.rabbitmq_host}:{settings.rabbitmq_port}...")
            self.connection = await connect_robust(settings.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Set prefetch count to 1 to process one message at a time
            await self.channel.set_qos(prefetch_count=1)
            
            # Declare queue
            self.queue = await self.channel.declare_queue(
                settings.rabbitmq_queue,
                durable=True  # Queue survives broker restart
            )
            
            logger.info(f"✅ Connected to RabbitMQ - Queue: {settings.rabbitmq_queue}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                logger.info("🐰 Disconnected from RabbitMQ")
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")
    
    async def publish_request(self, request_data: dict) -> str:
        """Publish a request to the queue"""
        try:
            message_body = json.dumps(request_data).encode()
            
            message = Message(
                message_body,
                delivery_mode=DeliveryMode.PERSISTENT,  # Message survives broker restart
                content_type="application/json"
            )
            
            await self.channel.default_exchange.publish(
                message,
                routing_key=settings.rabbitmq_queue
            )
            
            request_id = request_data.get('request_id', 'unknown')
            logger.info(f"📤 Published request {request_id} to queue")
            
            return request_id
            
        except Exception as e:
            logger.error(f"Error publishing request: {e}")
            raise
    
    async def start_consumer(self, handler):
        """Start consuming messages from the queue"""
        try:
            logger.info(f"🐰 Starting consumer for queue: {settings.rabbitmq_queue}")
            self.is_processing = True
            
            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            request_data = json.loads(message.body.decode())
                            request_id = request_data.get('request_id', 'unknown')
                            
                            logger.info(f"📥 Processing request {request_id} from queue")
                            
                            # Call the handler to process the request
                            await handler(request_data)
                            
                            logger.info(f"✅ Completed request {request_id}")
                            
                        except Exception as e:
                            logger.error(f"❌ Error processing message: {e}", exc_info=True)
                            # Message will be requeued if not acknowledged
                            
        except asyncio.CancelledError:
            logger.info("🛑 Consumer stopped")
            self.is_processing = False
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}", exc_info=True)
            self.is_processing = False
    
    async def get_queue_size(self) -> int:
        """
        Get approximate queue size
        Note: This is an estimate and may not be 100% accurate in all cases
        """
        try:
            # We can't easily get queue size with aio_pika without management API
            # Return 0 as placeholder - users won't see exact position
            # Alternative: Use RabbitMQ Management API (HTTP) for accurate count
            return 0
        except Exception as e:
            logger.error(f"Error getting queue size: {e}")
            return 0