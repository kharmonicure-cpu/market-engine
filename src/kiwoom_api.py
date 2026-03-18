from pykiwoom.kiwoom import Kiwoom


class KiwoomTrader:
    def __init__(self):
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect()
        print("키움 로그인 완료")

        accounts = self.kiwoom.GetLoginInfo("ACCNO")
        print("계좌목록:", accounts)

        if isinstance(accounts, str):
            accounts = accounts.split(";")

        self.account = [acc for acc in accounts if acc.strip()][0]
        print("사용 계좌:", self.account)

    def buy(self, code, qty, price):
        code = str(code)
        qty = int(qty)
        price = int(price)

        print(f"[매수] 계좌={self.account}, 종목코드={code}, 수량={qty}, 가격={price}")

        result = self.kiwoom.SendOrder(
            "자동매수",
            "0101",
            self.account,
            1,
            code,
            qty,
            price,
            "00",
            "",
        )
        print("SendOrder result:", result)
        return result

    def sell(self, code, qty, price):
        code = str(code)
        qty = int(qty)
        price = int(price)

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