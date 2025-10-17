import logging
logging.getLogger("httpx").setLevel(logging.WARNING)

from fastapi import FastAPI
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters
from contextlib import asynccontextmanager
import httpx
import asyncio

from config import get_settings
from app.services.telegram_service import TelegramService
from app.services.memory_service import MemoryService
from app.services.astrology_service import AstrologyService
from app.services.queue_service import QueueService
from app.agents.extraction_agent import ExtractionAgent
from app.agents.rudie_agent import RudieAgent
from app.workers.astrology_worker import AstrologyWorker

# Import handlers
from app.handlers.command_handlers import (
    handle_start_command,
    handle_help_command,
    handle_info_command,
    handle_clear_command
)
from app.handlers.conversation_handlers import (
    BIRTH_DATE, BIRTH_TIME, BIRTH_PLACE,
    start_birth_details_wizard,
    receive_birth_date,
    receive_birth_time,
    receive_birth_place,
    cancel_wizard
)
from app.handlers.message_handler import handle_message

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize services (global scope so they persist)
telegram_service = TelegramService()
memory_service = MemoryService(telegram_service=telegram_service)
astrology_service = AstrologyService()
queue_service = QueueService()
extraction_agent = ExtractionAgent()
rudie_agent = RudieAgent()

# Initialize worker
astrology_worker = AstrologyWorker(
    telegram_service=telegram_service,
    memory_service=memory_service,
    astrology_service=astrology_service,
    rudie_agent=rudie_agent
)

# Wrapper functions to inject services
async def _handle_start(update, context):
    return await handle_start_command(update, context, telegram_service)

async def _handle_help(update, context):
    return await handle_help_command(update, context, telegram_service)

async def _handle_info(update, context):
    return await handle_info_command(update, context, telegram_service)

async def _handle_clear(update, context):
    return await handle_clear_command(update, context, telegram_service)

async def _handle_message(update, context):
    return await handle_message(
        update, context, telegram_service, queue_service, extraction_agent
    )

async def _start_wizard(update, context):
    return await start_birth_details_wizard(update, context, telegram_service)

async def _receive_date(update, context):
    return await receive_birth_date(update, context, telegram_service)

async def _receive_time(update, context):
    return await receive_birth_time(update, context, telegram_service)

async def _receive_place(update, context):
    return await receive_birth_place(update, context, telegram_service)

async def _cancel_wizard(update, context):
    return await cancel_wizard(update, context, telegram_service)

# Create conversation handler
birth_details_conversation = ConversationHandler(
    entry_points=[
        CommandHandler("change", _start_wizard),
        CommandHandler("setup", _start_wizard),
    ],
    states={
        BIRTH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, _receive_date)],
        BIRTH_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, _receive_time)],
        BIRTH_PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, _receive_place)],
    },
    fallbacks=[CommandHandler("cancel", _cancel_wizard)],
    name="birth_details",
    persistent=False,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting astrology bot...")
    
    # Test Mem0 connection
    try:
        logger.info("🧠 Testing Mem0 connection...")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.mem0_service_url}/health")
            logger.info(f"🧠 Mem0 service responding: HTTP {response.status_code}")
            if response.status_code == 200:
                logger.info(f"✅ Mem0 service is healthy")
            else:
                logger.warning(f"⚠️  Mem0 service returned non-200 status")
    except Exception as e:
        logger.warning(f"🧠 Could not connect to Mem0 service: {e}")
        logger.warning("⚠️  Bot will continue but memory features may not work")
    
    # Connect to RabbitMQ
    try:
        await queue_service.connect()
    except Exception as e:
        logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
        raise
    
    # Start multiple consumers based on RABBITMQ_WORKERS
    consumer_tasks = []
    for worker_id in range(settings.rabbitmq_workers):
        logger.info(f"👷 Starting worker {worker_id + 1}/{settings.rabbitmq_workers}")
        task = asyncio.create_task(
            queue_service.start_consumer(astrology_worker.process_request),
            name=f"worker-{worker_id}"
        )
        consumer_tasks.append(task)
    
    logger.info(f"✅ Started {settings.rabbitmq_workers} worker(s)")
    
    # Start Telegram bot
    application = telegram_service.setup_application(
        message_handler=_handle_message,
        conversation_handler=birth_details_conversation,
        clear_handler=_handle_clear,
        start_handler=_handle_start,
        help_handler=_handle_help,
        info_handler=_handle_info
    )
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    logger.info("✅ Telegram bot started successfully")
    
    # Yield control to FastAPI (app is now running)
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down astrology bot...")
    
    # Stop all consumers
    for task in consumer_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    logger.info("✅ All workers stopped")
    
    # Disconnect from RabbitMQ
    await queue_service.disconnect()
    
    # Stop Telegram bot
    if telegram_service.application:
        await telegram_service.application.updater.stop()
        await telegram_service.application.stop()
        await telegram_service.application.shutdown()
    logger.info("✅ Telegram bot stopped")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Rudie Astrology Bot",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "bot": "rudie",
        "version": "1.0.0"
    }

@app.get("/queue/status")
async def queue_status():
    """Get queue status"""
    return {
        "is_processing": queue_service.is_processing,
        "queue_ready": queue_service.queue is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8282, reload=True)