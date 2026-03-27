from queue import Queue, Empty
from pykiwoom.kiwoom import Kiwoom
from src.config import MODE, MOCK_ACCOUNT, REAL_ACCOUNT


CHEJAN_FID_MAP = {
    "9001": "symbol",      # 종목코드
    "302": "name",         # 종목명
    "911": "qty",          # 체결수량
    "910": "price",        # 체결가
    "913": "status",       # 주문상태
    "9203": "order_no",    # 주문번호
}


class KiwoomTrader:
    def __init__(self):
        self.trades = []
        self.chejan_events = []

        if MODE == "paper":
            self.kiwoom = None
            self.account = None
            self.chejan_queue = None
            print("PAPER 모드: 키움 로그인 생략")
            return

        self.chejan_queue = Queue()
        self.kiwoom = Kiwoom(chejan_dqueue=self.chejan_queue)
        self.kiwoom.CommConnect(block=True)
        print("키움 로그인 완료")

        try:
            self.kiwoom.dynamicCall(
                "KOA_Functions(QString, QString)",
                "ShowAccountWindow",
                ""
            )
        except AttributeError:
            self.kiwoom.ocx.dynamicCall(
                "KOA_Functions(QString, QString)",
                "ShowAccountWindow",
                ""
            )

        accounts = self.kiwoom.GetLoginInfo("ACCNO")
        if isinstance(accounts, str):
            accounts = accounts.split(";")

        accounts = [acc.strip() for acc in accounts if acc.strip()]
        print("계좌목록:", accounts)
        print("현재 MODE:", MODE)

        if MODE == "mock":
            self.account = MOCK_ACCOUNT
        elif MODE == "real":
            self.account = REAL_ACCOUNT
        else:
            self.account = None

        print("선택된 계좌:", self.account)

        if self.account not in accounts:
            raise ValueError(
                f"설정한 계좌({self.account})가 로그인된 계좌목록에 없습니다. "
                f"현재 계좌목록: {accounts}"
            )

        print("사용 계좌:", self.account)

    def buy(self, code, qty, price):
        code = str(code)
        qty = int(qty)

        if MODE == "paper":
            print(f"[PAPER 매수] 종목코드={code}, 수량={qty}, 가격={price}")
            return "PAPER"

        print(f"[매수] 계좌={self.account}, 종목코드={code}, 수량={qty}, 주문구분=시장가")

        result = self.kiwoom.SendOrder(
            "자동매수",
            "0101",
            self.account,
            1,
            code,
            qty,
            0,
            "03",
            "",
        )
        print("SendOrder result:", result)
        return result

    def sell(self, code, qty, price):
        code = str(code)
        qty = int(qty)
        price = int(price)

        if MODE == "paper":
            print(f"[PAPER 매도] 종목코드={code}, 수량={qty}, 가격={price}")
            return "PAPER"

        print(f"[매도] 계좌={self.account}, 종목코드={code}, 수량={qty}, 가격={price}")

        result = self.kiwoom.SendOrder(
            "자동매도",
            "0101",
            self.account,
            2,
            code,
            qty,
            price,
            "00",
            "",
        )
        print("SendOrder result:", result)
        return result

    def drain_chejan_queue(self):
        if self.chejan_queue is None:
            return []

        drained = []

        while True:
            try:
                raw = self.chejan_queue.get_nowait()
            except Empty:
                break

            self.chejan_events.append(raw)
            drained.append(raw)

            print("\n=== CHEJAN QUEUE RAW ===")
            print(raw)

            gubun = str(raw.get("gubun", "")).strip()

            # 0: 주문접수/체결, 1: 잔고변경
            if gubun != "0":
                continue

            trade = {
                "symbol": str(raw.get("9001", "")).strip(),
                "name": str(raw.get("302", "")).strip(),
                "qty": str(raw.get("911", "")).strip(),
                "price": str(raw.get("910", "")).strip(),
                "status": str(raw.get("913", "")).strip(),
                "order_no": str(raw.get("9203", "")).strip(),
            }

            print("\n=== 체결/주문 이벤트 파싱 ===")
            print(trade)

            self.trades.append(trade)

        return drained

    def get_chejan_trades(self):
        return self.trades

    def get_chejan_events(self):
        return self.chejan_events