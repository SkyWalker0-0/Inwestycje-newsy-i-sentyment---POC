import pandas as pd
import yfinance as yf


def load_btc_for_news_period(
    news_df: pd.DataFrame,
    force_interval: str | None = None,
) -> pd.DataFrame:
    news = news_df.copy()

    news["time_published"] = pd.to_datetime(news["time_published"], errors="coerce")
    news = news.dropna(subset=["time_published"])

    if news.empty:
        raise ValueError("DataFrame z newsami jest pusty albo nie zawiera poprawnych dat.")

    start_dt = news["time_published"].min()
    end_dt = news["time_published"].max()
    span_days = (end_dt - start_dt).days

    allowed_intervals = {"1h", "1d"}
    if force_interval is not None and force_interval not in allowed_intervals:
        raise ValueError("force_interval musi być równe '1h' albo '1d'.")

    if force_interval is not None:
        interval = force_interval
    else:
        if span_days <= 730:
            interval = "1h"
        else:
            interval = "1d"

    start_download = start_dt.floor("D")
    end_download = end_dt.ceil("D") + pd.Timedelta(days=1)

    btc = yf.download(
        "BTC-USD",
        start=start_download.strftime("%Y-%m-%d"),
        end=end_download.strftime("%Y-%m-%d"),
        interval=interval,
        auto_adjust=False,
        progress=False,
    )

    if btc.empty:
        raise ValueError("Nie udało się pobrać danych BTC dla wybranego zakresu dat.")

    if isinstance(btc.columns, pd.MultiIndex):
        btc.columns = btc.columns.get_level_values(0)

    btc = btc.reset_index()

    if "Datetime" in btc.columns:
        btc["Datetime"] = pd.to_datetime(
            btc["Datetime"],
            errors="coerce",
            utc=True,
        ).dt.tz_localize(None)
    elif "Date" in btc.columns:
        btc = btc.rename(columns={"Date": "Datetime"})
        btc["Datetime"] = pd.to_datetime(btc["Datetime"], errors="coerce")
    else:
        raise ValueError("Pobrane dane BTC nie zawierają kolumny Datetime ani Date.")

    required_cols = ["Datetime", "Close", "High", "Low", "Open", "Volume"]
    missing_cols = [col for col in required_cols if col not in btc.columns]

    if missing_cols:
        raise ValueError(f"W danych BTC brakuje wymaganych kolumn: {missing_cols}")

    btc = btc.dropna(subset=["Datetime"]).sort_values("Datetime").reset_index(drop=True)
    btc = btc[required_cols].copy()

    btc["Return"] = btc["Close"].pct_change() * 100
    btc["Range"] = btc["High"] - btc["Low"]

    if interval == "1h":
        btc["time_key"] = btc["Datetime"].dt.floor("h")
    else:
        btc["time_key"] = btc["Datetime"].dt.floor("D")

    btc["btc_interval"] = interval

    return btc