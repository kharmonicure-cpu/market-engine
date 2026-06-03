import json
from datetime import date
from pathlib import Path


ALERT_STATE_FILE = "reports/alert_state.json"


def load_alert_state(file_path: str = ALERT_STATE_FILE) -> dict:
    path = Path(file_path)

    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"[ALERT STATE] 파일 형식 오류, 새로 시작합니다: {file_path}")
        return {}


def save_alert_state(state: dict, file_path: str = ALERT_STATE_FILE) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def make_alert_key(stock: str, signal: str) -> str:
    return f"{stock}:{signal}"


def was_alert_sent(stock: str, signal: str, state: dict) -> bool:
    key = make_alert_key(stock, signal)
    return key in state


def mark_alert_sent(stock: str, signal: str, state: dict) -> dict:
    key = make_alert_key(stock, signal)
    state[key] = date.today().isoformat()
    return state

def reset_alert_state(file_path: str = ALERT_STATE_FILE) -> None:
    path = Path(file_path)

    if path.exists():
        path.unlink()
        print(f"[ALERT STATE] 알람 상태 파일 삭제 완료: {file_path}")
    else:
        print(f"[ALERT STATE] 삭제할 알람 상태 파일 없음: {file_path}")