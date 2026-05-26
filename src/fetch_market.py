from pathlib import Path
from datetime import datetime
import csv


def load_stock_prices(file_path: str = "data/stock_prices.csv") -> dict:
    """
    data/stock_prices.csv 파일에서 종목 가격을 읽어온다.
    32비트 키움 환경에서도 pandas/yfinance 없이 실행 가능하다.
    """

    path = Path(file_path)

    if not path.exists():
        print(f"[WARN] 가격 파일이 없습니다: {file_path}")
        return {}

    stock_prices = {}

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            stock = row["stock"]
            price = int(row["price"])
            stock_prices[stock] = price

    return stock_prices


def fetch_market_data() -> dict:
    """
    CSV 기반 시장 데이터 수집
    yfinance/pandas 없이 32비트 Python에서 실행 가능
    """

    stock_prices = load_stock_prices()

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),

        # 아직은 임시값
        "kospi": 0.0,
        "kosdaq": 0.0,
        "up_count": 0,
        "down_count": 0,

        # 아직은 임시값
        "strong_sectors": ["반도체", "자동차"],
        "leaders": list(stock_prices.keys()),

        # 아직은 임시값
        "foreign_flow": "확인필요",
        "institution_flow": "확인필요",

        # CSV에서 읽은 가격
        "stock_prices": stock_prices,
    }


def save_market_file(data: dict, file_path: str = "data/market.txt") -> None:
    strong_sector_text = " ".join(data["strong_sectors"]) if data["strong_sectors"] else "없음"
    leaders_text = " ".join(data["leaders"]) if data["leaders"] else "없음"

    stock_price_parts = []

    for stock, price in data["stock_prices"].items():
        stock_price_parts.append(f"{stock}:{price}")

    stock_price_text = "|".join(stock_price_parts)

    text = f"""
시각 {data['timestamp']}
코스피 {data['kospi']}%
코스닥 {data['kosdaq']}%
상승종목수 {data['up_count']}
하락종목수 {data['down_count']}
강한섹터 {strong_sector_text}
거래대금상위 {leaders_text}
종목현재가 {stock_price_text}
외국인 {data['foreign_flow']}
기관 {data['institution_flow']}
""".strip()

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_fetch_once() -> dict:
    data = fetch_market_data()
    save_market_file(data)
    return data


if __name__ == "__main__":
    data = run_fetch_once()
    print("시장 데이터 1회 갱신 완료")
    print(data)