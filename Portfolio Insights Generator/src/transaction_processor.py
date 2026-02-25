import csv
from datetime import datetime
from collections import defaultdict


def load_csv(filepath):
    """reads the csv and returns raw rows as list of dicts"""
    rows = []
    with open(filepath, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def clean_data(raw_rows):
    """goes through raw rows, removes bad data, returns (clean_rows, cleaning_log)"""
    cleaning_log = {}

    # remove exact duplicates first
    seen = set()
    unique = []
    dupes = 0
    for row in raw_rows:
        key = tuple(sorted(row.items()))
        if key in seen:
            dupes += 1
            continue
        else:
            seen.add(key)
            unique.append(row)
    cleaning_log["duplicates"] = dupes

    # now validate each row
    clean = []
    missing_ts = 0
    missing_ticker = 0
    missing_price = 0
    missing_action = 0
    bad_action = 0
    bad_price = 0
    bad_qty = 0
    parse_err = 0

    for row in unique:
        # check for empty required fields
        if not row.get("timestamp", "").strip():
            missing_ts += 1
            continue
        if not row.get("ticker", "").strip():
            missing_ticker += 1
            continue
        if not row.get("price", "").strip():
            missing_price += 1
            continue
        if not row.get("action", "").strip():
            missing_action += 1
            continue

        try:
            # normalize the fields
            ticker = row["ticker"].strip().upper()
            action = row["action"].strip().upper()
            price = float(row["price"])
            quantity = int(row["quantity"])
            timestamp = datetime.strptime(row["timestamp"].strip(), "%Y-%m-%d %H:%M:%S")
            trader_id = row.get("trader_id", "UNKNOWN").strip()

            # validate values
            if action not in ("BUY", "SELL"):
                bad_action += 1
                continue
            if price <= 0:
                bad_price += 1
                continue
            if quantity <= 0:
                bad_qty += 1
                continue

            clean.append({
                "timestamp": timestamp,
                "ticker": ticker,
                "action": action,
                "quantity": quantity,
                "price": price,
                "trader_id": trader_id,
            })
        except (ValueError, KeyError):
            parse_err += 1

    cleaning_log["missing_timestamp"] = missing_ts
    cleaning_log["missing_ticker"] = missing_ticker
    cleaning_log["missing_price"] = missing_price
    cleaning_log["missing_action"] = missing_action
    cleaning_log["invalid_action"] = bad_action
    cleaning_log["negative_zero_price"] = bad_price
    cleaning_log["zero_negative_qty"] = bad_qty
    cleaning_log["parse_errors"] = parse_err

    # sort by time
    clean.sort(key=lambda x: x["timestamp"])
    return clean, cleaning_log


def build_ticker_index(transactions):
    """builds a dict mapping ticker -> list of transactions for fast lookup"""
    index = defaultdict(list)
    for txn in transactions:
        index[txn["ticker"]].append(txn)
    return dict(index)


def get_by_ticker(index, ticker):
    """look up transactions for a specific ticker"""
    return index.get(ticker.upper(), [])


def get_by_time_range(transactions, start, end):
    """get transactions between two datetimes"""
    return [t for t in transactions if start <= t["timestamp"] <= end]


# ---- analytics functions ----

def total_volume_by_ticker(index):
    """total dollar volume (qty * price) per ticker"""
    volume = {}
    for ticker, txns in index.items():
        volume[ticker] = sum(t["quantity"] * t["price"] for t in txns)
    # sort by volume descending
    return dict(sorted(volume.items(), key=lambda x: x[1], reverse=True))


def net_position_by_ticker(index):
    """net shares per ticker (buys - sells)"""
    positions = {}
    for ticker, txns in index.items():
        net = 0
        for t in txns:
            if t["action"] == "BUY":
                net += t["quantity"]
            else:
                net -= t["quantity"]
        positions[ticker] = net
    return dict(sorted(positions.items(), key=lambda x: abs(x[1]), reverse=True))


def most_active_traders(transactions, top_n=10):
    """traders with the most transactions"""
    counts = defaultdict(int)
    for t in transactions:
        counts[t["trader_id"]] += 1
    sorted_traders = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_traders[:top_n]


def time_based_analysis(transactions):
    """basic analysis of when trading happens"""
    monthly = defaultdict(int)
    hourly = defaultdict(int)
    daily_vol = defaultdict(float)

    for t in transactions:
        month = t["timestamp"].strftime("%Y-%m")
        hour = t["timestamp"].hour
        day = t["timestamp"].strftime("%Y-%m-%d")

        monthly[month] += 1
        hourly[hour] += 1
        daily_vol[day] += t["quantity"] * t["price"]

    peak_day = max(daily_vol, key=daily_vol.get) if daily_vol else "N/A"
    peak_hour = max(hourly, key=hourly.get) if hourly else "N/A"

    return {
        "monthly": dict(sorted(monthly.items())),
        "hourly": dict(sorted(hourly.items())),
        "peak_day": peak_day,
        "peak_day_volume": daily_vol.get(peak_day, 0),
        "peak_hour": peak_hour,
        "trading_days": len(daily_vol),
    }


def get_summary(transactions, index):
    """puts together the full analytics summary"""
    total = len(transactions)
    buys = sum(1 for t in transactions if t["action"] == "BUY")
    sells = total - buys
    dollar_vol = sum(t["quantity"] * t["price"] for t in transactions)
    tickers = sorted(index.keys())
    traders = list({t["trader_id"] for t in transactions})

    return {
        "total_transactions": total,
        "total_buys": buys,
        "total_sells": sells,
        "total_dollar_volume": round(dollar_vol, 2),
        "unique_tickers": tickers,
        "unique_traders_count": len(traders),
        "volume_by_ticker": total_volume_by_ticker(index),
        "net_position_by_ticker": net_position_by_ticker(index),
        "most_active_traders": most_active_traders(transactions),
        "time_analysis": time_based_analysis(transactions),
    }


def format_cleaning_log(log, total_raw, total_clean):
    """makes the cleaning log readable"""
    lines = [f"Raw rows: {total_raw}", f"Clean rows: {total_clean}", ""]
    for key, count in log.items():
        if count > 0:
            lines.append(f"  {key}: {count} removed")
    lines.append(f"\nTotal removed: {total_raw - total_clean}")
    return "\n".join(lines)


if __name__ == "__main__":
    import json

    raw = load_csv("data/sample_transactions.csv")
    transactions, log = clean_data(raw)
    index = build_ticker_index(transactions)

    print("=" * 50)
    print("CLEANING REPORT")
    print("=" * 50)
    print(format_cleaning_log(log, len(raw), len(transactions)))

    print("\n" + "=" * 50)
    print("ANALYTICS")
    print("=" * 50)
    summary = get_summary(transactions, index)
    print(json.dumps(summary, indent=2, default=str))

    # quick lookup test
    print("\n" + "=" * 50)
    print("AAPL TRANSACTIONS (first 5)")
    print("=" * 50)
    aapl = get_by_ticker(index, "AAPL")
    for t in aapl[:5]:
        print(f"  {t['timestamp']} | {t['action']} {t['quantity']} @ ${t['price']:.2f} | {t['trader_id']}")
