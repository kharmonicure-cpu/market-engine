import time
import csv
import sys
from pathlib import Path
from datetime import datetime

SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent

sys.path.append(str(SRC_DIR))
sys.path.append(str(ROOT_DIR))

from fetch_market import run_fetch_once
from main import run_analysis

def append_snapshot_csv(file_path: str, data: dict) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "timestamp",
        "kospi",
        "kosdaq",
        "up_count",
        "down_count",
        "strong_sectors",
        "leaders",
        "foreign_flow",
        "institution_flow",
    ]

    file_exists = path.exists()

    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                "timestamp": data["timestamp"],
                "kospi": data["kospi"],
                "kosdaq": data["kosdaq"],
                "up_count": data["up_count"],
                "down_count": data["down_count"],
                "strong_sectors": "|".join(data["strong_sectors"]),
                "leaders": "|".join(data["leaders"]),
                "foreign_flow": data["foreign_flow"],
                "institution_flow": data["institution_flow"],
            }
        )


def live_monitor_loop(interval_seconds: int = 5, max_cycles: int = 10) -> None:
    print(f"실시간 감시 시작: {interval_seconds}초 간격 / 총 {max_cycles}회")

    prev_data = None
    prev_analysis = None

    for cycle in range(1, max_cycles + 1):
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{now}] {cycle}회차 수집 시작")

        data = run_fetch_once()
        analysis_result = run_analysis()

        market_alerts = detect_market_changes(prev_data, data)
        signal_alerts = detect_signal_changes(prev_analysis, analysis_result)

        for alert in market_alerts:
            print(alert)

        for alert in signal_alerts:
            print(alert)

        append_snapshot_csv("reports/live_snapshots.csv", data)
        print(
            f"코스피 {data['kospi']}%, "
            f"코스닥 {data['kosdaq']}%, "
            f"리더 {', '.join(data['leaders'])}"
        )
        print(f"시장 상태: {analysis_result['market_status']}")
        print(f"후보 종목: {', '.join(analysis_result['bigcap_candidates']) if analysis_result['bigcap_candidates'] else '없음'}")

        prev_data = data
        prev_analysis = analysis_result
    
        if cycle < max_cycles:
            time.sleep(interval_seconds)

    print("\n실시간 감시 종료")

def detect_market_changes(prev_data: dict, new_data: dict):

    alerts = []

    # 코스피 변화
    if prev_data:
        prev_kospi = prev_data["kospi"]
        new_kospi = new_data["kospi"]

        if abs(new_kospi - prev_kospi) >= 0.3:
            alerts.append(
                f"[ALERT] 코스피 급변: {prev_kospi} → {new_kospi}"
            )

    # 리더 종목 변경
    if prev_data:
        if prev_data["leaders"] != new_data["leaders"]:
            alerts.append(
                f"[ALERT] 리더 종목 변경: "
                f"{prev_data['leaders']} → {new_data['leaders']}"
            )

    # 섹터 변경
    if prev_data:
        if prev_data["strong_sectors"] != new_data["strong_sectors"]:
            alerts.append(
                f"[ALERT] 강한 섹터 변경: "
                f"{prev_data['strong_sectors']} → {new_data['strong_sectors']}"
            )

    return alerts

def classify_signal(score: int) -> str:
    if score >= 6:
        return "매매 후보"
    if score >= 4:
        return "관찰"
    return "제외"

def detect_signal_changes(prev_analysis: dict | None, new_analysis: dict) -> list[str]:
    alerts = []

    if not prev_analysis:
        return alerts

    prev_scores = {}
    for item in prev_analysis.get("scored_candidates", []):
        prev_scores[item["stock"]] = item["score"]

    new_scores = {}
    for item in new_analysis.get("scored_candidates", []):
        new_scores[item["stock"]] = item["score"]

    all_stocks = set(prev_scores.keys()) | set(new_scores.keys())

    for stock in sorted(all_stocks):
        prev_score = prev_scores.get(stock)
        new_score = new_scores.get(stock)

        if prev_score is None and new_score is not None:
            alerts.append(f"[TRADE SIGNAL] 새 후보 등장: {stock} ({new_score}점)")
            continue

        if prev_score is not None and new_score is None:
            alerts.append(f"[TRADE SIGNAL] 후보 제외: {stock}")
            continue

        if prev_score is not None and new_score is not None:
            if new_score >= prev_score + 2:
                alerts.append(f"[TRADE SIGNAL] {stock} 점수 상승: {prev_score} → {new_score}")

            prev_signal = classify_signal(prev_score)
            new_signal = classify_signal(new_score)

            if prev_signal != new_signal:
                alerts.append(
                    f"[TRADE SIGNAL] {stock} 상태 변경: {prev_signal} → {new_signal}"
                )

    return alerts

if __name__ == "__main__":
    live_monitor_loop(interval_seconds=5, max_cycles=10)