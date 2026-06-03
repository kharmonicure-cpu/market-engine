from pathlib import Path
from datetime import date
from collections import Counter
import csv
import html

def read_dashboard_history(file_path: str = "reports/history.csv") -> list[dict]:
    path = Path(file_path)

    if not path.exists():
        return []

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)

def format_number(value) -> str:
    if value is None:
        return "-"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    if number.is_integer():
        return f"{int(number):,}"

    return f"{number:,.2f}"


def get_market_badge_class(market_status: str) -> str:
    if market_status == "Risk-On":
        return "badge risk-on"

    if market_status == "Risk-Off":
        return "badge risk-off"

    return "badge neutral"
def make_market_breadth_chart(market: dict) -> str:
    up_count = int(market.get("up_count", 0) or 0)
    down_count = int(market.get("down_count", 0) or 0)

    total = up_count + down_count

    if total <= 0:
        up_percent = 0
        down_percent = 0
    else:
        up_percent = round((up_count / total) * 100, 1)
        down_percent = round((down_count / total) * 100, 1)

    return f"""
    <div class="chart-box">
        <div class="chart-row">
            <div class="chart-label">상승종목</div>
            <div class="chart-track">
                <div class="bar bar-up" style="width: {up_percent}%;">
                    {up_count:,}개
                </div>
            </div>
            <div class="chart-percent">{up_percent}%</div>
        </div>

        <div class="chart-row">
            <div class="chart-label">하락종목</div>
            <div class="chart-track">
                <div class="bar bar-down" style="width: {down_percent}%;">
                    {down_count:,}개
                </div>
            </div>
            <div class="chart-percent">{down_percent}%</div>
        </div>
    </div>
    """

def make_market_status_history_chart(history_rows: list[dict]) -> str:
    if not history_rows:
        return """
        <div class="empty">최근 시장 상태 그래프를 만들 데이터가 없습니다.</div>
        """

    counter = Counter()

    for row in history_rows:
        market_status = row.get("market_status", "").strip()

        if market_status:
            counter[market_status] += 1

    chart_items = [
        ("Risk-On", counter.get("Risk-On", 0), "bar-up"),
        ("Neutral", counter.get("Neutral", 0), "bar-score"),
        ("Risk-Off", counter.get("Risk-Off", 0), "bar-down"),
    ]

    max_count = max(count for _, count, _ in chart_items)

    if max_count <= 0:
        max_count = 1

    rows = []

    for label, count, bar_class in chart_items:
        width_percent = round((count / max_count) * 100, 1)

        rows.append(
            f"""
            <div class="chart-row">
                <div class="chart-label">{html.escape(label)}</div>
                <div class="chart-track">
                    <div class="bar {bar_class}" style="width: {width_percent}%;">
                        {count}회
                    </div>
                </div>
                <div class="chart-percent">{count}</div>
            </div>
            """
        )

    return f"""
    <div class="chart-box">
        {''.join(rows)}
    </div>
    """


def make_top_candidate_history_chart(history_rows: list[dict]) -> str:
    if not history_rows:
        return """
        <div class="empty">후보 종목 그래프를 만들 데이터가 없습니다.</div>
        """

    counter = Counter()

    for row in history_rows:
        bigcap_candidates = row.get("bigcap_candidates", "").strip()
        candidate_scores = row.get("candidate_scores", "").strip()

        if bigcap_candidates:
            candidates = bigcap_candidates.split("|")

            for stock in candidates:
                stock = stock.strip()

                if stock:
                    counter[stock] += 1

            continue

        if candidate_scores:
            parts = candidate_scores.split("|")

            for part in parts:
                if ":" not in part:
                    continue

                stock = part.split(":", 1)[0].strip()

                if stock:
                    counter[stock] += 1

    top_items = counter.most_common(5)

    if not top_items:
        return """
        <div class="empty">후보 종목 기록이 없습니다.</div>
        """

    max_count = max(count for _, count in top_items)

    if max_count <= 0:
        max_count = 1

    rows = []

    for stock, count in top_items:
        width_percent = round((count / max_count) * 100, 1)

        rows.append(
            f"""
            <div class="chart-row">
                <div class="chart-label">{html.escape(stock)}</div>
                <div class="chart-track">
                    <div class="bar bar-score" style="width: {width_percent}%;">
                        {count}회
                    </div>
                </div>
                <div class="chart-percent">{count}</div>
            </div>
            """
        )

    return f"""
    <div class="chart-box">
        {''.join(rows)}
    </div>
    """

def make_candidate_score_chart(scored_candidates: list[dict]) -> str:
    if not scored_candidates:
        return """
        <div class="empty">후보 점수 그래프를 만들 데이터가 없습니다.</div>
        """

    max_score = max(int(item.get("score", 0) or 0) for item in scored_candidates)

    if max_score <= 0:
        max_score = 1

    rows = []

    for item in scored_candidates:
        stock = html.escape(str(item.get("stock", "")))
        score = int(item.get("score", 0) or 0)
        width_percent = round((score / max_score) * 100, 1)

        rows.append(
            f"""
            <div class="chart-row">
                <div class="chart-label">{stock}</div>
                <div class="chart-track">
                    <div class="bar bar-score" style="width: {width_percent}%;">
                        {score}점
                    </div>
                </div>
                <div class="chart-percent">{score}</div>
            </div>
            """
        )

    return f"""
    <div class="chart-box">
        {''.join(rows)}
    </div>
    """

def make_candidate_rows(scored_candidates: list[dict]) -> str:
    if not scored_candidates:
        return """
        <tr>
            <td colspan="4" class="empty">후보 종목이 없습니다.</td>
        </tr>
        """

    rows = []

    for item in scored_candidates:
        stock = html.escape(str(item.get("stock", "")))
        score = item.get("score", 0)
        signal = html.escape(str(item.get("signal", "")))
        reasons = item.get("reasons", [])

        if not signal:
            if score >= 6:
                signal = "매매 후보"
            elif score >= 4:
                signal = "관찰"
            else:
                signal = "제외"

        reasons_text = ", ".join(reasons) if reasons else "사유 없음"
        reasons_text = html.escape(reasons_text)

        rows.append(
            f"""
            <tr>
                <td>{stock}</td>
                <td class="number">{score}</td>
                <td>{signal}</td>
                <td>{reasons_text}</td>
            </tr>
            """
        )

    return "\n".join(rows)


def make_trade_plan_rows(trade_plans: list[dict]) -> str:
    if not trade_plans:
        return """
        <tr>
            <td colspan="6" class="empty">매매 계획이 없습니다.</td>
        </tr>
        """

    rows = []

    for plan in trade_plans:
        stock = html.escape(str(plan.get("stock", "")))
        signal = html.escape(str(plan.get("signal", "")))
        entry_price = format_number(plan.get("entry_price"))
        target_price = format_number(plan.get("target_price"))
        stop_price = format_number(plan.get("stop_price"))
        quantity = format_number(plan.get("quantity"))

        rows.append(
            f"""
            <tr>
                <td>{stock}</td>
                <td>{signal}</td>
                <td class="number">{entry_price}</td>
                <td class="number">{target_price}</td>
                <td class="number">{stop_price}</td>
                <td class="number">{quantity}</td>
            </tr>
            """
        )

    return "\n".join(rows)


def make_order_rows(orders: list[dict]) -> str:
    if not orders:
        return """
        <tr>
            <td colspan="6" class="empty">주문 티켓이 없습니다.</td>
        </tr>
        """

    rows = []

    for order in orders:
        name = html.escape(str(order.get("name", "")))
        symbol = html.escape(str(order.get("symbol", "")))
        side = html.escape(str(order.get("side", "")))
        quantity = format_number(order.get("quantity"))
        price = format_number(order.get("price"))
        strategy = html.escape(str(order.get("strategy", "")))

        rows.append(
            f"""
            <tr>
                <td>{name}</td>
                <td>{symbol}</td>
                <td>{side}</td>
                <td class="number">{quantity}</td>
                <td class="number">{price}</td>
                <td>{strategy}</td>
            </tr>
            """
        )

    return "\n".join(rows)


def generate_dashboard(
    analysis_result: dict,
    market: dict,
    history_summary: str,
    output_path: str = "reports/dashboard.html",
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    market_status = analysis_result.get("market_status", "Unknown")
    bigcap_candidates = analysis_result.get("bigcap_candidates", [])
    scored_candidates = analysis_result.get("scored_candidates", [])
    trade_plans = analysis_result.get("trade_plans", [])
    orders = analysis_result.get("orders", [])
    summary = analysis_result.get("summary", "")

    sectors = market.get("sectors", [])
    leaders = market.get("leaders", [])
    history_rows = read_dashboard_history()

    badge_class = get_market_badge_class(market_status)

    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Market Engine Dashboard</title>
    <style>
        body {{
            margin: 0;
            padding: 24px;
            font-family: Arial, "Malgun Gothic", sans-serif;
            background: #f4f6f8;
            color: #222;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            margin-bottom: 24px;
        }}

        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}

        .subtitle {{
            margin-top: 8px;
            color: #666;
        }}

        .cards {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}

        .card {{
            background: white;
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}

        .card-title {{
            font-size: 13px;
            color: #777;
            margin-bottom: 8px;
        }}

        .card-value {{
            font-size: 22px;
            font-weight: bold;
        }}

        .badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            color: white;
            font-weight: bold;
            font-size: 16px;
        }}

        .risk-on {{
            background: #1f9d55;
        }}

        .risk-off {{
            background: #d64545;
        }}

        .neutral {{
            background: #6b7280;
        }}

        .section {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}

        .section h2 {{
            margin-top: 0;
            font-size: 20px;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }}

        th, td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
            text-align: left;
            font-size: 14px;
        }}

        th {{
            background: #f8fafc;
            color: #444;
        }}

        .number {{
            text-align: right;
        }}

        .summary-box {{
            line-height: 1.7;
            background: #f8fafc;
            padding: 14px;
            border-radius: 8px;
            white-space: pre-line;
        }}

                .empty {{
            text-align: center;
            color: #888;
            padding: 24px;
        }}

        .chart-box {{
            margin-top: 12px;
        }}

        .chart-row {{
            display: grid;
            grid-template-columns: 120px 1fr 70px;
            gap: 12px;
            align-items: center;
            margin-bottom: 14px;
        }}

        .chart-label {{
            font-weight: bold;
            color: #333;
        }}

        .chart-track {{
            background: #edf2f7;
            border-radius: 999px;
            overflow: hidden;
            height: 30px;
        }}

        .bar {{
            height: 30px;
            line-height: 30px;
            border-radius: 999px;
            color: white;
            font-size: 13px;
            font-weight: bold;
            text-align: right;
            padding-right: 10px;
            box-sizing: border-box;
            min-width: 44px;
        }}

        .bar-up {{
            background: #1f9d55;
        }}

        .bar-down {{
            background: #d64545;
        }}

        .bar-score {{
            background: #2563eb;
        }}

        .chart-percent {{
            text-align: right;
            color: #555;
            font-weight: bold;
        }}

        @media (max-width: 900px) {{
            .cards {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        @media (max-width: 600px) {{
            .cards {{
                grid-template-columns: 1fr;
            }}

            body {{
                padding: 12px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Market Engine Dashboard</h1>
            <div class="subtitle">생성일: {date.today().isoformat()}</div>
        </div>

        <div class="cards">
            <div class="card">
                <div class="card-title">시장 상태</div>
                <div class="card-value">
                    <span class="{badge_class}">{html.escape(str(market_status))}</span>
                </div>
            </div>

            <div class="card">
                <div class="card-title">코스피</div>
                <div class="card-value">{format_number(market.get("kospi"))}%</div>
            </div>

            <div class="card">
                <div class="card-title">코스닥</div>
                <div class="card-value">{format_number(market.get("kosdaq"))}%</div>
            </div>

            <div class="card">
                <div class="card-title">대형주 후보 수</div>
                <div class="card-value">{len(bigcap_candidates)}개</div>
            </div>
        </div>

        <div class="section">
            <h2>오늘 시장 요약</h2>
            <div class="summary-box">{html.escape(summary)}</div>
            <table>
                <tr>
                    <th>항목</th>
                    <th>값</th>
                </tr>
                <tr>
                    <td>상승종목수</td>
                    <td class="number">{format_number(market.get("up_count"))}</td>
                </tr>
                <tr>
                    <td>하락종목수</td>
                    <td class="number">{format_number(market.get("down_count"))}</td>
                </tr>
                <tr>
                    <td>강한 섹터</td>
                    <td>{html.escape(", ".join(sectors) if sectors else "없음")}</td>
                </tr>
                <tr>
                    <td>리더 종목</td>
                    <td>{html.escape(", ".join(leaders) if leaders else "없음")}</td>
                </tr>
                <tr>
                    <td>외국인 수급</td>
                    <td>{html.escape(str(market.get("foreign_flow", "-")))}</td>
                </tr>
                <tr>
                    <td>기관 수급</td>
                    <td>{html.escape(str(market.get("institution_flow", "-")))}</td>
                </tr>
            </table>
        </div>

                <div class="section">
            <h2>시장 흐름 그래프</h2>
            {make_market_breadth_chart(market)}
        </div>

        <div class="section">
            <h2>후보 점수 그래프</h2>
            {make_candidate_score_chart(scored_candidates)}
        </div>

        <div class="section">
            <h2>오늘 후보 점수</h2>
            <table>
                <tr>
                    <th>종목</th>
                    <th>점수</th>
                    <th>판단</th>
                    <th>사유</th>
                </tr>
                {make_candidate_rows(scored_candidates)}
            </table>
        </div>

        <div class="section">
            <h2>매매 계획</h2>
            <table>
                <tr>
                    <th>종목</th>
                    <th>상태</th>
                    <th>진입가</th>
                    <th>목표가</th>
                    <th>손절가</th>
                    <th>수량</th>
                </tr>
                {make_trade_plan_rows(trade_plans)}
            </table>
        </div>

        <div class="section">
            <h2>주문 티켓</h2>
            <table>
                <tr>
                    <th>종목명</th>
                    <th>종목코드</th>
                    <th>매수/매도</th>
                    <th>수량</th>
                    <th>가격</th>
                    <th>전략</th>
                </tr>
                {make_order_rows(orders)}
            </table>
        </div>

                <div class="section">
            <h2>최근 시장 상태 그래프</h2>
            {make_market_status_history_chart(history_rows)}
        </div>

        <div class="section">
            <h2>후보 종목 TOP 5</h2>
            {make_top_candidate_history_chart(history_rows)}
        </div>

        <div class="section">
            <h2>최근 기록 요약</h2>
            <div class="summary-box">{html.escape(history_summary)}</div>
        </div>
    </div>
</body>
</html>
"""

    path.write_text(html_content, encoding="utf-8")
    print(f"[DASHBOARD] HTML 대시보드 생성 완료: {output_path}")