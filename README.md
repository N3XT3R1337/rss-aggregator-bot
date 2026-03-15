```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ██████╗ ███████╗███████╗     █████╗  ██████╗  ██████╗          ║
║   ██╔══██╗██╔════╝██╔════╝    ██╔══██╗██╔════╝ ██╔════╝          ║
║   ██████╔╝███████╗███████╗    ███████║██║  ███╗██║  ███╗          ║
║   ██╔══██╗╚════██║╚════██║    ██╔══██║██║   ██║██║   ██║          ║
║   ██║  ██║███████║███████║    ██║  ██║╚██████╔╝╚██████╔╝          ║
║   ╚═╝  ╚═╝╚══════╝╚══════╝    ╚═╝  ╚═╝ ╚═════╝  ╚═════╝          ║
║                                                                  ║
║          RSS Aggregator Bot for Telegram                         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

![Build](https://img.shields.io/github/actions/workflow/status/N3XT3R1337/rss-aggregator-bot/ci.yml?branch=main&style=flat-square)
![License](https://img.shields.io/github/license/N3XT3R1337/rss-aggregator-bot?style=flat-square)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=flat-square&logo=telegram&logoColor=white)

---

A powerful Telegram bot that aggregates RSS feeds, filters entries by keywords, groups channels, supports OPML import/export, and delivers daily digests — all on your schedule.

## Features

- **RSS Feed Management** — Add, remove, toggle, and list RSS/Atom feeds
- **Keyword Filtering** — Include or exclude entries based on keywords
- **Channel Grouping** — Organize feeds into named groups for better management
- **OPML Import/Export** — Migrate feeds from/to any RSS reader
- **Digest Mode** — Receive a single daily summary instead of real-time updates
- **Scheduled Checks** — APScheduler-powered background feed polling
- **Persistent Storage** — SQLAlchemy + SQLite with full async support
- **Duplicate Detection** — SHA-256 hashing ensures you never see the same entry twice

## Tech Stack

| Component | Technology |
|-----------|------------|
| Bot Framework | [aiogram 3.x](https://docs.aiogram.dev/) |
| Feed Parsing | [feedparser](https://feedparser.readthedocs.io/) |
| Scheduling | [APScheduler](https://apscheduler.readthedocs.io/) |
| ORM | [SQLAlchemy 2.0](https://docs.sqlalchemy.org/) (async) |
| Database | SQLite via [aiosqlite](https://aiosqlite.omnilib.dev/) |
| Config | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |

## Installation

### Prerequisites

- Python 3.10 or higher
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Setup

```bash
git clone https://github.com/N3XT3R1337/rss-aggregator-bot.git
cd rss-aggregator-bot

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
```

Edit `.env` and set your bot token:

```env
RSS_BOT_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
RSS_BOT_DATABASE_URL=sqlite+aiosqlite:///rss_bot.db
RSS_BOT_CHECK_INTERVAL_MINUTES=30
RSS_BOT_DIGEST_HOUR=9
RSS_BOT_LOG_LEVEL=INFO
```

### Run

```bash
python -m bot.main
```

## Usage

### Feed Management

```
/add https://blog.python.org/feeds/posts/default    Add a feed
/list                                                 List all feeds
/remove 3                                             Remove feed by ID
/toggle 3                                             Pause/resume a feed
/check                                                Manually check all feeds
```

### Keyword Filtering

```
/addkw python          Include entries mentioning "python"
/addkw -advertisement  Exclude entries mentioning "advertisement"
/keywords              List all active keywords
/rmkw python           Remove a keyword
/clearkw               Clear all keywords
```

### Channel Groups

```
/newgroup Tech              Create a group called "Tech"
/groups                     List all groups
/addtogroup 1 3             Add feed #3 to group #1
/rmfromgroup 1 3            Remove feed #3 from group #1
/delgroup 1                 Delete group #1
```

### Digest Mode

```
/digest                     Toggle digest mode on/off
/digesttime 14 30           Set digest delivery to 14:30 UTC
/digeststatus               View current digest settings
```

### OPML Import/Export

```
/export                     Download your feeds as OPML
/import                     Upload an OPML file to import feeds
```

## Running Tests

```bash
pip install pytest pytest-asyncio aiosqlite
pytest -v
```

## Project Structure

```
rss-aggregator-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              Entry point and bot setup
│   ├── config.py             Settings via pydantic-settings
│   ├── models.py             SQLAlchemy ORM models
│   ├── database.py           Async engine and session factory
│   ├── middlewares.py        Database session middleware
│   ├── handlers/
│   │   ├── feeds.py          Feed CRUD commands
│   │   ├── groups.py         Group management commands
│   │   ├── keywords.py       Keyword filter commands
│   │   ├── opml.py           OPML import/export handlers
│   │   └── digest.py         Digest mode commands
│   └── services/
│       ├── feed_service.py   Feed fetching and filtering logic
│       ├── scheduler_service.py  APScheduler job management
│       ├── opml_service.py   OPML generation and parsing
│       └── digest_service.py Digest building and formatting
├── tests/
│   ├── conftest.py           Shared fixtures
│   ├── test_models.py        ORM model tests
│   ├── test_feed_service.py  Feed service unit tests
│   ├── test_opml_service.py  OPML roundtrip tests
│   └── test_digest_service.py Digest formatting tests
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── pyproject.toml
```

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/N3XT3R1337">panaceya</a>
</p>
