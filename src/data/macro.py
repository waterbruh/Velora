"""
Makro-Daten: US (FRED) + EU (ECB).
Zinsen, Inflation, Arbeitslosigkeit, Yield Curves.
"""

import logging
from datetime import datetime, timedelta

import requests

logger = logging.getLogger(__name__)


def fetch_fred_data(api_key: str) -> dict:
    """Holt wichtige US-Makrodaten von FRED."""
    series = {
        "fed_funds_rate": "FEDFUNDS",
        "us_cpi_yoy": "CPIAUCSL",
        "us_10y_yield": "DGS10",
        "us_2y_yield": "DGS2",
        "us_unemployment": "UNRATE",
        "us_gdp_growth": "A191RL1Q225SBEA",
        "vix": "VIXCLS",
        "credit_spread_hy": "BAMLH0A0HYM2",
    }

    results = {}
    base_url = "https://api.stlouisfed.org/fred/series/observations"
    today = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    for name, series_id in series.items():
        try:
            params = {
                "series_id": series_id,
                "api_key": api_key,
                "file_type": "json",
                "observation_start": start,
                "observation_end": today,
                "sort_order": "desc",
                "limit": 5,
            }
            resp = requests.get(base_url, params=params, timeout=10)
            data = resp.json()
            observations = data.get("observations", [])
            if observations:
                latest = observations[0]
                value = latest.get("value", ".")
                if value != ".":
                    results[name] = {
                        "value": float(value),
                        "date": latest["date"],
                        "source": f"FRED:{series_id}",
                    }
        except Exception as e:
            logger.error(f"FRED {name} ({series_id}) Fehler: {e}")

    # Yield Curve Spread berechnen
    if "us_10y_yield" in results and "us_2y_yield" in results:
        spread = results["us_10y_yield"]["value"] - results["us_2y_yield"]["value"]
        results["yield_curve_spread"] = {
            "value": round(spread, 3),
            "date": results["us_10y_yield"]["date"],
            "source": "berechnet aus FRED:DGS10 - FRED:DGS2",
            "note": "negativ = invertiert = Rezessionssignal",
        }

    return results


def fetch_ecb_data() -> dict:
    """Holt EZB-Daten direkt von der ECB Data API."""
    results = {}

    endpoints = {
        "ecb_main_rate": {
            "url": "https://data-api.ecb.europa.eu/service/data/FM/M.U2.EUR.4F.KR.MRR_FR.LEV",
            "desc": "EZB Hauptrefinanzierungssatz",
        },
        "eu_hicp_inflation": {
            "url": "https://data-api.ecb.europa.eu/service/data/ICP/M.U2.N.000000.4.ANR",
            "desc": "HICP Inflation Eurozone YoY",
        },
        "eur_usd": {
            "url": "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A",
            "desc": "EUR/USD Wechselkurs",
        },
    }

    headers = {"Accept": "application/vnd.sdmx.data+json;version=1.0.0-wd"}

    for name, ep in endpoints.items():
        try:
            params = {"lastNObservations": "1"}
            resp = requests.get(ep["url"], headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                datasets = data.get("dataSets", [{}])
                if datasets:
                    series = datasets[0].get("series", {})
                    for key, s in series.items():
                        obs = s.get("observations", {})
                        if obs:
                            last_key = max(obs.keys())
                            value = obs[last_key][0]
                            results[name] = {
                                "value": float(value),
                                "description": ep["desc"],
                                "source": "ECB Data API",
                                "timestamp": datetime.now().isoformat(),
                            }
        except Exception as e:
            logger.error(f"ECB {name} Fehler: {e}")

    return results


def fetch_fear_greed() -> dict | None:
    """CNN Fear & Greed Index."""
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        fg = data.get("fear_and_greed", {})
        return {
            "value": fg.get("score"),
            "rating": fg.get("rating"),
            "previous_close": fg.get("previous_close"),
            "previous_1_week": fg.get("previous_1_week"),
            "previous_1_month": fg.get("previous_1_month"),
            "previous_1_year": fg.get("previous_1_year"),
            "source": "CNN Fear & Greed Index",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Fear & Greed Fehler: {e}")
        return None


def collect_all_macro_data(fred_api_key: str) -> dict:
    """Sammelt alle Makrodaten."""
    fred = fetch_fred_data(fred_api_key) if fred_api_key else {}
    ecb = fetch_ecb_data()
    fear_greed = fetch_fear_greed()

    return {
        "us": fred,
        "eu": ecb,
        "fear_greed": fear_greed,
        "collected_at": datetime.now().isoformat(),
    }
