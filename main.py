from pathlib import Path
import re
import csv
from datetime import date
from collections import Counter

from src.risk_engine import filter_orders_by_risk
from src.execution_engine import execute_orders, save_trade_log

TOTAL_CAPITAL = 4_400_000
POSITION_RATIO = 0.2

BIGCAP_WATCHLIST = [
    "삼성전자",
    "SK하이닉스",
    "현대차",
    "기아",
    "한화에어로",
    "LIG넥스원",
    "한화시스템",
    "S-Oil",
    "한국전력",
    "두산에너빌리티",
]

SECTOR_STOCK_MAP = {
    "반도체": ["삼성전자", "SK하이닉스"],
    "방산": ["한화에어로", "LIG넥스원", "한화시스템"],
    "자동차": ["현대차", "기아"],
    "에너지": ["S-Oil"],
}

BASE_PRICE_MAP = {
    "삼성전자": 191200,
    "SK하이닉스": 941000,
    "현대차": 554000,
    "기아": 128000,
    "한화에어로": 485000,
    "LIG넥스원": 152000,
    "한화시스템": 150800,
    "S-Oil": 134600,
    "한국전력": 48550,
    "두산에너빌리티": 91100,
    "POSCO홀딩스": 410000,
    "LG에너지솔루션": 430000,
}

def read_market_file(file_path: str) -> str:
    path = Path(file_path)
    return path.read_text(encoding="utf-8")


def extract_percent(line_prefix: str, text: str) -> float:
    pattern = rf"{line_prefix}\s*([+-]?\d+(?:\.\d+)?)%"
    match = re.search(pattern, text)
    if not match:
        return 0.0
    return float(match.group(1))


def extract_int(line_prefix: str, text: str) -> int:
    pattern = rf"{line_prefix}\s*(\d+)"
    match = re.search(pattern, text)
    if not match:
        return 0
    return int(match.group(1))


def extract_words(line_prefix: str, text: str) -> list[str]:
    pattern = rf"{line_prefix}\s*(.+)"
    match = re.search(pattern, text)
    if not match:
        return []
    value = match.group(1).strip()
    if value == "없음":
        return []
    return value.split()

def extract_stock_prices(line_prefix: str, text: str) -> dict[str, float]:
    pattern = rf"{line_prefix}\s*(.+)"
    match = re.search(pattern, text)
    if not match:
        return {}

    raw_value = match.group(1).strip()
    if raw_value == "없음":
        return {}

    prices = {}
    parts = raw_value.split("|")

    for part in parts:
        if ":" not in part:
            continue
        stock, price = part.split(":", 1)
        stock = stock.strip()
        price = price.strip()

        try:
            prices[stock] = float(price)
        except ValueError:
            continue

    return prices

def detect_flow_keyword(text: str, actor: str) -> str:
    if f"{actor} 매수" in text:
        return "매수"
    if f"{actor} 매도" in text:
        return "매도"
    return "중립"


def classify_market(kospi: float, kosdaq: float, up_count: int, down_count: int) -> str:
    if kospi > 0.5 and kosdaq > 0.5 and up_count > down_count:
        return "Risk-On"
    if kospi < 0 and kosdaq < 0 and down_count > up_count:
        return "Risk-Off"
    return "Neutral"


def find_bigcap_candidates(leaders: list[str], watchlist: list[str]) -> list[str]:
    return [stock for stock in leaders if stock in watchlist]


def score_candidates(
    candidates: list[str],
    market_status: str,
    sectors: list[str],
    foreign_flow: str,
    leaders: list[str],
) -> list[dict]:
    scored = []

    for stock in candidates:
        score = 0
        reasons = []

        if stock in leaders:
            score += 2
            reasons.append("리더종목")

        if sectors:
            score += 2
            reasons.append("강한섹터존재")

        for sector in sectors:
            if sector in SECTOR_STOCK_MAP:
                if stock in SECTOR_STOCK_MAP[sector]:
                    score += 2
                    reasons.append(f"{sector}섹터가산점")

        if foreign_flow == "매수":
            score += 1
            reasons.append("외국인매수")

        if market_status == "Risk-On":
            score += 2
            reasons.append("Risk-On")
        elif market_status == "Neutral":
            score += 1
            reasons.append("Neutral")

        scored.append(
            {
                "stock": stock,
                "score": score,
                "reasons": reasons,
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def make_summary(
    market_status: str,
    sectors: list[str],
    leaders: list[str],
    candidates: list[str],
) -> str:
    sector_text = ", ".join(sectors) if sectors else "뚜렷한 섹터 없음"
    leader_text = ", ".join(leaders[:3]) if leaders else "리더 종목 없음"
    candidate_text = ", ".join(candidates) if candidates else "대형주 후보 없음"

    if market_status == "Risk-On":
        return (
            f"{sector_text} 중심으로 강세가 나타났고, "
            f"리더 종목은 {leader_text}입니다. "
            f"대형주 후보는 {candidate_text}입니다."
        )

    if market_status == "Risk-Off":
        return (
            f"전반적으로 약한 시장이며, 현재 주도 섹터는 {sector_text} 수준입니다. "
            f"대형주 후보는 {candidate_text}입니다."
        )

    return (
        f"중립적인 시장 흐름이며, {sector_text}와 {leader_text}를 계속 관찰해야 합니다. "
        f"대형주 후보는 {candidate_text}입니다."
    )


def save_text_report(file_path: str, content: str) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_csv_row(file_path: str, row: dict) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "date",
        "kospi",
        "kosdaq",
        "up_count",
        "down_count",
        "market_status",
        "sectors",
        "leaders",
        "bigcap_candidates",
        "candidate_scores",
        "candidate_signals",
        "foreign_flow",
        "institution_flow",
        "summary",
    ]

    file_exists = path.exists()

    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def read_history(file_path: str) -> list[dict]:
    path = Path(file_path)
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def summarize_history(rows: list[dict]) -> str:
    if not rows:
        return "최근 기록이 아직 없습니다."

    market_counter = Counter()
    sector_counter = Counter()
    candidate_counter = Counter()

    for row in rows:
        market_status = row.get("market_status", "").strip()
        if market_status:
            market_counter[market_status] += 1

        sectors = row.get("sectors", "").strip()
        if sectors:
            for sector in sectors.split("|"):
                if sector:
                    sector_counter[sector] += 1

        candidates = row.get("bigcap_candidates", "").strip()
        if candidates:
            for candidate in candidates.split("|"):
                if candidate:
                    candidate_counter[candidate] += 1

    total_count = len(rows)
    risk_on_count = market_counter.get("Risk-On", 0)
    risk_off_count = market_counter.get("Risk-Off", 0)
    neutral_count = market_counter.get("Neutral", 0)

    if sector_counter:
        top_sector, top_sector_count = sector_counter.most_common(1)[0]
        top_sector_text = f"{top_sector} ({top_sector_count}회)"
    else:
        top_sector_text = "기록 없음"

    if candidate_counter:
        top_candidate, top_candidate_count = candidate_counter.most_common(1)[0]
        top_candidate_text = f"{top_candidate} ({top_candidate_count}회)"
    else:
        top_candidate_text = "기록 없음"

    return (
        "=== 최근 기록 요약 ===\n"
        f"총 기록 수: {total_count}\n"
        f"Risk-On: {risk_on_count}회\n"
        f"Risk-Off: {risk_off_count}회\n"
        f"Neutral: {neutral_count}회\n"
        f"가장 자주 나온 강한 섹터: {top_sector_text}\n"
        f"가장 자주 나온 대형주 후보: {top_candidate_text}"
    )


def format_candidate_scores(scored_candidates: list[dict]) -> str:
    if not scored_candidates:
        return "없음"

    lines = []
    for item in scored_candidates:
        reasons_text = ", ".join(item["reasons"]) if item["reasons"] else "사유없음"
        lines.append(f"- {item['stock']}: {item['score']}점 ({reasons_text})")
    return "\n".join(lines)


def format_candidate_scores_csv(scored_candidates: list[dict]) -> str:
    if not scored_candidates:
        return ""

    return "|".join(
        [f"{item['stock']}:{item['score']}" for item in scored_candidates]
    )
def format_candidate_signals_csv(scored_candidates: list[dict]) -> str:
    if not scored_candidates:
        return ""

    parts = []

    for item in scored_candidates:
        signal = classify_signal(item["score"])
        parts.append(f"{item['stock']}:{item['score']}:{signal}")

    return "|".join(parts)

def format_top_candidates(scored_candidates: list[dict], top_n: int = 3) -> str:
    if not scored_candidates:
        return "없음"

    lines = []
    top_items = scored_candidates[:top_n]

    for idx, item in enumerate(top_items, start=1):
        signal = classify_signal(item["score"])
        lines.append(f"{idx}. {item['stock']} ({item['score']}점, {signal})")

    return "\n".join(lines)

def make_trade_plan(scored_candidates: list[dict], stock_prices: dict[str, float]) -> list[dict]:
    plans = []

    for item in scored_candidates:
        stock = item["stock"]
        score = item["score"]
        signal = classify_signal(score)

        if signal == "제외":
            continue

        current_price = stock_prices.get(stock)
        if current_price is None:
            current_price = BASE_PRICE_MAP.get(stock)

        if current_price is None:
            continue

        entry_price = current_price
        target_price = round(current_price * 1.02, 2)
        stop_price = round(current_price * 0.99, 2)

        qty = calculate_position_size(entry_price)

        plans.append(
            {
                "stock": stock,
                "score": score,
                "signal": signal,
                "entry_price": entry_price,
                "target_price": target_price,
                "stop_price": stop_price,
                "quantity": qty,
            }
        )

    return plans

def format_trade_plans(trade_plans: list[dict]) -> str:
    if not trade_plans:
        return "없음"

    lines = []

    for plan in trade_plans:
        lines.append(
            f"- {plan['stock']} | 상태: {plan['signal']} | "
            f"진입가: {plan['entry_price']} | "
            f"목표가: {plan['target_price']} | "
            f"손절가: {plan['stop_price']} | "
            f"수량: {plan['quantity']}주"
        )

    return "\n".join(lines)

def format_orders(orders: list[dict]) -> str:

    if not orders:
        return "없음"

    lines = []

    for order in orders:
        lines.append(
            f"[ORDER] {order['symbol']} "
            f"{order['side']} "
            f"{order['quantity']}주 "
            f"@ {order['price']} "
            f"(TP {order['take_profit']} / SL {order['stop_loss']})"
        )

    return "\n".join(lines)

def generate_order_tickets(trade_plans: list[dict]) -> list[dict]:

    orders = []

    for plan in trade_plans:

        if plan["signal"] != "매매 후보":
            continue

        order = {
            "symbol": plan["stock"],
            "side": "BUY",
            "quantity": plan["quantity"],
            "price": plan["entry_price"],
            "stop_loss": plan["stop_price"],
            "take_profit": plan["target_price"],
            "strategy": "MOMENTUM",
        }

        orders.append(order)

    return orders

def calculate_position_size(price: float) -> int:
    position_capital = TOTAL_CAPITAL * POSITION_RATIO

    qty = int(position_capital // price)

    if qty < 1:
        qty = 1

    return qty

def classify_signal(score: int) -> str:
    if score >= 6:
        return "매매 후보"
    if score >= 4:
        return "관찰"
    return "제외"

def parse_market_data(text: str) -> dict:
    kospi = extract_percent("코스피", text)
    kosdaq = extract_percent("코스닥", text)
    up_count = extract_int("상승종목수", text)
    down_count = extract_int("하락종목수", text)
    sectors = extract_words("강한섹터", text)
    leaders = extract_words("거래대금상위", text)
    stock_prices = extract_stock_prices("종목현재가", text)
    foreign_flow = detect_flow_keyword(text, "외국인")
    institution_flow = detect_flow_keyword(text, "기관")

    return {
        "kospi": kospi,
        "kosdaq": kosdaq,
        "up_count": up_count,
        "down_count": down_count,
        "sectors": sectors,
        "leaders": leaders,
        "stock_prices": stock_prices,
        "foreign_flow": foreign_flow,
        "institution_flow": institution_flow,
    }

def run_analysis(execute: bool = False) -> dict:
    text = read_market_file("data/market.txt")
    market = parse_market_data(text)

    market_status = classify_market(
        market["kospi"],
        market["kosdaq"],
        market["up_count"],
        market["down_count"],
    )

    bigcap_candidates = find_bigcap_candidates(
        market["leaders"],
        BIGCAP_WATCHLIST,
    )

    scored_candidates = score_candidates(
        candidates=bigcap_candidates,
        market_status=market_status,
        sectors=market["sectors"],
        foreign_flow=market["foreign_flow"],
        leaders=market["leaders"],
    )

    trade_plans = make_trade_plan(scored_candidates, market["stock_prices"])
    raw_orders = generate_order_tickets(trade_plans)
    approved_orders = filter_orders_by_risk(raw_orders, TOTAL_CAPITAL)

    if execute:
        trades = execute_orders(approved_orders)
        save_trade_log(trades)
    print("\n=== PAPER TRADING RESULT ===")
    print(trades)

    summary = make_summary(
        market_status=market_status,
        sectors=market["sectors"],
        leaders=market["leaders"],
        candidates=bigcap_candidates,
    )

    signal_lines = []
    for item in scored_candidates:
        signal = classify_signal(item["score"])
        signal_lines.append(f"- {item['stock']}: {item['score']}점 → {signal}")

    signal_text = "\n".join(signal_lines) if signal_lines else "없음"
    top_candidates_text = format_top_candidates(scored_candidates, top_n=3)

    report_text = f"""
=== 시장 분석 결과 ===
날짜: {date.today().isoformat()}
코스피: {market['kospi']}%
코스닥: {market['kosdaq']}%
상승종목수: {market['up_count']}
하락종목수: {market['down_count']}
시장 상태: {market_status}
강한 섹터: {', '.join(market['sectors']) if market['sectors'] else '없음'}
리더 종목: {', '.join(market['leaders']) if market['leaders'] else '없음'}
오늘 대형주 후보: {', '.join(bigcap_candidates) if bigcap_candidates else '없음'}
외국인 수급: {market['foreign_flow']}
기관 수급: {market['institution_flow']}
한 줄 요약: {summary}

=== 오늘 후보 점수 ===
{format_candidate_scores(scored_candidates)}

=== 오늘 매매 판단 ===
{signal_text}

=== 오늘 최종 후보 TOP 3 ===
{top_candidates_text}

=== 매매 계획 ===
{format_trade_plans(trade_plans)}

=== 주문 티켓 ===
{format_orders(approved_orders)}
""".strip()

    print(report_text)

    save_text_report("reports/summary.txt", report_text)

    csv_row = {
        "date": date.today().isoformat(),
        "kospi": market["kospi"],
        "kosdaq": market["kosdaq"],
        "up_count": market["up_count"],
        "down_count": market["down_count"],
        "market_status": market_status,
        "sectors": "|".join(market["sectors"]),
        "leaders": "|".join(market["leaders"]),
        "bigcap_candidates": "|".join(bigcap_candidates),
        "candidate_scores": format_candidate_scores_csv(scored_candidates),
        "candidate_signals": format_candidate_signals_csv(scored_candidates),
        "foreign_flow": market["foreign_flow"],
        "institution_flow": market["institution_flow"],
        "summary": summary,
        print("test")
    }

    append_csv_row("reports/history.csv", csv_row)

    history_rows = read_history("reports/history.csv")
    history_summary = summarize_history(history_rows)
    print()
    print(history_summary)
    save_text_report("reports/history_summary.txt", history_summary)

    return {
        "market_status": market_status,
        "bigcap_candidates": bigcap_candidates,
        "scored_candidates": scored_candidates,
        "trade_plans": trade_plans,
        "orders": approved_orders,
        "summary": summary,
        "report_text": report_text,
    }


def main() -> None:
    run_analysis(execute=True)


if __name__ == "__main__":
    main()