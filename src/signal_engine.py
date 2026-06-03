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

    if trade_strength >= BUY_TRADE_STRENGTH:
        reasons.append(f"체결강도 {BUY_TRADE_STRENGTH}% 이상")

    if trade_strength >= STRONG_BUY_TRADE_STRENGTH:
        reasons.append(f"강한 체결강도 {STRONG_BUY_TRADE_STRENGTH}% 이상")

    if foreign_flow == "매수":
        reasons.append("외국인 매수")

    if broker_flow == "매수우위":
        reasons.append("거래원 매수우위")

    is_buy_signal = (
        trade_strength >= BUY_TRADE_STRENGTH
        and foreign_flow == "매수"
        and broker_flow == "매수우위"
    )

    if is_buy_signal and trade_strength >= STRONG_BUY_TRADE_STRENGTH:
        signal = "STRONG_BUY"
    elif is_buy_signal:
        signal = "BUY"
    else:
        signal = "WAIT"

    return {
        "stock": stock["stock"],
        "signal": signal,
        "reasons": reasons,
        "trade_strength": trade_strength,
        "foreign_flow": foreign_flow,
        "broker_flow": broker_flow,
    }


def make_sell_signal(position: dict) -> dict:
    reasons = []

    trade_strength = position.get("trade_strength", 0)
    profit_rate = position.get("profit_rate", 0)
    foreign_flow = position.get("foreign_flow", "중립")
    broker_flow = position.get("broker_flow", "중립")

    if trade_strength < SELL_TRADE_STRENGTH:
        reasons.append(f"체결강도 {SELL_TRADE_STRENGTH}% 미만 약화")

    if trade_strength < STRONG_SELL_TRADE_STRENGTH:
        reasons.append(f"강한 매도우위 체결강도 {STRONG_SELL_TRADE_STRENGTH}% 미만")

    if foreign_flow == "매도":
        reasons.append("외국인 매도 전환")

    if broker_flow == "매도우위":
        reasons.append("거래원 매도우위")

    if profit_rate <= STOP_LOSS_RATE:
        reasons.append(f"손절 기준 {STOP_LOSS_RATE}% 도달")

    if profit_rate >= TAKE_PROFIT_RATE:
        reasons.append(f"익절 기준 {TAKE_PROFIT_RATE}% 도달")

    is_sell_signal = (
        trade_strength < SELL_TRADE_STRENGTH
        or foreign_flow == "매도"
        or broker_flow == "매도우위"
        or profit_rate <= STOP_LOSS_RATE
        or profit_rate >= TAKE_PROFIT_RATE
    )

    if is_sell_signal and trade_strength < STRONG_SELL_TRADE_STRENGTH:
        signal = "STRONG_SELL"
    elif is_sell_signal:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "stock": position["stock"],
        "signal": signal,
        "reasons": reasons,
        "trade_strength": trade_strength,
        "profit_rate": profit_rate,
        "foreign_flow": foreign_flow,
        "broker_flow": broker_flow,
    }