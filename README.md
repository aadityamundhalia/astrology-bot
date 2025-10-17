# Rudie - Vedic Astrology Telegram Bot 🌿✨

A friendly, AI-powered Telegram bot that provides personalized Vedic astrology predictions with a warm, conversational personality.

## Features

### 🔮 Astrology Predictions
- 🌙 Daily, weekly, monthly, quarterly, and yearly predictions
- 💕 Love, career, wealth, and health forecasts
- 🎯 Event-specific predictions (job offers, proposals, etc.)
- 📊 Comprehensive horoscope readings

### 🤖 AI-Powered Interface
- **Rudie**: A 22-year-old Australian astrologer personality
- Natural, conversational responses
- Direct YES/NO/WAIT answers for decisions
- Thinking mode for deeper reasoning (configurable)
- Multi-tool function calling for accurate predictions

### 🎨 User Experience
- 📝 Step-by-step wizard for birth details
- 🔄 Easy detail updates via `/change` command
- ⚡ Priority queue system for VIP users
- 🚦 User activation/deactivation system
- 💬 Chat history with Redis caching
- 🧠 Mem0-powered memory for context retention

### ⚙️ System Features
- 🐰 RabbitMQ message queue (prevents GPU overload)
- 👷 Configurable worker count for scalability
- 🎯 Priority-based request processing
- 🔐 User status management (active/inactive)
- 📈 Ready for monetization with priority tiers

## Tech Stack

- **Framework**: FastAPI (with lifespan management)
- **AI/LLM**: Semantic Kernel + Ollama (`gpt-oss:latest`)
- **Database**: PostgreSQL (with Alembic migrations)
- **Cache**: Redis (chat history, temporary data)
- **Queue**: RabbitMQ (request queuing with priorities)
- **Bot**: python-telegram-bot (async)
- **Memory**: Mem0 (conversation memory service)
- **Embeddings**: Qdrant (vector database for Mem0)

## Architecture
```
Telegram Users
      ↓
  Telegram Bot (FastAPI)
      ↓
  Message Handler → Validates User Status & Priority
      ↓
  RabbitMQ Queue (Priority-based)
      ↓
  Worker Pool (1-N configurable workers)
      ↓
  Rudie Agent (AI + Semantic Kernel)
      ↓
  Astrology Tools → External Astrology API
      ↓
  Response → User
```

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL (database)
- Redis (caching)
- RabbitMQ (message queue)
- Qdrant (vector database for Mem0)
- Ollama with models:
  - `gpt-oss:latest` (main reasoning model)
  - `nomic-embed-text` (embeddings for Mem0)
- Telegram Bot Token (from @BotFather)
- Mem0 Service (running separately)
- Astrology API Service (running separately)

### Installation

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd astrology-bot
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

Key environment variables:
```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# Database
POSTGRES_HOST=192.168.0.200
POSTGRES_PORT=5432
POSTGRES_DB=astrology
POSTGRES_USER=default
POSTGRES_PASSWORD=your_password

# Redis
REDIS_HOST=192.168.0.200
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_HOST=192.168.0.200
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_QUEUE=astrology_requests
RABBITMQ_WORKERS=1  # Number of concurrent workers

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gpt-oss:latest
ENABLE_THINKING=true
THINKING_MAX_TOKENS=500
THINKING_TEMPERATURE=0.75

# External Services
MEM0_SERVICE_URL=http://192.168.0.200:8085
ASTROLOGY_API_URL=http://192.168.0.200:8087
```

5. **Setup database:**
```bash
# Create database
psql -h your_host -U your_user -c "CREATE DATABASE astrology;"

# Run migrations
alembic upgrade head
```

6. **Pull Ollama models:**
```bash
ollama pull gpt-oss:latest
ollama pull nomic-embed-text
```

7. **Run tests:**
```bash
# Test all connections
python tests/test_connections.py

# Test RabbitMQ specifically
python tests/test_rabbitmq.py

# Test Mem0
python tests/test_mem0_connection.py
```

8. **Start the bot:**
```bash
# Development
python main.py

# Production (Docker)
docker-compose up -d
```

## Docker Deployment
```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f astrology-bot

# Stop
docker-compose down
```

## Project Structure
```
astrology-bot/
├── app/
│   ├── agents/              # AI agents
│   │   ├── rudie_agent.py       # Main astrology agent
│   │   └── extraction_agent.py  # Birth data extraction
│   ├── handlers/            # Telegram command handlers
│   │   ├── command_handlers.py  # /start, /help, /info, /clear
│   │   ├── conversation_handlers.py  # Birth details wizard
│   │   └── message_handler.py   # Main message processing
│   ├── services/            # External services
│   │   ├── telegram_service.py  # Telegram bot interface
│   │   ├── memory_service.py    # Mem0 integration
│   │   ├── astrology_service.py # Astrology API client
│   │   └── queue_service.py     # RabbitMQ queue management
│   ├── workers/             # Background workers
│   │   └── astrology_worker.py  # Queue message processor
│   ├── tools/               # Semantic Kernel tools
│   │   └── astrology_tools.py   # Function calling tools
│   ├── utils/               # Utilities
│   │   └── validators.py        # Data validation
│   ├── models.py            # SQLAlchemy models
│   └── database.py          # Database configuration
├── tests/                   # Test suite
│   ├── test_connections.py      # Connection tests
│   ├── test_rabbitmq.py         # RabbitMQ tests
│   └── test_mem0_connection.py  # Mem0 tests
├── scripts/                 # Admin scripts
│   ├── manage_user.py           # User management CLI
│   ├── purge_queue.py           # Queue purging
│   └── purge_queue_http.py      # HTTP-based queue purge
├── alembic/                 # Database migrations
├── config.py                # Configuration management
├── main.py                  # Application entry point
├── docker-compose.yml       # Docker configuration
├── Dockerfile              # Container definition
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── README.md               # This file
```

## Usage

### User Commands

Talk to your bot on Telegram:

**Setup** (first time):
- `/start` - Welcome and setup instructions
- `/change` - Interactive wizard for birth details
- Send details all at once:
```
  Date of Birth: 1990-01-15
  Time of Birth: 10:30
  Place of Birth: New Delhi, India
```

**Get Predictions:**
- "How is today for me?"
- "What's my week looking like?"
- "Tell me about my love life this month"
- "Should I take this job offer?"
- "Good time to ask someone out?"
- "Career predictions for this year"

**Other Commands:**
- `/info` - View your birth details
- `/help` - Usage instructions
- `/clear` - Clear chat history and memory
- `/cancel` - Cancel current operation

### Admin Commands

Manage users via CLI:
```bash
# List all users
python scripts/manage_user.py list

# Get user details
python scripts/manage_user.py get 123456789

# Activate/Deactivate users
python scripts/manage_user.py activate 123456789
python scripts/manage_user.py deactivate 123456789

# Set user priority (1=VIP, 10=lowest)
python scripts/manage_user.py priority 123456789 1

# Purge RabbitMQ queue
python scripts/purge_queue.py
# or
python scripts/purge_queue_http.py
```

### Scaling Workers

Adjust concurrent workers in `.env`:
```bash
RABBITMQ_WORKERS=3  # Process 3 requests simultaneously
```

**Note**: More workers = more GPU memory usage. Start with 1 worker per GPU.

## User Priority System

Users have priority levels (1-10):
- **Priority 1-2**: VIP users (⚡ fastest response)
- **Priority 3-5**: Standard users (default: 5)
- **Priority 6-10**: Low priority users

Messages are processed in priority order. Within the same priority, FIFO (first-in-first-out) applies.

## API Endpoints

### Health Check
- `GET /health` - Service health status
- `GET /queue/status` - Queue status

### Astrology API (External Service)
Used internally by the bot:
- `/predictions/today` - Today's forecast
- `/predictions/week` - 7-day forecast
- `/predictions/current-month` - Current month
- `/predictions/quarterly` - 3-month forecast
- `/predictions/yearly` - 12-month forecast
- `/predictions/love` - Love predictions
- `/predictions/career` - Career predictions
- `/predictions/wealth` - Wealth predictions
- `/predictions/health` - Health predictions
- `/predictions/wildcard` - Specific event predictions
- `/horoscope/daily` - Daily horoscope
- `/horoscope/weekly` - Weekly horoscope
- `/horoscope/monthly` - Monthly horoscope

## Configuration

### Thinking Mode

Enable/disable AI reasoning:
```bash
ENABLE_THINKING=true           # Enable thinking for better responses
THINKING_MAX_TOKENS=500        # Allow more tokens for reasoning
THINKING_TEMPERATURE=0.75      # Control creativity
```

### Worker Configuration

Adjust based on hardware:
```bash
RABBITMQ_WORKERS=1  # Single GPU: 1 worker
RABBITMQ_WORKERS=2  # Dual GPU: 2 workers
RABBITMQ_WORKERS=4  # High-end server: 4+ workers
```

### Chat History

Control Redis cache:
```bash
REDIS_CHAT_HISTORY_LIMIT=5  # Keep last 5 conversation pairs
```

## Monitoring

### Logs
```bash
# Docker logs
docker-compose logs -f astrology-bot

# Application logs (if running directly)
# Logs appear in terminal with timestamps
```

### Queue Status
```bash
# Check queue via HTTP
curl http://localhost:8282/queue/status

# Check via RabbitMQ Management
http://192.168.0.200:15672
# Login: guest/guest
```

## Troubleshooting

### Bot not responding
1. Check if bot is running: `docker-compose ps`
2. Check logs: `docker-compose logs -f astrology-bot`
3. Verify RabbitMQ: `python tests/test_rabbitmq.py`
4. Purge old messages: `python scripts/purge_queue.py`

### Ollama errors
1. Verify models: `ollama list`
2. Pull if missing: `ollama pull gpt-oss:latest`
3. Check Ollama: `curl http://localhost:11434/api/tags`

### Database issues
1. Check connection: `python tests/test_connections.py`
2. Run migrations: `alembic upgrade head`
3. Check current version: `alembic current`

### Memory (Mem0) issues
1. Test connection: `python tests/test_mem0_connection.py`
2. Check Mem0 health: `curl http://192.168.0.200:8085/health`

## Performance Tips

1. **Single GPU**: Set `RABBITMQ_WORKERS=1`
2. **Multiple GPUs**: Set `RABBITMQ_WORKERS=<num_gpus>`
3. **Disable thinking for speed**: `ENABLE_THINKING=false`
4. **Reduce token limit**: `THINKING_MAX_TOKENS=300`
5. **Use SSD for PostgreSQL and Redis**

## Monetization Ready

The bot includes priority system for paid tiers:
- Free users: Priority 5 (default)
- Basic plan: Priority 3-4
- Premium plan: Priority 1-2

Implement payment gateway and update user priority upon payment.

## License

MIT License - See LICENSE file for details

## Contributing

Pull requests are welcome! For major changes:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Support

- 📧 Email: your-email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 📖 Docs: [Wiki](https://github.com/your-repo/wiki)

## Acknowledgments

- Semantic Kernel by Microsoft
- Ollama for local LLM inference
- python-telegram-bot community
- Mem0 for memory management

---

Made with ❤️ and ✨ cosmic energy