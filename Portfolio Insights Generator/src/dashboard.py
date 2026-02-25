import streamlit as st
import pandas as pd
from transaction_processor import load_csv, clean_data, build_ticker_index, get_summary, format_cleaning_log, get_by_ticker
from insights_generator import generate_insights_safe


@st.cache_data
def load_data():
    raw = load_csv("../data/sample_transactions.csv")
    transactions, log = clean_data(raw)
    index = build_ticker_index(transactions)
    analytics = get_summary(transactions, index)
    cleaning_text = format_cleaning_log(log, len(raw), len(transactions))
    return transactions, index, analytics, cleaning_text


def main():
    st.set_page_config(page_title="Portfolio Insights Generator", layout="wide")
    st.title("Portfolio Insights Generator")
    st.caption("Financial transaction analysis powered by AI")

    transactions, index, analytics, cleaning_text = load_data()


    st.divider()

    # key stats
    st.header("Key Statistics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Transactions", f"{analytics['total_transactions']:,}")
    c2.metric("Total Buys", f"{analytics['total_buys']:,}")
    c3.metric("Total Sells", f"{analytics['total_sells']:,}")
    c4.metric("Dollar Volume", f"${analytics['total_dollar_volume']:,.0f}")

    c5, c6, c7 = st.columns(3)
    c5.metric("Unique Tickers", len(analytics["unique_tickers"]))
    c6.metric("Unique Traders", analytics["unique_traders_count"])
    c7.metric("Trading Days", analytics["time_analysis"]["trading_days"])

    st.divider()

    # volume and positions side by side
    left, right = st.columns(2)

    with left:
        st.subheader("Top Tickers by Volume")
        vol_df = pd.DataFrame(
            [{"Ticker": k, "Volume ($)": f"${v:,.2f}"} for k, v in analytics["volume_by_ticker"].items()]
        )
        st.dataframe(vol_df, hide_index=True)

    with right:
        st.subheader("Net Position by Ticker")
        pos_df = pd.DataFrame(
            [{"Ticker": k, "Net Shares": v} for k, v in analytics["net_position_by_ticker"].items()]
        )
        st.dataframe(pos_df, hide_index=True)

    st.divider()

    # most active traders
    st.subheader("Most Active Traders")
    trader_df = pd.DataFrame(analytics["most_active_traders"], columns=["Trader", "Transactions"])
    st.bar_chart(trader_df.set_index("Trader"))

    st.divider()

    # time analysis
    st.subheader("Time Analysis")
    t1, t2 = st.columns(2)

    with t1:
        st.write("**Monthly**")
        monthly = pd.DataFrame(
            [{"Month": k, "Count": v} for k, v in analytics["time_analysis"]["monthly"].items()]
        )
        st.bar_chart(monthly.set_index("Month"))

    with t2:
        st.write("**Hourly**")
        hourly = pd.DataFrame(
            [{"Hour": f"{k}:00", "Count": v} for k, v in analytics["time_analysis"]["hourly"].items()]
        )
        st.bar_chart(hourly.set_index("Hour"))

    p1, p2 = st.columns(2)
    p1.metric("Peak Day", analytics["time_analysis"]["peak_day"])
    p2.metric("Peak Hour", f"{analytics['time_analysis']['peak_hour']}:00")

    st.divider()

    # raw data viewer
    with st.expander("Raw Data"):
        raw_df = pd.DataFrame([
            {
                "Time": t["timestamp"].strftime("%Y-%m-%d %H:%M"),
                "Ticker": t["ticker"],
                "Action": t["action"],
                "Qty": t["quantity"],
                "Price": f"${t['price']:.2f}",
                "Trader": t["trader_id"],
            }
            for t in transactions
        ])
        st.dataframe(raw_df, hide_index=True)

    st.divider()

    # ticker lookup
    st.subheader("Ticker Lookup")
    ticker = st.selectbox("Pick a ticker:", sorted(analytics["unique_tickers"]))
    if ticker:
        results = get_by_ticker(index, ticker)
        st.write(f"**{len(results)}** transactions for {ticker}")
        ticker_df = pd.DataFrame([
            {
                "Time": t["timestamp"].strftime("%Y-%m-%d %H:%M"),
                "Action": t["action"],
                "Qty": t["quantity"],
                "Price": f"${t['price']:.2f}",
                "Trader": t["trader_id"],
            }
            for t in results
        ])
        st.dataframe(ticker_df, hide_index=True)

    st.divider()

    # AI insights
    st.header("AI Insights")
    if st.button("Generate Insights", type="primary"):
        with st.spinner("Thinking..."):
            insights = generate_insights_safe(analytics)
            st.session_state["insights"] = insights

    if "insights" in st.session_state:
        st.markdown(st.session_state["insights"])


if __name__ == "__main__":
    main()
