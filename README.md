# claudefolio

Your AI-powered personal wealth advisor. Automated portfolio monitoring, market analysis, and investment briefings delivered via Telegram. Runs on Claude Code with your existing Max/Pro subscription — no API costs.

Built on Claude Code CLI, it combines real-time market data, macroeconomic analysis, and persistent memory to provide contextualized investment insights — not generic stock tips.

## What It Does

Twice a week (configurable), claudefolio collects market data for your entire portfolio, pulls macroeconomic indicators, searches for relevant news, and feeds everything into Claude with a specialized financial analyst system prompt. The result is a comprehensive briefing delivered straight to your Telegram -- like having a CFA on retainer.

## Features

- **Bi-weekly Portfolio Briefings** -- Scheduled market analysis with portfolio-specific insights, delivered via Telegram
- **Monthly Reports** -- Performance review, top/bottom performers, lessons learned
- **On-Demand Ticker Analysis** -- Send any ticker to the Telegram bot for a deep-dive analysis
- **Free-Form Chat** -- Ask your advisor anything about your portfolio via Telegram
- **Trade Tracking** -- Tell the bot about buys/sells in natural language, it updates your portfolio automatically
- **Watchlist Management** -- Track tickers you're interested in
- **Persistent Memory** -- Remembers past briefings, tracks recommendation outcomes, avoids repetition
- **Tax-Loss Harvesting** -- Identifies tax optimization opportunities (configurable tax regime)
- **Benchmark Comparison** -- Compares your portfolio against S&P 500, NASDAQ, DAX, Gold, BTC
- **Earnings Calendar** -- Alerts you to upcoming earnings for your positions
- **Multi-Account Support** -- Track positions across multiple brokers
- **EUR/USD Conversion** -- Correct P&L calculation for mixed-currency portfolios

## Example Briefing (Anonymized)

```
MARKTLAGE

Relief-Rally (NASDAQ +4.4%, VIX -22%) aendert nichts am Extreme-Fear-Regime.
Yield Curve normal (+52bps), aber Credit Spreads weiten sich. EUR/USD bei 1.15
frisst USD-Gewinne systematisch auf.

PORTFOLIO-CHECK

ASML: Staerkster Gewinner (+63% total), aber underperformed am Rally-Tag
(-2.2% vs DAX +3.9%). Nervositaet vor Earnings am 15.4 -- Stop-Loss bei
1050 EUR empfohlen.

Gold ETC: -1.8% in EUR trotz +3.4% Goldpreis in USD. Das ist der EUR/USD-
Effekt in Reinform.

EMPFEHLUNGEN

Keine neuen Trades. 14 von 17 Positionen reporten in den naechsten 6 Wochen.
Cash-Quote von 31% ist im Extreme-Fear-Umfeld eine Staerke, nicht Schwaeche.
Abwarten.

RISIKEN AUF DEM RADAR

- Geopolitik (Hormuz/Iran) bleibt Tail-Risk
- Earnings-Saison kann Volatilitaet verstaerken
- EUR-Staerke als systematischer Headwind auf USD-Exposure
```

## Architecture

```
claudefolio/
├── config/
│   ├── settings.json          # API keys & schedule (git-ignored)
│   ├── portfolio.json         # Your portfolio positions (git-ignored)
│   └── watchlist.json         # Tickers you're watching
├── src/
│   ├── main.py                # Orchestrator (briefing/monthly/analyze/bot modes)
│   ├── data/
│   │   ├── market.py          # Stock prices & fundamentals (yfinance)
│   │   ├── macro.py           # Macro data (FRED API, ECB, Fear & Greed)
│   │   ├── news.py            # News search (Brave Search API)
│   │   └── calendar.py        # Earnings calendar (yfinance)
│   ├── analysis/
│   │   ├── claude.py          # Claude Code CLI wrapper
│   │   ├── prompt.py          # System prompt & data formatting
│   │   ├── memory.py          # Persistent memory system
│   │   ├── performance.py     # Benchmarks, tax-loss harvesting, rec tracking
│   │   └── chat_history.py    # Telegram conversation history
│   └── delivery/
│       └── telegram.py        # Telegram bot & message delivery
├── memory/                    # Persistent state (git-ignored)
│   ├── briefings.json         # Past briefing summaries
│   ├── recommendations.json   # Open/closed recommendations
│   ├── notes.json             # Market regime, position theses, insights
│   └── chat_history.json      # Recent Telegram conversations
├── scripts/
│   ├── deploy.sh              # Deploy to remote server
│   └── setup_rockpi.sh        # Server setup (RockPi/Raspberry Pi)
├── setup.sh                   # Local setup script
└── requirements.txt           # Python dependencies
```

### Data Flow

```
[Cron / Telegram Command]
        │
        ▼
    main.py (orchestrator)
        │
        ├── data/market.py     → yfinance (prices, fundamentals, insiders)
        ├── data/macro.py      → FRED API (US), ECB API (EU), CNN Fear & Greed
        ├── data/news.py       → Brave Search API
        └── data/calendar.py   → yfinance (earnings dates)
        │
        ▼
    analysis/prompt.py         → Builds structured prompt with all data
        │
        ▼
    analysis/claude.py         → Claude Code CLI (--print mode, Opus model)
        │
        ▼
    analysis/memory.py         → Saves summary, recommendations, theses
        │
        ▼
    delivery/telegram.py       → Sends formatted briefing to Telegram
```

### How Claude Is Used

This project does **not** use the Claude API directly. Instead, it shells out to the [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) in `--print` mode. This means:

- No API key management for Claude -- it uses your Claude Max/Pro subscription
- Access to the latest models (Opus) with high effort mode
- The CLI handles authentication, rate limiting, and token management
- Prompts are passed via stdin, so there is no length limitation from command-line arguments

## Prerequisites

- **Python 3.11+**
- **Claude Code CLI** -- requires a Claude Max or Pro subscription
  - Install: `npm install -g @anthropic-ai/claude-code`
  - Authenticate: `claude auth`
- **Telegram Bot** -- create one via [@BotFather](https://t.me/BotFather)
- **Brave Search API key** -- free tier available at [brave.com/search/api](https://brave.com/search/api/)
- **FRED API key** -- free at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html)

## Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/claudefolio.git
cd claudefolio

# Run the interactive setup wizard
python3 setup.py

# This will guide you through:
#   → Language selection
#   → Country & tax regime
#   → Telegram bot setup
#   → API keys (Brave Search, FRED)
#   → Briefing schedule
#   → Portfolio configuration
#   → Dependency installation

# Activate the virtual environment
source venv/bin/activate

# Run your first briefing
python -m src.main briefing

# Or start the Telegram bot
python -m src.main bot
```

## Configuration

### settings.json

| Key | Description |
|-----|-------------|
| `telegram.bot_token` | Telegram bot token from @BotFather |
| `telegram.chat_id` | Your Telegram chat ID (see below) |
| `brave_search.api_key` | Brave Search API key for news |
| `fred.api_key` | FRED API key for US macro data |
| `schedule.briefing_days` | Days for automated briefings (e.g., `["monday", "thursday"]`) |
| `schedule.briefing_time` | Time for briefings (e.g., `"07:00"`) |
| `data.primary_source` | Price data source (`yfinance`) |

**Getting your Telegram Chat ID:**
1. Create a bot via [@BotFather](https://t.me/BotFather) and copy the token
2. Send `/start` to your new bot
3. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Find your `chat.id` in the response

### portfolio.json

The portfolio file supports multiple broker accounts, each with a list of positions:

```json
{
  "accounts": {
    "my_broker": {
      "positions": [
        {
          "name": "Apple",
          "isin": "US0378331005",
          "ticker": "AAPL",
          "shares": 10.0,
          "buy_in": 178.50,
          "currency": "USD"
        }
      ]
    }
  },
  "bank_accounts": {
    "savings": {
      "bank": "My Bank",
      "value": 10000.00,
      "interest": 2.5,
      "note": "Emergency fund",
      "is_depot_cash": false
    }
  },
  "user_profile": {
    "age": 25,
    "country": "DE",
    "tax_regime": "Abgeltungssteuer 26.375%",
    "risk_tolerance": "moderate",
    "goal": "growth",
    "time_horizon": "long_term"
  }
}
```

The `user_profile` section shapes Claude's advice -- risk tolerance, tax regime, and time horizon all influence recommendations.

### watchlist.json

```json
{
  "watchlist": [
    {"ticker": "RKLB", "name": "Rocket Lab"}
  ],
  "last_updated": "2026-01-01"
}
```

Watchlist tickers are included in data collection but not in portfolio P&L calculations.

## Telegram Bot Commands

| Command / Input | Action |
|----------------|--------|
| `/status` | Show current portfolio overview |
| `/briefing` | Trigger an on-demand briefing |
| `/help` | Show help message |
| `AAPL` | Analyze a ticker (any 1-5 letter uppercase word) |
| `watch RKLB` | Add ticker to watchlist |
| `unwatch RKLB` | Remove ticker from watchlist |
| `Bought 10 AAPL @ 180` | Record a buy (asks for confirmation) |
| `Sold 5 TSLA @ 250` | Record a sell (asks for confirmation) |
| *Any other text* | Free-form chat with your AI advisor |

Trade messages are parsed flexibly -- `"Hab 10 AAPL bei 180 gekauft"` works just as well as `"Bought 10 AAPL @ 180"`.

## Running Modes

```bash
# Bi-weekly briefing (meant for cron)
python -m src.main briefing

# Monthly report (meant for cron, 1st of each month)
python -m src.main monthly

# On-demand ticker analysis
python -m src.main analyze --ticker AAPL

# Interactive Telegram bot (long-running)
python -m src.main bot
```

## Deployment (Raspberry Pi / RockPi / Any Linux Server)

The system is designed to run on a low-power always-on device.

### Automated Setup

```bash
# On your local machine: deploy to your server
cd scripts
./deploy.sh
```

The deploy script copies files via SCP and runs `setup_rockpi.sh` on the remote, which:
- Installs Python, Node.js, and Claude Code CLI
- Creates a virtual environment and installs dependencies
- Sets up cron jobs for scheduled briefings
- Creates a systemd service for the Telegram bot

### Manual Setup

```bash
# On the server
sudo apt update && sudo apt install -y python3-pip python3-venv nodejs npm
npm install -g @anthropic-ai/claude-code
claude auth   # Authenticate with your Anthropic account

cd /home/your_user/claudefolio
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Cron Jobs

```cron
# Briefing on Monday and Thursday at 07:00
0 7 * * 1,4 cd /home/your_user/claudefolio && ./venv/bin/python -m src.main briefing >> logs/briefing.log 2>&1

# Monthly report on the 1st at 09:00
0 9 1 * * cd /home/your_user/claudefolio && ./venv/bin/python -m src.main monthly >> logs/monthly.log 2>&1
```

### Telegram Bot as systemd Service

```ini
[Unit]
Description=claudefolio Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/home/your_user/claudefolio
ExecStart=/home/your_user/claudefolio/venv/bin/python -m src.main bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable claude-money-bot
sudo systemctl start claude-money-bot
```

## Memory System

claudefolio maintains a persistent memory to avoid repetition and track recommendation outcomes:

- **Briefing History** -- Last 20 briefing summaries, so Claude knows what was already discussed
- **Recommendations** -- Open recommendations are tracked with entry price, target, and stop-loss. Outcomes (target hit / stop triggered) are updated automatically based on market data
- **Position Theses** -- Claude's investment thesis for each position, updated when the situation changes
- **Market Regime** -- Current market assessment (e.g., "Extreme Fear with technical bounce")
- **Key Insights** -- Accumulated insights that persist across sessions

## API Rate Limits & Costs

- **yfinance** -- Free, no API key needed. May rate-limit on heavy use
- **Brave Search** -- Free tier: 2,000 queries/month (sufficient for 2 briefings/week)
- **FRED** -- Free, generous limits
- **ECB Data API** -- Free, no key needed
- **Claude Code CLI** -- Included in your Claude Max ($100/mo) or Pro ($20/mo) subscription

## Disclaimer

This software is for **educational and informational purposes only**. It does not constitute financial advice, investment advice, trading advice, or any other kind of advice.

- The AI-generated analysis may contain errors, hallucinations, or outdated information
- Past performance of recommendations does not guarantee future results
- Always do your own research before making investment decisions
- The authors accept no liability for any financial losses incurred through use of this software

## License

MIT
