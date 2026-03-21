"""
Weekly Quality Report Generator — Phase 9 (QC-05, QC-06)

Generates HTML email with 4-week trend data and anomaly detection.

Usage:
  python scripts/quality_report.py
  python scripts/quality_report.py --dry-run
  python scripts/quality_report.py --reference-date 2026-03-20
"""
import argparse
import os
import logging
import smtplib
import ssl
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage

import pandas as pd
from sqlmodel import Session, select

sys_path_insert = __import__("pathlib").Path(__file__).resolve().parent.parent
import sys
if str(sys_path_insert) not in sys.path:
    sys.path.insert(0, str(sys_path_insert))

from app.db.database import sync_engine, init_db_sync
from app.models.quality_metric import QualityMetric

ANOMALY_THRESHOLD = 0.10
WEEKS_TO_SHOW = 4
METRICS = ["freshness_hours", "completeness_pct", "coverage_pct", "product_count", "error_rate"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_weekly_data(session: Session, reference_date: datetime) -> pd.DataFrame:
    """Fetch quality metrics from the last 4 weeks and return weekly averages."""
    start = reference_date - timedelta(weeks=WEEKS_TO_SHOW)
    
    query = (
        select(QualityMetric)
        .where(QualityMetric.scraper_name != "__consolidated__")
        .where(QualityMetric.checked_at >= start)
        .where(QualityMetric.checked_at < reference_date)
    )
    rows = session.exec(query).all()
    
    if not rows:
        return pd.DataFrame()
    
    data = []
    for row in rows:
        data.append({
            "scraper_name": row.scraper_name,
            "freshness_hours": row.freshness_hours,
            "completeness_pct": row.completeness_pct,
            "coverage_pct": row.coverage_pct,
            "product_count": row.product_count,
            "error_rate": row.error_rate,
            "checked_at": row.checked_at,
        })
    
    df = pd.DataFrame(data)
    if df.empty:
        return df
    
    df["week"] = pd.to_datetime(df["checked_at"]).dt.isocalendar().week.astype(int)
    weekly = df.groupby(["scraper_name", "week"]).mean(numeric_only=True).reset_index()
    return weekly


def detect_anomalies(weekly_df: pd.DataFrame) -> dict:
    """Detect scrapers with >10% change week-over-week."""
    improving = []
    degrading = []
    
    if weekly_df.empty:
        return {"improving": improving, "degrading": degrading}
    
    scrapers = weekly_df["scraper_name"].unique()
    
    for scraper in scrapers:
        scraper_data = weekly_df[weekly_df["scraper_name"] == scraper].sort_values("week")
        
        if len(scraper_data) < 2:
            continue
        
        weeks = scraper_data["week"].values
        current_week_data = scraper_data[scraper_data["week"] == weeks[-1]]
        prior_week_data = scraper_data[scraper_data["week"] == weeks[-2]]
        
        if current_week_data.empty or prior_week_data.empty:
            continue
        
        current = current_week_data.iloc[0]
        prior = prior_week_data.iloc[0]
        
        for metric in METRICS:
            prior_val = prior[metric]
            current_val = current[metric]
            
            if prior_val == 0:
                continue
            
            delta = (current_val - prior_val) / abs(prior_val)
            
            if delta > ANOMALY_THRESHOLD:
                if scraper not in improving:
                    improving.append(scraper)
            elif delta < -ANOMALY_THRESHOLD:
                if scraper not in degrading:
                    degrading.append(scraper)
    
    return {"improving": improving, "degrading": degrading}


def _get_arrow(current_val: float, prior_val: float) -> tuple[str, str]:
    """Return arrow character and color based on metric change."""
    if prior_val == 0:
        return "", ""
    
    delta = (current_val - prior_val) / abs(prior_val)
    
    if delta > 0.05:
        return "↑", "#16a34a"
    elif delta < -0.05:
        return "↓", "#dc2626"
    return "", ""


def build_weekly_report(weekly_df: pd.DataFrame, anomalies: dict, reference_date: datetime) -> str:
    """Generate HTML email body with trend table and anomaly sections."""
    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body { font-family: Arial, sans-serif; margin: 20px; }
table { border-collapse: collapse; width: 100%; margin: 20px 0; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
th { background-color: #f5f5f5; }
.degrading { background-color: #fee2e2; border-left: 4px solid #ef4444; padding: 10px; margin: 10px 0; }
.improving { background-color: #dcfce7; border-left: 4px solid #22c55e; padding: 10px; margin: 10px 0; }
.footer { color: #666; font-size: 12px; margin-top: 20px; }
h2 { margin-bottom: 10px; }
</style>
</head>
<body>
<h1>[SliceInsights] Weekly Quality Report</h1>
"""
    
    if anomalies["degrading"]:
        html += "<div class='degrading'><h2>⚠️ Degrading Scrapers</h2><ul>"
        for scraper in anomalies["degrading"]:
            html += f"<li><strong>{scraper}</strong> — one or more metrics dropped &gt;10% week-over-week</li>"
        html += "</ul></div>"
    
    if anomalies["improving"]:
        html += "<div class='improving'><h2>✅ Improving Scrapers</h2><ul>"
        for scraper in anomalies["improving"]:
            html += f"<li><strong>{scraper}</strong> — one or more metrics improved &gt;10% week-over-week</li>"
        html += "</ul></div>"
    
    if weekly_df.empty:
        html += "<p>No quality data available for the reporting period.</p>"
    else:
        scrapers = weekly_df["scraper_name"].unique()
        weeks = sorted(weekly_df["week"].unique())[-WEEKS_TO_SHOW:]
        
        html += "<h2>4-Week Trend</h2><table><thead><tr><th>Scraper</th>"
        for week in weeks:
            html += f"<th>Week {week}</th>"
        html += "</tr></thead><tbody>"
        
        for scraper in scrapers:
            scraper_data = weekly_df[weekly_df["scraper_name"] == scraper].set_index("week")
            html += f"<tr><td style='text-align:left'><strong>{scraper}</strong></td>"
            
            for i, week in enumerate(weeks):
                if week in scraper_data.index:
                    row = scraper_data.loc[week]
                    arrows = []
                    for metric in METRICS:
                        if i > 0 and weeks[i-1] in scraper_data.index:
                            prior_val = scraper_data.loc[weeks[i-1], metric]
                            arrow, color = _get_arrow(row[metric], prior_val)
                            if arrow:
                                arrows.append(f"<span style='color:{color}'>{arrow}</span>")
                        else:
                            arrows.append("")
                    
                    cell_value = f"{row['completeness_pct']:.1f}%"
                    html += f"<td>{cell_value} {''.join(arrows)}</td>"
                else:
                    html += "<td>—</td>"
            
            html += "</tr>"
        
        html += "</tbody></table>"
    
    html += f"""<div class="footer">
    Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
    </div>
</body>
</html>"""
    
    return html


def send_report(html_body: str, subject: str) -> bool:
    """Send HTML email report via SMTP."""
    email_host = os.getenv("EMAIL_HOST", "")
    email_port = int(os.getenv("EMAIL_PORT", "587"))
    email_user = os.getenv("EMAIL_USER", "")
    email_password = os.getenv("EMAIL_PASSWORD", "")
    admin_email_group = os.getenv("ADMIN_EMAIL_GROUP", "")
    
    if not email_host or not email_user or not admin_email_group:
        logger.warning("Email configuration incomplete — skipping send")
        return False
    
    recipients = [e.strip() for e in admin_email_group.split(",") if e.strip()]
    
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = email_user
    msg["To"] = ", ".join(recipients)
    msg.set_content("Weekly Quality Report — view in HTML-capable email client")
    msg.add_alternative(html_body, subtype="html")
    
    try:
        with smtplib.SMTP(email_host, email_port) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(email_user, email_password)
            smtp.send_message(msg)
        logger.info(f"Report sent to {len(recipients)} recipient(s)")
        return True
    except Exception as exc:
        logger.error(f"Failed to send report: {exc}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Weekly quality report generator")
    parser.add_argument("--reference-date", help="ISO date for report window end (default: now)")
    parser.add_argument("--dry-run", action="store_true", help="Generate HTML but don't send email")
    args = parser.parse_args()
    
    if args.reference_date:
        reference_date = datetime.fromisoformat(args.reference_date).replace(tzinfo=timezone.utc)
    else:
        reference_date = datetime.now(timezone.utc)
    
    week_num = reference_date.isocalendar()[1]
    subject = f"[SliceInsights] Weekly Quality Report — Week {week_num}"
    
    init_db_sync()
    
    with Session(sync_engine) as session:
        weekly_df = fetch_weekly_data(session, reference_date)
        anomalies = detect_anomalies(weekly_df)
        html = build_weekly_report(weekly_df, anomalies, reference_date)
        
        if args.dry_run:
            print(html)
        else:
            send_report(html, subject)


if __name__ == "__main__":
    main()
