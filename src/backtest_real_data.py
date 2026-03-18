from pathlib import Path
import yfinance as yf
import pandas as pd
from typing import Optional


TICKER = "005930.KS"   # 삼성전자
START_DATE = "2021-01-01"
END_DATE = None

BUY_THRESHOLD = 0.01      # 전일 대비 1% 이상 상승하면 진입
TAKE_PROFIT = 0.02        # 익절 +2%
STOP_LOSS = -0.01         # 손절 -1%


def download_price_data(ticker: str, start: str, end: Optional[str] = None) -> pd.DataFrame:
    df = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
    if df.empty:
        raise ValueError("가격 데이터를 가져오지 못했습니다.")

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


def run_backtest(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    trades: list[dict] = []

    for i in range(1, len(df) - 1):
        row = df.iloc[i]

        if not bool(row["buy_signal"]):
            continue

        entry_date = df.iloc[i + 1]["date"]
        entry_price = float(df.iloc[i + 1]["open"])

        target_price = round(entry_price * (1 + TAKE_PROFIT), 2)
        stop_price = round(entry_price * (1 + STOP_LOSS), 2)

        # 단순 버전: 다음 날 고가/저가로 익절/손절 판정
        exit_date = df.iloc[i + 1]["date"]
        high_price = float(df.iloc[i + 1]["high"])
        low_price = float(df.iloc[i + 1]["low"])
        close_price = float(df.iloc[i + 1]["close"])

        if high_price >= target_price:
            exit_price = target_price
            outcome = "WIN"
        elif low_price <= stop_price:
            exit_price = stop_price
            outcome = "LOSS"
        else:
            exit_price = close_price
            outcome = "HOLD"

        pnl_pct = round((exit_price - entry_price) / entry_price * 100, 2)

        trades.append(
            {
                "signal_date": row["date"],
                "entry_date": entry_date,
                "exit_date": exit_date,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "target_price": target_price,
                "stop_price": stop_price,
                "outcome": outcome,
                "pnl_pct": pnl_pct,
            }
        )

    trades_df = pd.DataFrame(trades)

    if trades_df.empty:
        summary_df = pd.DataFrame(
            [{"total_trades": 0, "win_rate": 0.0, "avg_pnl_pct": 0.0, "cum_pnl_pct": 0.0}]
        )
        return trades_df, summary_df

    total_trades = len(trades_df)
    win_rate = round((trades_df["outcome"] == "WIN").mean() * 100, 2)
    avg_pnl_pct = round(trades_df["pnl_pct"].mean(), 2)
    cum_pnl_pct = round(trades_df["pnl_pct"].sum(), 2)

    summary_df = pd.DataFrame(
        [
            {
                "total_trades": total_trades,
                "win_rate": win_rate,
                "avg_pnl_pct": avg_pnl_pct,
                "cum_pnl_pct": cum_pnl_pct,
            }
        ]
    )

    return trades_df, summary_df


def save_results(price_df: pd.DataFrame, trades_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    price_df.to_csv(reports_dir / "samsung_price_data.csv", index=False, encoding="utf-8-sig")
    trades_df.to_csv(reports_dir / "samsung_backtest_trades.csv", index=False, encoding="utf-8-sig")
    summary_df.to_csv(reports_dir / "samsung_backtest_summary.csv", index=False, encoding="utf-8-sig")


def main() -> None:
    price_df = download_price_data(TICKER, START_DATE, END_DATE)
    signal_df = add_signals(price_df)
    trades_df, summary_df = run_backtest(signal_df)
    save_results(signal_df, trades_df, summary_df)

    print("=== 삼성전자 실제 데이터 백테스트 완료 ===")
    print(summary_df.to_string(index=False))
    print("\n저장 파일:")
    print("- reports/samsung_price_data.csv")
    print("- reports/samsung_backtest_trades.csv")
    print("- reports/samsung_backtest_summary.csv")


if __name__ == "__main__":
    main()