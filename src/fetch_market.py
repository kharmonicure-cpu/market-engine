from pathlib import Path
from datetime import datetime
import random


def fetch_market_data() -> dict:
    """
    지금은 연습용 더미 데이터.
    나중에 네이버/KRX/키움 API로 교체할 자리.
    """

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "kospi": round(random.uniform(-1.5, 1.5), 2),
        "kosdaq": round(random.uniform(-2.0, 2.0), 2),
        "up_count": random.randint(200, 900),
        "down_count": random.randint(100, 800),
        "strong_sectors": ["반도체", "방산"],
        "leaders": ["삼성전자", "SK하이닉스", "한화시스템"],
        "foreign_flow": "매수",
        "institution_flow": "매도",
        "stock_prices": {
            "삼성전자": random.randint(188000, 194000),
            "SK하이닉스": random.randint(930000, 950000),
            "한화시스템": random.randint(148000, 153000),
            "현대차": random.randint(545000, 560000),
            "기아": random.randint(125000, 131000),
        },
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