BUY_TRADE_STRENGTH = 130
STRONG_BUY_TRADE_STRENGTH = 150
SELL_TRADE_STRENGTH = 100
STRONG_SELL_TRADE_STRENGTH = 90
STOP_LOSS_RATE = -3
TAKE_PROFIT_RATE = 5

def make_buy_signal(stock: dict) -> dict:
    reasons = []

    trade_strength = stock.get("trade_strength", 0)
    foreign_flow = stock.get("foreign_flow", "중립")
    broker_flow = stock.get("broker_flow", "중립")

    if trade_strength >= 130:
        reasons.append("체결강도 130% 이상")

    if foreign_flow == "매수":
        reasons.append("외국인 매수")

    if broker_flow == "매수우위":
        reasons.append("거래원 매수우위")

    is_buy_signal = (
        trade_strength >= 130
        and foreign_flow == "매수"
        and broker_flow == "매수우위"
    )

    return {
        "stock": stock["stock"],
        "signal": "BUY" if is_buy_signal else "WAIT",
        "reasons": reasons,
        "trade_strength": trade_strength,
        "foreign_flow": foreign_flow,
        "broker_flow": broker_flow,
    }


def make_sell_signal(position: dict) -> dict:
    reasons = []

    trade_strength = position.get("trade_strength", 0)
    profit_rate = position.get("profit_rate", 0)

    if trade_strength < 100:
        reasons.append("체결강도 100% 미만 약화")

    if profit_rate <= -3:
        reasons.append("손절 기준 도달")

    if profit_rate >= 5:
        reasons.append("익절 기준 도달")

    is_sell_signal = (
        trade_strength < 100
        or profit_rate <= -3
        or profit_rate >= 5
    )

    return {
        "stock": position["stock"],
        "signal": "SELL" if is_sell_signal else "HOLD",
        "reasons": reasons,
        "trade_strength": trade_strength,
        "profit_rate": profit_rate,
    }