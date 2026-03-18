import csv
import os
from datetime import datetime
from src.kiwoom_api import KiwoomTrader

trader = KiwoomTrader()


def save_trade_log(trades, filename="trade_log.csv"):
    if not trades:
        print("저장할 거래 로그가 없습니다.")
        return

    file_exists = os.path.exists(filename)

    with open(filename, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["timestamp", "symbol", "name", "price", "qty"])

        for trade in trades:
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                trade.get("symbol", ""),
                trade.get("name", ""),
                trade.get("price", ""),
                trade.get("qty", trade.get("quantity", ""))
            ])

    print(f"거래 로그 저장 완료: {filename}")


def execute_orders(orders):
    if not orders:
        print("실행할 주문 없음")
        return []

    print("\n=== 주문 실행 ===")
    results = []

    for order in orders:
        symbol = order["symbol"]          # 005930 같은 코드
        name = order.get("name", symbol)  # 삼성전자 같은 이름
        qty = int(order["quantity"])
        price = int(order["price"])

        print(f"주문 실행: {name} {qty}주 @ {price}")
        trader.buy(symbol, qty, price)
        results.append(order)

    return results