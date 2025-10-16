# Rudie - Vedic Astrology Telegram Bot 🌿

A friendly Telegram bot that provides personalized Vedic astrology predictions using AI.

## Features

- 🌙 Daily, weekly, monthly, and yearly predictions
- 💕 Love, career, wealth, and health forecasts
- 🤖 AI-powered conversational interface (Rudie personality)
- 🧠 Memory system to remember user context
- 📊 Multiple prediction endpoints
- 🔄 Real-time Telegram integration

## Tech Stack

- **Framework**: FastAPI
- **AI**: Semantic Kernel + Ollama (local LLM)
- **Database**: PostgreSQL
- **Cache**: Redis
- **Bot**: python-telegram-bot
- **Memory**: Mem0
- **Migrations**: Alembic

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- Ollama with `gpt-oss:latest` model
- Telegram Bot Token

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd astrology-bot
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. Setup database:
```bash
# Create database
psql -h your_host -U your_user -c "CREATE DATABASE astrology;"

# Run migrations
alembic upgrade head
```

6. Run tests:
```bash
python tests/test_connections.py
```

7. Start the bot:
```bash
python main.py
```

## Project Structure
```
astrology-bot/
├── app/
│   ├── agents/              # AI agents (Rudie, Extraction)
│   ├── services/            # External services (Telegram, Memory, Astrology)
│   ├── tools/               # Astrology tools for Semantic Kernel
│   ├── models.py            # Database models
│   └── database.py          # Database configuration
├── tests/                   # Test suite
├── alembic/                 # Database migrations
├── config.py                # Configuration management
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
└── .env.example            # Environment variables template
```

## Usage

Send a message to your Telegram bot:

- "How is today for me?"
- "What's my weekly horoscope?"
- "Tell me about my love life this month"
- "Career predictions for this year"

First-time users will be asked to provide:
- Date of Birth (YYYY-MM-DD)
- Time of Birth (HH:MM)
- Place of Birth (City, Region)

## API Endpoints

The bot uses these internal endpoints:
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

## License

MIT

## Contributing

Pull requests are welcome! For major changes, please open an issue first.
