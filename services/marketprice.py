import requests
import logging
from os import getenv

API_KEY = getenv("ALPHA_VANTAGE_KEY")  # Make sure you set this in environment

def get_live_price(symbol):
    """
    Get live price for a symbol.
    Supports:
    - Indian stocks (BSE) using symbol.BSE
    - Crypto (BTC, ETH, etc.) using Crypto API
    """

    symbol = symbol.upper()

    # If symbol is a known crypto
    crypto_symbols = ["BTC", "ETH", "LTC", "XRP", "DOGE"]
    if symbol in crypto_symbols:
        try:
            url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={symbol}&to_currency=INR&apikey={API_KEY}"
            response = requests.get(url)
            data = response.json()
            if "Realtime Currency Exchange Rate" not in data:
                logging.warning(f"No crypto quote for {symbol}: {data}")
                raise ValueError(f"No crypto quote found for {symbol}")
            price = float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
            return price
        except Exception as e:
            logging.error(f"Error fetching crypto price for {symbol}: {e}")
            raise

    # Otherwise, treat as BSE stock
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}.BSE&apikey={API_KEY}"
        response = requests.get(url)
        data = response.json()
        if "Global Quote" not in data or not data["Global Quote"]:
            logging.warning(f"No Global Quote for {symbol}.BSE: {data}")
            raise ValueError(f"Stock symbol {symbol} not found on BSE")
        price = float(data["Global Quote"]["05. price"])
        return price
    except Exception as e:
        logging.error(f"Error fetching stock price for {symbol}: {e}")
        raise

