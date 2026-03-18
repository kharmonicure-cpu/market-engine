MAX_POSITIONS = 3
MAX_DAILY_LOSS = 0.03
MAX_POSITION_RATIO = 0.2


def filter_orders_by_risk(orders: list[dict], capital: float) -> list[dict]:

    approved = []

    for order in orders:

        position_value = order["price"] * order["quantity"]

        if position_value > capital * MAX_POSITION_RATIO:
            continue

        approved.append(order)

        if len(approved) >= MAX_POSITIONS:
            break

    return approved