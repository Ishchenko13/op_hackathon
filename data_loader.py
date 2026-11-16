import pandas as pd

def load_city_data(path: str = "data/cities.csv") -> pd.DataFrame:
    """
    Returns a pandas DataFrame with city, month, price_eur, and crowd_index.
    month is an integer from 1 to 12. Each city-month pair is unique.
    Prices must be finite and positive, and proxy values must be finite and nonnegative.
    """
    df = pd.read_csv(path)
    
    # Validation checks according to contract
    expected_cols = {"city", "month", "price_eur", "crowd_index"}
    if not expected_cols.issubset(df.columns):
        raise ValueError(f"Missing columns in dataset. Expected: {expected_cols}")
        
    # Ensure month is integer 1-12
    df["month"] = df["month"].astype(int)
    if not df["month"].between(1, 12).all():
        raise ValueError("Months must be integers between 1 and 12.")
        
    # Check uniqueness of city-month pairs
    if df.duplicated(subset=["city", "month"]).any():
        raise ValueError("Duplicate city-month pairs found in dataset.")
        
    # Prices must be finite and positive
    if not (df["price_eur"] > 0).all() or not df["price_eur"].notna().all():
        raise ValueError("All prices must be finite and positive.")
        
    # Proxy values must be finite and nonnegative
    if not (df["crowd_index"] >= 0).all() or not df["crowd_index"].notna().all():
        raise ValueError("All crowd indices must be finite and nonnegative.")
        
    return df


def load_provenance(path: str = "data/provenance.csv") -> pd.DataFrame:
    """
    Returns source metadata keyed by city and month, including price and proxy source URLs,
    snapshot dates or review periods, methodology, and data_status (observed or demo).
    """
    df = pd.read_csv(path)
    expected_cols = {
        "city", "month", "price_source_url", "proxy_source_url", 
        "snapshot_date", "methodology", "data_status"
    }
    if not expected_cols.issubset(df.columns):
        raise ValueError(f"Missing columns in provenance data. Expected: {expected_cols}")
        
    df["month"] = df["month"].astype(int)
    return df
