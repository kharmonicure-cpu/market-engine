import os
from typing import Optional


def is_true(value: Optional[str]) -> bool:
    return str(value).lower() == "true"


def check_trading_permission() -> bool:
    mode = os.getenv("MODE", "mock").lower()

    allow_trading = is_true(os.getenv("ALLOW_TRADING"))
    allow_real_trading = is_true(os.getenv("ALLOW_REAL_TRADING"))

    if mode == "mock":
        if not allow_trading:
            print("[SAFE MODE] Mock trading is blocked.")
            print("[SAFE MODE] Set ALLOW_TRADING=true to enable mock orders.")
            return False

        print("[SAFE MODE] Mock trading is allowed.")
        return True

    if mode == "real":
        if not allow_real_trading:
            print("[SAFE MODE] Real trading is blocked.")
            print("[SAFE MODE] Set ALLOW_REAL_TRADING=true only when you really want live trading.")
            return False

        print("[WARNING] Real trading is enabled.")
        return True

    print(f"[SAFE MODE] Unknown MODE: {mode}")
    print("[SAFE MODE] Trading is blocked.")
    return False