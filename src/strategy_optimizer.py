import pandas as pd

from backtest_multi_data import (
    download_price_data,
    add_signals,
    run_backtest_for_stock,
    calculate_sharpe_ratio,
)

TICKERS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
}

START_DATE = "2021-01-01"

TAKE_PROFIT_RANGE = [0.01, 0.015, 0.02, 0.025]
STOP_LOSS_RANGE = [-0.005, -0.01, -0.015]


def optimize_strategy():

    results = []

    for tp in TAKE_PROFIT_RANGE:
        for sl in STOP_LOSS_RANGE:

            all_trades = []

            for stock_name, ticker in TICKERS.items():

                price_df = download_price_data(ticker, START_DATE)
                signal_df = add_signals(price_df)

                trades_df = run_backtest_for_stock(
                    signal_df,
                    stock_name,
                    take_profit=tp,
                    stop_loss=sl,
                )

                all_trades.append(trades_df)

            merged = pd.concat(all_trades)

            sharpe = calculate_sharpe_ratio(merged)

            results.append(
                {
                    "take_profit": tp,
                    "stop_loss": sl,
                    "trades": len(merged),
                    "sharpe": sharpe,
                }
            )

    results_df = pd.DataFrame(results)

    best = results_df.sort_values("sharpe", ascending=False).iloc[0]

    print("=== 전략 최적화 결과 ===")
    print(results_df)

    print("\n=== BEST 전략 ===")
    print(best)

    results_df.to_csv("reports/strategy_optimization.csv", index=False)


if __name__ == "__main__":
    optimize_strategy()