import csv
from pathlib import Path


BUY_SCORE_THRESHOLD = 6
TAKE_PROFIT_RATIO = 1.02
STOP_LOSS_RATIO = 0.99


def load_backtest_data(file_path: str) -> list[dict]:
    path = Path(file_path)

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    return rows


def group_by_stock(rows: list[dict]) -> dict[str, list[dict]]:
    grouped = {}

    for row in rows:
        stock = row["stock"]

        if stock not in grouped:
            grouped[stock] = []

        grouped[stock].append(
            {
                "date": row["date"],
                "stock": stock,
                "price": float(row["price"]),
                "score": int(row["score"]),
            }
        )

    return grouped


def run_backtest(rows: list[dict]) -> list[dict]:
    grouped = group_by_stock(rows)
    results = []

    for stock, stock_rows in grouped.items():
        stock_rows.sort(key=lambda x: x["date"])

        for i in range(len(stock_rows) - 1):
            current_row = stock_rows[i]
            next_row = stock_rows[i + 1]

            score = current_row["score"]
            entry_price = current_row["price"]

            if score < BUY_SCORE_THRESHOLD:
                continue

            target_price = entry_price * TAKE_PROFIT_RATIO
            stop_price = entry_price * STOP_LOSS_RATIO
            next_price = next_row["price"]

            if next_price >= target_price:
                outcome = "WIN"
                pnl_pct = 2.0
            elif next_price <= stop_price:
                outcome = "LOSS"
                pnl_pct = -1.0
            else:
                outcome = "HOLD"
                pnl_pct = round(((next_price - entry_price) / entry_price) * 100, 2)

            results.append(
                {
                    "stock": stock,
                    "entry_date": current_row["date"],
                    "exit_date": next_row["date"],
                    "entry_price": entry_price,
                    "exit_price": next_price,
                    "score": score,
                    "outcome": outcome,
                    "pnl_pct": pnl_pct,
                }
            )

    return results


def summarize_results(results: list[dict]) -> str:
    if not results:
        return "백테스트 결과가 없습니다."

    total = len(results)
    wins = sum(1 for r in results if r["outcome"] == "WIN")
    losses = sum(1 for r in results if r["outcome"] == "LOSS")
    holds = sum(1 for r in results if r["outcome"] == "HOLD")

    avg_pnl = round(sum(r["pnl_pct"] for r in results) / total, 2)
    win_rate = round((wins / total) * 100, 2)

    return (
        "=== 백테스트 요약 ===\n"
        f"총 거래 수: {total}\n"
        f"승리: {wins}\n"
        f"손실: {losses}\n"
        f"보합/기타: {holds}\n"
        f"승률: {win_rate}%\n"
        f"평균 손익률: {avg_pnl}%"
    )


def save_backtest_results(file_path: str, results: list[dict]) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "stock",
        "entry_date",
        "exit_date",
        "entry_price",
        "exit_price",
        "score",
        "outcome",
        "pnl_pct",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def main() -> None:
    rows = load_backtest_data("data/backtest_data.csv")
    results = run_backtest(rows)
    summary = summarize_results(results)

    stock_summary = summarize_by_stock(results)

    score_summary = summarize_by_score(results)

    save_backtest_results("reports/backtest_results.csv", results)

    print(summary)
    print(stock_summary)
    print(score_summary)
    
    print("\n상세 결과가 reports/backtest_results.csv 에 저장되었습니다.")

from collections import defaultdict


def summarize_by_stock(results: list[dict]) -> str:

    grouped = defaultdict(list)

    for r in results:
        grouped[r["stock"]].append(r)

    lines = ["\n=== 종목별 성과 ==="]

    for stock, trades in grouped.items():

        total = len(trades)
        wins = sum(1 for t in trades if t["outcome"] == "WIN")
        avg_pnl = round(sum(t["pnl_pct"] for t in trades) / total, 2)
        win_rate = round((wins / total) * 100, 2)

        lines.append("")
        lines.append(stock)
        lines.append(f"거래수: {total}")
        lines.append(f"승률: {win_rate}%")
        lines.append(f"평균 수익률: {avg_pnl}%")

    return "\n".join(lines)

def summarize_by_score(results: list[dict]) -> str:

    grouped = defaultdict(list)

    for r in results:
        grouped[r["score"]].append(r)

    lines = ["\n=== 점수별 성과 ==="]

    for score, trades in sorted(grouped.items()):

        total = len(trades)
        wins = sum(1 for t in trades if t["outcome"] == "WIN")
        avg_pnl = round(sum(t["pnl_pct"] for t in trades) / total, 2)
        win_rate = round((wins / total) * 100, 2)

        lines.append("")
        lines.append(f"score {score}")
        lines.append(f"거래수: {total}")
        lines.append(f"승률: {win_rate}%")
        lines.append(f"평균 수익률: {avg_pnl}%")

    return "\n".join(lines)

if __name__ == "__main__":
    main()