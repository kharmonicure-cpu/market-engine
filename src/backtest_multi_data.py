from pathlib import Path
from typing import Optional
from collections import defaultdict

import yfinance as yf
import pandas as pd
import numpy as np

COMMISSION = 0.00015   # 수수료 (0.015%)
TAX = 0.0023           # 세금 (0.23%)
SLIPPAGE = 0.0005      # 슬리피지 (0.05%)


TICKERS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대차": "005380.KS",
    "한화시스템": "272210.KS",
}

START_DATE = "2021-01-01"
END_DATE: Optional[str] = None

BUY_THRESHOLD = 0.01   # 전일 대비 1% 이상 상승
TAKE_PROFIT = 0.02     # +2%
STOP_LOSS = -0.01      # -1%


def download_price_data(
    ticker: str,
    start: str,
    end: Optional[str] = None,
) -> pd.DataFrame:
    df = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)

    if df.empty:
        raise ValueError(f"{ticker} 가격 데이터를 가져오지 못했습니다.")

    df = df.reset_index()
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
    df.columns = ["date", "open", "high", "low", "close", "volume"]
    return df


def add_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["prev_close"] = df["close"].shift(1)
    df["daily_return"] = (df["close"] - df["prev_close"]) / df["prev_close"]
    df["buy_signal"] = df["daily_return"] >= BUY_THRESHOLD
    return df


def run_backtest_for_stock(
    df: pd.DataFrame,
    stock_name: str,
    take_profit: float = 0.02,
    stop_loss: float = -0.01,
):
    trades: list[dict] = []

    for i in range(1, len(df) - 1):
        row = df.iloc[i]

        if not bool(row["buy_signal"]):
            continue

        next_row = df.iloc[i + 1]

        entry_date = next_row["date"]
        entry_price = float(next_row["open"])
        target_price = round(entry_price * (1 + take_profit), 2)
        stop_price = round(entry_price * (1 + stop_loss), 2)    

        high_price = float(next_row["high"])
        low_price = float(next_row["low"])
        close_price = float(next_row["close"])

        if high_price >= target_price:
            exit_price = target_price
            outcome = "WIN"
        elif low_price <= stop_price:
            exit_price = stop_price
            outcome = "LOSS"
        else:
            exit_price = close_price
            outcome = "HOLD"

        raw_return = (exit_price - entry_price) / entry_price

        cost = COMMISSION + SLIPPAGE
        tax_cost = TAX if raw_return > 0 else 0

        net_return = raw_return - cost - tax_cost

        pnl_pct = round(net_return * 100, 2)

        trades.append(
            {
                "stock": stock_name,
                "signal_date": row["date"],
                "entry_date": entry_date,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "target_price": target_price,
                "stop_price": stop_price,
                "outcome": outcome,
                "pnl_pct": pnl_pct,
            }
        )

    return pd.DataFrame(trades)


def summarize_results(results_df: pd.DataFrame) -> str:
    if results_df.empty:
        return "백테스트 결과가 없습니다."

    total = len(results_df)
    wins = int((results_df["outcome"] == "WIN").sum())
    losses = int((results_df["outcome"] == "LOSS").sum())
    holds = int((results_df["outcome"] == "HOLD").sum())

    win_rate = round(wins / total * 100, 2)
    avg_pnl = round(results_df["pnl_pct"].mean(), 2)
    cum_pnl = round(results_df["pnl_pct"].sum(), 2)

    return (
        "=== 멀티 종목 백테스트 요약 ===\n"
        f"총 거래 수: {total}\n"
        f"승리: {wins}\n"
        f"손실: {losses}\n"
        f"보합/기타: {holds}\n"
        f"승률: {win_rate}%\n"
        f"평균 손익률: {avg_pnl}%\n"
        f"누적 손익률 합계: {cum_pnl}%"
    )

def calculate_equity_curve(results_df: pd.DataFrame) -> pd.DataFrame:

    if results_df.empty:
        return pd.DataFrame()

    equity = 100
    equity_curve = []

    for _, row in results_df.iterrows():

        pnl = row["pnl_pct"] / 100

        equity = equity * (1 + pnl)

        equity_curve.append(
            {
                "date": row["entry_date"],
                "equity": equity
            }
        )

    return pd.DataFrame(equity_curve)

def calculate_max_drawdown(equity_df: pd.DataFrame) -> float:

    if equity_df.empty:
        return 0.0

    peak = equity_df["equity"].iloc[0]
    max_dd = 0

    for equity in equity_df["equity"]:

        if equity > peak:
            peak = equity

        drawdown = (equity - peak) / peak

        if drawdown < max_dd:
            max_dd = drawdown

    return round(max_dd * 100, 2)

def calculate_sharpe_ratio(results_df: pd.DataFrame) -> float:

    if results_df.empty:
        return 0.0

    returns = results_df["pnl_pct"] / 100

    avg_return = returns.mean()
    std_return = returns.std()

    if std_return == 0:
        return 0.0

    sharpe = avg_return / std_return

    return round(sharpe, 3)

def summarize_by_stock(results_df: pd.DataFrame) -> str:
    if results_df.empty:
        return "\n=== 종목별 성과 ===\n결과 없음"

    lines = ["\n=== 종목별 성과 ==="]

    grouped = results_df.groupby("stock")

    for stock, group in grouped:
        total = len(group)
        wins = int((group["outcome"] == "WIN").sum())
        win_rate = round(wins / total * 100, 2)
        avg_pnl = round(group["pnl_pct"].mean(), 2)

        lines.append("")
        lines.append(stock)
        lines.append(f"거래수: {total}")
        lines.append(f"승률: {win_rate}%")
        lines.append(f"평균 손익률: {avg_pnl}%")

    return "\n".join(lines)


def save_results(
    price_data_map: dict[str, pd.DataFrame],
    results_df: pd.DataFrame,
) -> None:
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    for stock_name, df in price_data_map.items():
        file_name = f"{stock_name}_price_data.csv"
        df.to_csv(reports_dir / file_name, index=False, encoding="utf-8-sig")

    results_df.to_csv(
        reports_dir / "multi_backtest_results.csv",
        index=False,
        encoding="utf-8-sig",
    )


def main() -> None:
    all_results = []
    price_data_map: dict[str, pd.DataFrame] = {}

    for stock_name, ticker in TICKERS.items():
        print(f"{stock_name} 데이터 다운로드 중...")

        price_df = download_price_data(ticker, START_DATE, END_DATE)
        signal_df = add_signals(price_df)
        result_df = run_backtest_for_stock(signal_df, stock_name)

        price_data_map[stock_name] = signal_df
        all_results.append(result_df)

    if all_results:
        results_df = pd.concat(all_results, ignore_index=True)
    else:
        results_df = pd.DataFrame()

    save_results(price_data_map, results_df)

    summary_text = summarize_results(results_df)
    stock_summary_text = summarize_by_stock(results_df)

    equity_df = calculate_equity_curve(results_df)
    max_dd = calculate_max_drawdown(equity_df)
    sharpe = calculate_sharpe_ratio(results_df)

    print(summary_text)
    print(stock_summary_text)

    print("\n=== 계좌 성과 ===")
    print(f"최종 Equity: {round(equity_df['equity'].iloc[-1],2)}")
    print(f"Max Drawdown: {max_dd}%")
    print(f"Sharpe Ratio: {sharpe}")

    print("\n저장 파일:")
    print("- reports/multi_backtest_results.csv")
    for stock_name in TICKERS.keys():
        print(f"- reports/{stock_name}_price_data.csv")


if __name__ == "__main__":
    main()