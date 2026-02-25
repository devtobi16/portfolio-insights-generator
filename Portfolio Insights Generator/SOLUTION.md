# SOLUTION.md

## Data Processing Decisions

When I loaded the CSV I found 1215 rows with various issues. Here's what I ran into and how I handled each one:

**Duplicates:** Found exact duplicate rows — I hashed each row's fields as a tuple and removed the copies. Pretty straightforward.

**Missing fields:** Some rows had empty timestamps, tickers, prices, or actions. Since these are all important fields for a valid transaction, I just dropped those rows. I thought about trying to fill in missing values but for financial data that felt risky, it is better to throw out bad data than make assumptions.

**Invalid actions:** Found some rows with "HOLD" or lowercase "buy"/"sell". I normalized everything to uppercase first, then kept only BUY and SELL. While HOLD is a valid recommendation in finance (meaning the stock is fairly valued and expected to perform in line with the market), it isn't an executable transaction, this dataset tracks actual trades, not analyst recommendations. The lowercase entries were just formatting issues so those got normalized and kept.

**Negative/zero prices:** Prices should always be positive for a real trade, so these got removed.

**Zero/negative quantities:** Same logic,you can't trade 0 shares.

**Whitespace in tickers:** Some tickers had extra spaces like "  AMZN  ". I stripped whitespace and uppercased all tickers during normalization.

**End result:** 1089 clean transactions out of 1215 rows. I sorted everything by timestamp at the end so it's always in chronological order.

## API Design
- `src/transaction_processor.py` — handles loading, cleaning, storing, and analyzing the data
- `src/insights_generator.py` — sends the analytics to OpenAI and gets back insights
- `src/dashboard.py` — Streamlit app

For the transaction processor I went with functions instead of classes since the data flow is mostly linear,load → clean → index → analyze. The main data structure choice was using a **dict mapping ticker → list of transactions** for the index. This gives O(1) lookup by ticker which matters when you have a lot of operations to execute.

All the analytics (volume, net position, active traders, time analysis) are separate functions that take the transaction list or index as input. I liked this approach because each function does one thing and they're easy to test individually.

For the LLM part, I used OpenAI's `gpt-4o-mini` since it's cheap and fast. The prompt includes the full analytics summary as JSON so the model has all the numbers to work with.

## AI Tools Used

I used Claude & Antigravity to help me get started with the project structure and boilerplate. I wrote the core logic myself,the data cleaning pipeline, analytics functions, and dashboard layout. The AI helped mostly with setup and connecting the pieces together.

OpenAI GPT-4o-mini is used at runtime to generate the trading insights.

## Time Spent

About 3-4 hours total. Most of the time went into figuring out what data quality issues existed in the CSV and deciding how to handle each one.
