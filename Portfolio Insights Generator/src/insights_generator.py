import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)


def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set — add it to your .env file")
    return OpenAI(api_key=api_key)


def build_prompt(analytics):
    """builds the prompt we send to the LLM with the analytics data"""
    data_str = json.dumps(analytics, indent=2, default=str)

    return f"""You are a financial analyst reviewing trading data.
Here is a summary of the transactions:

{data_str}

Please analyze this and cover:
1. Trading patterns — which tickers are most traded, any buy/sell imbalances?
2. Concentration risks — any traders or tickers taking up too much of the volume?
3. Unusual activity — anything that stands out as abnormal?
4. Time patterns — when does most trading happen?
5. What should be monitored further?

Use specific numbers from the data. Format with headers and bullet points."""


def generate_insights(analytics, model="gpt-4o-mini"):
    """sends analytics to openai and gets back insights"""
    client = get_client()
    prompt = build_prompt(analytics)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a financial analyst who specializes in trading pattern analysis."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    return response.choices[0].message.content


def generate_insights_safe(analytics):
    """wrapper that catches errors instead of crashing"""
    try:
        return generate_insights(analytics)
    except ValueError as e:
        return f"Config error: {e}"
    except Exception as e:
        return f"Error generating insights: {e}"


if __name__ == "__main__":
    from transaction_processor import load_csv, clean_data, build_ticker_index, get_summary

    raw = load_csv("../data/sample_transactions.csv")
    transactions, _ = clean_data(raw)
    index = build_ticker_index(transactions)
    analytics = get_summary(transactions, index)

    print("Generating insights...")
    result = generate_insights_safe(analytics)
    print(result)
