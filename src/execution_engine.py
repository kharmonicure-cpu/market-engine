from src.kiwoom_api import KiwoomTrader

trader = KiwoomTrader()


def execute_orders(orders):

    results = []

    for order in orders:

        symbol = order["symbol"]
        qty = order["quantity"]
        price = order["price"]

        trader.buy(symbol, qty, price)

        results.append(order)

    return results

def execute_orders(orders: list[dict]):

    if not orders:
        print("실행할 주문 없음")
        return

    print("\n=== 주문 실행 ===")

    for order in orders:

        symbol = order["symbol"]
        qty = order["quantity"]
        price = order["price"]

        print(
            f"주문 실행: {symbol} "
            f"{qty}주 "
            f"@ {price}"
        )