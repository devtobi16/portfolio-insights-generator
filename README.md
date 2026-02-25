# portfolio-insights-generator

# Portfolio Insights Generator

Processes financial transaction data from a CSV, runs analytics on it, and uses OpenAI to generate insights about trading patterns.

## Setup

```bash
pip install -r requirements.txt
```

Add your OpenAI API key to the `.env` file:
```
OPENAI_API_KEY=your-key-here
```

(Only needed for the AI insights feature — everything else works without it)

## Project Structure

```
├── data/
│   └── sample_transactions.csv     # the transaction data
├── src/
│   ├── __init__.py
│   ├── transaction_processor.py    # loads, cleans, stores, analyzes
│   ├── insights_generator.py       # OpenAI integration
│   └── dashboard.py                # Streamlit dashboard
├── .env                            # API key (not committed)
├── requirements.txt
├── SOLUTION.md                     # design decisions and assumptions
└── README.md
```

## Running

**To run theDashboard:**
```bash
cd src && streamlit run dashboard.py
```

**To run the analytics:**
```bash
python -m src.transaction_processor
```

**To generate insights:**
```bash
python -m src.insights_generator
```

## Data

The CSV has columns: `timestamp`, `ticker`, `action`, `quantity`, `price`, `trader_id`

There are data quality issues (missing values, duplicates, negative prices, etc.) — the processor handles all of these automatically. See `SOLUTION.md` for details on what I found and how I handled it.
