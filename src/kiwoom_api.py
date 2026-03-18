from pykiwoom.kiwoom import Kiwoom


class KiwoomTrader:

    def __init__(self):

        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect()

        print("키움 로그인 완료")

    def buy(self, code, qty, price):

        self.kiwoom.SendOrder(
            "자동매수",
            "0101",
            "계좌번호",
            1,
            code,
            qty,
            price,
            "00",
            "",
        )

    def sell(self, code, qty, price):

        self.kiwoom.SendOrder(
            "자동매도",
            "0101",
            "계좌번호",
            2,
            code,
            qty,
            price,
            "00",
            "",
        )