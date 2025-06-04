import json

def stock_json_to_text(data: dict) -> str:
    """
    Converts a stock snapshot JSON into a readable text string.
    """
    try:
        security = data.get("security", "Unknown")
        price = data.get("price", 0.0)
        change_percent = data.get("changePercent", 0.0)
        volume = data.get("tradeVolume", 0)
        is_open = data.get("isMarketOpen", False)
        status = data.get("marketStatus", "Unknown")
        timestamp = data.get("timestamp", "Unknown")

        market_open_text = "open" if is_open else "closed"

        return (
            f"Security: {security}. Price: ${price:.2f}. "
            f"Change: {change_percent:.2f}%. Volume: {volume}. "
            f"Market is currently {market_open_text} ({status}). "
            f"Timestamp: {timestamp}."
        )
    except Exception as e:
        return f"Error formatting stock data: {e}"

def try_parse_json_or_text(raw_data: str) -> str:
    """
    Attempts to parse raw S3 object content as JSON.
    If successful, converts it to a string using `json_to_text`.
    Otherwise, returns the raw text unchanged.
    """
    try:
        parsed = json.loads(raw_data)
        if isinstance(parsed, dict):
            return stock_json_to_text(parsed)
    except json.JSONDecodeError:
        pass  # not JSON

    return raw_data  # plain text
