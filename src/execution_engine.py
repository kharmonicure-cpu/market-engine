import csv
import os
import time
from datetime import datetime

import pythoncom
from PyQt5.QtWidgets import QApplication

from src.config import MODE
from src.kiwoom_api import KiwoomTrader

trader = None


def get_trader():
    global trader
    if trader is None:
        trader = KiwoomTrader()
    return trader


def execute_orders(orders):
    if not orders:
        print("실행할 주문 없음")
        return []

    print("\n=== 주문 실행 ===")
    results = []

    current_trader = get_trader() if MODE != "paper" else None

    for order in orders:
        symbol = order["symbol"]
        name = order.get("name", symbol)
        qty = int(order["quantity"])
        price = int(order["price"])

        print(f"주문 실행: {name} ({symbol}) {qty}주 @ {price}")

        if MODE == "paper":
            result = "PAPER"
            print("[PAPER] 실제 주문은 전송하지 않음")
        else:
            result = current_trader.buy(symbol, qty, price)

        results.append({
            "symbol": symbol,
            "name": name,
            "price": price,
            "quantity": qty,
            "status": result,
        })

        # 주문 직후 이벤트 처리
        if MODE != "paper":
            for _ in range(5):
                pythoncom.PumpWaitingMessages()
                time.sleep(0.1)

    if MODE != "paper":
        print("\n=== 체결 이벤트 대기 (10초) ===")
        start = time.time()

        while time.time() - start < 10:
            pythoncom.PumpWaitingMessages()
            time.sleep(0.1)

            print("\n=== 수신된 체결/잔고 이벤트 수 ===")
            print(len(current_trader.get_chejan_events()))

            print("\n=== 수신된 체결 데이터 ===")
            print(current_trader.get_chejan_trades())

            print("\n=== 수신된 서버 메시지 수 ===")
            print(len(current_trader.get_msg_events()))

            if current_trader.get_msg_events():
                print(current_trader.get_msg_events()[-1])

            if current_trader.get_chejan_events():
                break

    return results


def save_trade_log(trades, filename="trade_log.csv"):
    if not trades:
        print("저장할 거래 로그가 없습니다.")
        return

    file_exists = os.path.exists(filename)

    with open(filename, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["timestamp", "symbol", "name", "price", "qty", "status"])

        for trade in trades:
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                trade.get("symbol", ""),
                trade.get("name", ""),
                trade.get("price", ""),
                trade.get("qty", trade.get("quantity", "")),
                trade.get("status", "")
            ])

    print(f"거래 로그 저장 완료: {filename}")