import os
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests


NEWS_COLUMNS = [
    "date",
    "time_published",
    "title",
    "summary",
    "source",
    "url",
    "overall_sentiment_score",
    "overall_sentiment_label",
]


def empty_news_df() -> pd.DataFrame:
    return pd.DataFrame(columns=NEWS_COLUMNS)


def load_existing_news(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        return empty_news_df()

    try:
        df = pd.read_csv(csv_path)

        if df.empty:
            return empty_news_df()

        for col in NEWS_COLUMNS:
            if col not in df.columns:
                df[col] = pd.NA

        df = df[NEWS_COLUMNS].copy()

        df["time_published"] = pd.to_datetime(df["time_published"], errors="coerce")
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

        return df

    except Exception as e:
        print(f"Nie udało się odczytać pliku CSV: {e}")
        return empty_news_df()


def clean_news_df(df: pd.DataFrame, min_date: str = "2026-01-01") -> pd.DataFrame:
    if df.empty:
        return empty_news_df()

    df = df.copy()

    for col in NEWS_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[NEWS_COLUMNS].copy()

    df["time_published"] = pd.to_datetime(df["time_published"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    df = df.dropna(subset=["time_published", "title", "source"])

    min_ts = pd.Timestamp(min_date)
    df = df[df["time_published"] >= min_ts]

    btc_keywords = [
        "bitcoin",
        "btc",
        "xbt",
        "btc-usd",
        "bitcoin etf",
        "spot bitcoin etf",
        "bitcoin price",
        "btc price",
        "bitcoin mining",
        "bitcoin miner",
        "bitcoin treasury",
        "crypto",
        "cryptocurrency",
        "digital asset",
    ]

    exclude_if_no_btc_keywords = [
        "ethereum",
        "ether",
        "eth",
        "dogecoin",
        "doge",
        "xrp",
        "solana",
        "cardano",
        "ada",
        "nft",
        "defi",
        "altcoin",
        "altcoins",
    ]

    text_series = (
        df["title"].fillna("").astype(str).str.lower() + " " +
        df["summary"].fillna("").astype(str).str.lower()
    )

    mask_btc = pd.Series(False, index=df.index)
    for keyword in btc_keywords:
        mask_btc = mask_btc | text_series.str.contains(keyword, regex=False)

    mask_other_topics = pd.Series(False, index=df.index)
    for keyword in exclude_if_no_btc_keywords:
        mask_other_topics = mask_other_topics | text_series.str.contains(keyword, regex=False)

    df = df[mask_btc | (~mask_other_topics)].copy()

    df = df.drop_duplicates(subset=["time_published", "title", "source"])
    df = df.sort_values("time_published").reset_index(drop=True)

    df["date"] = pd.to_datetime(df["time_published"], errors="coerce").dt.date

    return df


def fetch_news_from_api(
    api_key: str,
    time_from: str,
    time_to: str | None = None,
    limit: int = 1000,
) -> list[dict]:
    url = "https://www.alphavantage.co/query"

    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": "CRYPTO:BTC",
        "time_from": time_from,
        "sort": "EARLIEST",
        "limit": limit,
        "apikey": api_key,
    }

    if time_to is not None:
        params["time_to"] = time_to

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Błąd zapytania do API: {e}")
        return []
    except ValueError as e:
        print(f"Błąd parsowania odpowiedzi API: {e}")
        return []

    if "feed" in data:
        return data["feed"]

    print("Odpowiedź API:")
    print(data)

    if "Information" in data:
        info = str(data["Information"]).lower()

        if "rate limit" in info or "25 requests per day" in info:
            print("Osiągnięto limit API Alpha Vantage.")
            return []

        if "invalid inputs" in info:
            print("Próbuję ponownie bez parametru time_to...")
            time.sleep(1.2)

            retry_params = {
                "function": "NEWS_SENTIMENT",
                "tickers": "CRYPTO:BTC",
                "time_from": time_from,
                "sort": "EARLIEST",
                "limit": limit,
                "apikey": api_key,
            }

            try:
                response = requests.get(url, params=retry_params, timeout=30)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                print(f"Błąd ponownego zapytania do API: {e}")
                return []
            except ValueError as e:
                print(f"Błąd parsowania drugiej odpowiedzi API: {e}")
                return []

            print("Druga odpowiedź API:")
            print(data)

            if "feed" in data:
                return data["feed"]

            if "Information" in data:
                retry_info = str(data["Information"]).lower()
                if "rate limit" in retry_info or "25 requests per day" in retry_info:
                    print("Osiągnięto limit API Alpha Vantage.")
                    return []

    print("API nie zwróciło pola 'feed'.")
    return []


def transform_feed_to_df(feed: list[dict]) -> pd.DataFrame:
    if not feed:
        return empty_news_df()

    rows = []

    for item in feed:
        rows.append({
            "time_published": item.get("time_published"),
            "title": item.get("title"),
            "summary": item.get("summary"),
            "source": item.get("source"),
            "url": item.get("url"),
            "overall_sentiment_score": item.get("overall_sentiment_score"),
            "overall_sentiment_label": item.get("overall_sentiment_label"),
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return empty_news_df()

    df["time_published"] = pd.to_datetime(
        df["time_published"],
        format="%Y%m%dT%H%M%S",
        errors="coerce",
    )

    df["date"] = df["time_published"].dt.date

    for col in NEWS_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[NEWS_COLUMNS].copy()

    return df


def fetch_news_for_window(api_key: str, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    time_from = start_dt.strftime("%Y%m%dT%H%M")
    time_to = end_dt.strftime("%Y%m%dT%H%M")

    print(f"Pobieranie okresu: {time_from} -> {time_to}")

    feed = fetch_news_from_api(
        api_key=api_key,
        time_from=time_from,
        time_to=time_to,
        limit=1000,
    )

    if not feed:
        print("Brak danych w tym okresie.")
        return empty_news_df()

    df = transform_feed_to_df(feed)
    print(f"Pobrano rekordów: {len(df)}")
    return df


def build_initial_news_csv(
    api_key: str,
    csv_path: str = "btc_news.csv",
    start_date: str = "2026-01-01",
) -> pd.DataFrame:
    existing_news = load_existing_news(csv_path)
    existing_news = clean_news_df(existing_news, min_date=start_date)

    if not existing_news.empty:
        print("Plik już zawiera dane.")
        print(f"Liczba istniejących rekordów: {len(existing_news)}")
        print(
            f"Zakres dat istniejącego pliku: "
            f"{existing_news['time_published'].min()} -> {existing_news['time_published'].max()}"
        )
        print("Plik nie został nadpisany.")
        return existing_news

    start_dt = pd.Timestamp(start_date).to_pydatetime()
    now_dt = datetime.now(timezone.utc).replace(tzinfo=None)

    parts = []
    current_start = start_dt

    while current_start < now_dt:
        next_month_start = (pd.Timestamp(current_start) + pd.offsets.MonthBegin(1)).to_pydatetime()
        current_end = min(next_month_start, now_dt)

        chunk_df = fetch_news_for_window(api_key, current_start, current_end)
        if not chunk_df.empty:
            parts.append(chunk_df)

        time.sleep(1.2)
        current_start = current_end

    if not parts:
        print("Nie pobrano żadnych danych startowych.")
        print("Istniejący plik nie został nadpisany pustym DataFrame.")
        return empty_news_df()

    all_news = pd.concat(parts, ignore_index=True)
    all_news = clean_news_df(all_news, min_date=start_date)

    if all_news.empty:
        print("Po czyszczeniu nie zostały żadne rekordy.")
        print("Plik nie został zapisany, aby nie nadpisać danych pustym plikiem.")
        return empty_news_df()

    all_news.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print("Zakończono budowę pliku startowego.")
    print(f"Liczba rekordów po czyszczeniu: {len(all_news)}")
    print(f"Zakres dat: {all_news['time_published'].min()} -> {all_news['time_published'].max()}")

    return all_news


def update_news_csv(
    api_key: str,
    csv_path: str = "btc_news.csv",
    min_date: str = "2026-01-01",
) -> pd.DataFrame:
    existing_news = load_existing_news(csv_path)
    existing_news = clean_news_df(existing_news, min_date=min_date)

    old_count = len(existing_news)

    if existing_news.empty or not existing_news["time_published"].notna().any():
        print("Plik jest pusty albo nie zawiera poprawnych dat.")
        print("Najpierw uruchom budowę danych startowych.")
        return existing_news

    last_time = existing_news["time_published"].max().floor("min")
    next_time = last_time + timedelta(minutes=1)
    now_dt = datetime.now(timezone.utc).replace(tzinfo=None)

    if next_time >= now_dt:
        print("Brak nowych newsów do pobrania.")
        print(f"Liczba rekordów bez zmian: {old_count}")
        return existing_news

    print(f"Pobieranie nowych newsów od: {next_time} do: {now_dt}")

    new_news = fetch_news_for_window(api_key, next_time, now_dt)

    if new_news.empty:
        print("Brak nowych rekordów z API.")
        print("Istniejący plik pozostaje bez zmian.")
        print(f"Liczba rekordów bez zmian: {old_count}")
        return existing_news

    all_news = pd.concat([existing_news, new_news], ignore_index=True)
    all_news = clean_news_df(all_news, min_date=min_date)

    new_count = len(all_news)

    if new_count == 0:
        print("Po połączeniu i czyszczeniu nie ma żadnych danych.")
        print("Plik nie został nadpisany.")
        return existing_news

    all_news.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"Było rekordów: {old_count}")
    print(f"Jest rekordów: {new_count}")
    print(f"Przybyło: {new_count - old_count}")
    print(f"Zakres dat: {all_news['time_published'].min()} -> {all_news['time_published'].max()}")

    return all_news