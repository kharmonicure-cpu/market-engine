from pathlib import Path
import csv
from datetime import datetime


INITIAL_CAPITAL = 4_400_000


def load_account():

    path = Path("data/paper_account.csv")

    if not path.exists():

        return {
            "cash": INITIAL_CAPITAL,
            "positions": {},
        }

    with path.open("r", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        cash = INITIAL_CAPITAL
        positions = {}

        for row in reader:

            if row["type"] == "CASH":
                cash = float(row["value"])

            if row["type"] == "POSITION":

                positions[row["symbol"]] = {
                    "quantity": int(row["quantity"]),
                    "price": float(row["price"]),
                }

        return {
            "cash": cash,
            "positions": positions,
        }


def save_account(account):

    path = Path("data/paper_account.csv")
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as f:

        writer = csv.writer(f)

        writer.writerow(["type", "symbol", "quantity", "price", "value"])

        writer.writerow(["CASH", "", "", "", account["cash"]])

        for symbol, pos in account["positions"].items():

            writer.writerow(
                [
                    "POSITION",
                    symbol,
                    pos["quantity"],
                    pos["price"],
                    "",
                ]
            )

def save_trade_log(trades):

    path = Path("reports/paper_trades.csv")
    path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = path.exists()

    with path.open("a", encoding="utf-8", newline="") as f:

        fieldnames = ["time", "symbol", "qty", "price", "cost"]

        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerows(trades)

def execute_paper_orders(orders):

    account = load_account()

    cash = account["cash"]
    positions = account["positions"]

    trade_logs = []

    for order in orders:

        symbol = order["symbol"]
        qty = order["quantity"]
        price = order["price"]

        cost = qty * price

        if cost > cash:
            continue

        cash -= cost

        positions[symbol] = {
            "quantity": qty,
            "price": price,
        }

        trade_logs.append(
            {
                "time": datetime.now().isoformat(),
                "symbol": symbol,
                "qty": qty,
                "price": price,
                "cost": cost,
            }
        )

    account["cash"] = cash
    account["positions"] = positions

    save_account(account)

    return trade_logs