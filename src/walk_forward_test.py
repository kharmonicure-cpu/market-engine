import pandas as pd

from backtest_multi_data import (
    download_price_data,
    add_signals,
    run_backtest_for_stock,
    calculate_sharpe_ratio,
)

TICKER = "005930.KS"

TRAIN_YEARS = 3
TEST_YEARS = 1

TAKE_PROFIT_RANGE = [0.01, 0.015, 0.02, 0.025]
STOP_LOSS_RANGE = [-0.005, -0.01, -0.015]


def find_best_strategy(df):

    best_sharpe = -999
    best_tp = None
    best_sl = None

    for tp in TAKE_PROFIT_RANGE:
        for sl in STOP_LOSS_RANGE:

            trades = run_backtest_for_stock(
                df,
                "train",
                take_profit=tp,
                stop_loss=sl,
            )

            sharpe = calculate_sharpe_ratio(trades)

            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_tp = tp
                best_sl = sl

    return best_tp, best_sl, best_sharpe


def run_walk_forward():

    price_df = download_price_data(TICKER, "2018-01-01")

    price_df["year"] = pd.to_datetime(price_df["date"]).dt.year

    years = sorted(price_df["year"].unique())

    results = []

    for i in range(len(years) - (TRAIN_YEARS + TEST_YEARS) + 1):

        train_years = years[i : i + TRAIN_YEARS]
        test_years = years[i + TRAIN_YEARS : i + TRAIN_YEARS + TEST_YEARS]

        train_df = price_df[price_df["year"].isin(train_years)]
        test_df = price_df[price_df["year"].isin(test_years)]

        train_df = add_signals(train_df)
        test_df = add_signals(test_df)

        tp, sl, train_sharpe = find_best_strategy(train_df)

        test_trades = run_backtest_for_stock(
            test_df,
            "test",
            take_profit=tp,
            stop_loss=sl,
        )

        test_sharpe = calculate_sharpe_ratio(test_trades)

        results.append(
            {
                "train_years": train_years,
                "test_years": test_years,
                "take_profit": tp,
                "stop_loss": sl,
                "train_sharpe": train_sharpe,
                "test_sharpe": test_sharpe,
            }
        )

    results_df = pd.DataFrame(results)

    print("=== Walk Forward Test ===")
    print(results_df)

    results_df.to_csv("reports/walk_forward_results.csv", index=False)


if __name__ == "__main__":
    run_walk_forward()