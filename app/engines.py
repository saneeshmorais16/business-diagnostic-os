from pathlib import Path
import re

import pandas as pd


REQUIRED = {
    "financial": ["date", "revenue", "gross_profit", "operating_cost", "budget_revenue"],
    "operations": ["date", "cycle_time_hours", "throughput", "error_rate", "on_time_rate", "backlog"],
    "sales": ["date", "leads", "opportunities", "wins", "sales_value", "acquisition_cost"],
    "customer_service": [
        "date",
        "contacts",
        "complaints",
        "response_time_hours",
        "resolution_time_hours",
        "satisfaction_score",
        "first_contact_resolution",
        "sla_compliance",
    ],
    "employee": [
        "date",
        "headcount",
        "leavers",
        "absent_days",
        "available_days",
        "vacancies",
        "training_completion",
        "revenue_per_employee",
    ],
}


def safe_filename(name):
    # Keep uploaded file names readable but remove anything that can affect paths.
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", Path(name).name)
    return cleaned[:120] or "upload.csv"


def validate_dataframe(df, kind):
    if kind not in REQUIRED:
        return [{"severity": "error", "type": "dataset_type", "message": "Unsupported dataset type"}]

    issues = []
    required_columns = REQUIRED[kind]
    missing = [column for column in required_columns if column not in df.columns]

    for column in missing:
        issues.append(
            {
                "severity": "error",
                "type": "required_column",
                "column": column,
                "message": f"Required column '{column}' is missing",
            }
        )

    # If core columns are missing, stop before type checks to avoid noisy follow-on errors.
    if missing:
        return issues

    if df.empty:
        return [{"severity": "error", "type": "empty", "message": "Dataset has no rows"}]

    for column in required_columns:
        missing_count = df[column].isna().sum()
        if missing_count:
            issues.append(
                {
                    "severity": "error",
                    "type": "missing_value",
                    "column": column,
                    "message": f"{missing_count} missing value(s)",
                }
            )

    if df.duplicated().any():
        issues.append(
            {
                "severity": "error",
                "type": "duplicate",
                "message": f"{df.duplicated().sum()} duplicate row(s)",
            }
        )

    dates = pd.to_datetime(df.date, errors="coerce")
    if dates.isna().any():
        issues.append(
            {
                "severity": "error",
                "type": "date",
                "column": "date",
                "message": "One or more dates are invalid",
            }
        )
    if dates.duplicated().any():
        issues.append(
            {
                "severity": "warning",
                "type": "date",
                "column": "date",
                "message": "Duplicate reporting periods detected",
            }
        )

    for column in required_columns[1:]:
        numeric = pd.to_numeric(df[column], errors="coerce")

        # Compare against original missing values so blank cells are not double-counted as type errors.
        if numeric.isna().sum() > df[column].isna().sum():
            issues.append(
                {
                    "severity": "error",
                    "type": "data_type",
                    "column": column,
                    "message": "Non-numeric value detected",
                }
            )
            continue

        if (numeric < 0).any():
            issues.append(
                {
                    "severity": "error",
                    "type": "impossible_value",
                    "column": column,
                    "message": "Negative value is not permitted",
                }
            )

        if len(numeric) >= 4 and numeric.std() > 0:
            z_scores = (numeric - numeric.mean()).abs() / numeric.std()
            if (z_scores > 3).any():
                issues.append(
                    {
                        "severity": "warning",
                        "type": "outlier",
                        "column": column,
                        "message": "Extreme outlier requires review",
                    }
                )

        # Rate-like columns are stored as percentages in the sample templates.
        if ("rate" in column or "completion" in column) and (numeric > 100).any():
            issues.append(
                {
                    "severity": "error",
                    "type": "impossible_value",
                    "column": column,
                    "message": "Percentage cannot exceed 100",
                }
            )

    return issues


def _percentage_change(start, end):
    return round((end / start - 1) * 100, 1) if start else 0


def calculate_kpis(df, kind):
    first_row = df.iloc[0]
    last_row = df.iloc[-1]

    # These are intentionally simple board-level indicators, not a full BI layer.
    if kind == "financial":
        return {
            "Revenue growth": _percentage_change(first_row.revenue, last_row.revenue),
            "Gross margin": round(last_row.gross_profit / last_row.revenue * 100, 1),
            "Operating margin": round((last_row.revenue - last_row.operating_cost) / last_row.revenue * 100, 1),
            "Cost growth": _percentage_change(first_row.operating_cost, last_row.operating_cost),
            "Cost-to-income": round(last_row.operating_cost / last_row.revenue * 100, 1),
            "Budget variance": round((last_row.revenue - last_row.budget_revenue) / last_row.budget_revenue * 100, 1),
        }

    if kind == "operations":
        return {
            "Cycle time": float(last_row.cycle_time_hours),
            "Throughput": float(last_row.throughput),
            "Error rate": float(last_row.error_rate),
            "On-time completion": float(last_row.on_time_rate),
            "Backlog": float(last_row.backlog),
            "Average delay": round(float(df.cycle_time_hours.mean()), 1),
        }

    if kind == "sales":
        return {
            "Conversion rate": round(last_row.wins / last_row.leads * 100, 1),
            "Average deal value": round(last_row.sales_value / last_row.wins, 1),
            "Sales growth": _percentage_change(first_row.sales_value, last_row.sales_value),
            "Pipeline value": round(last_row.opportunities * (last_row.sales_value / last_row.wins), 1),
            "Win rate": round(last_row.wins / last_row.opportunities * 100, 1),
            "Customer acquisition cost": round(last_row.acquisition_cost / last_row.wins, 1),
        }

    if kind == "customer_service":
        return {
            "Response time": float(last_row.response_time_hours),
            "Resolution time": float(last_row.resolution_time_hours),
            "Complaint rate": round(last_row.complaints / last_row.contacts * 100, 1),
            "Satisfaction score": float(last_row.satisfaction_score),
            "First-contact resolution": float(last_row.first_contact_resolution),
            "Service-level compliance": float(last_row.sla_compliance),
        }

    return {
        "Employee turnover": round(last_row.leavers / last_row.headcount * 100, 1),
        "Absenteeism": round(last_row.absent_days / last_row.available_days * 100, 1),
        "Vacancy rate": round(last_row.vacancies / (last_row.headcount + last_row.vacancies) * 100, 1),
        "Training completion": float(last_row.training_completion),
        "Employee productivity": float(last_row.revenue_per_employee),
    }


def roi(initial, recurring, annual):
    # Benefits are gross annual estimates; the README explains they still need finance validation.
    net = annual - recurring
    monthly = net / 12
    return {
        "net_benefit": round(net, 2),
        "roi_percentage": round(net / initial * 100, 1) if initial else None,
        "payback_months": round(initial / monthly, 1) if monthly > 0 else None,
    }


def score_opportunity(scores, weights=None):
    weights = weights or {
        "impact": 0.25,
        "alignment": 0.15,
        "feasibility": 0.15,
        "time_to_value": 0.10,
        "readiness": 0.10,
        "risk": 0.15,
        "cost": 0.10,
    }

    positive = ["impact", "alignment", "feasibility", "time_to_value", "readiness"]
    weighted_score = sum(scores[key] * weights[key] for key in positive)

    # Risk and cost are inverted so lower risk/cost improves the priority score.
    weighted_score += (6 - scores["risk"]) * weights["risk"]
    weighted_score += (6 - scores["cost"]) * weights["cost"]
    score = round(weighted_score / sum(weights.values()) * 20, 1)

    if score >= 75 and scores["difficulty"] <= 2:
        label = "Quick Win"
    elif score >= 75:
        label = "Strategic Priority"
    elif scores["impact"] >= 4 and scores["difficulty"] >= 4:
        label = "Major Transformation"
    elif score < 40:
        label = "Do Not Pursue"
    else:
        label = "Defer"

    return score, label


def classify_stakeholder(influence, interest):
    if influence >= 4 and interest >= 4:
        return "Manage Closely"
    if influence >= 4:
        return "Keep Satisfied"
    if interest >= 4:
        return "Keep Informed"
    return "Monitor"


def diagnose(kpis, maturity=3):
    findings = []
    rules = [
        ("Operating margin", 8, "Margin compression", "Finance", 5, False),
        ("On-time completion", 85, "Delivery reliability below target", "Operations", 5, False),
        ("Complaint rate", 5, "Complaint rate above tolerance", "Customer service", 4, True),
    ]

    for metric, threshold, title, function, severity, high_is_bad in rules:
        if metric not in kpis:
            continue

        value = kpis[metric]
        threshold_breached = value > threshold if high_is_bad else value < threshold
        if threshold_breached:
            findings.append(
                {
                    "title": title,
                    "function": function,
                    "affected_kpi": metric,
                    "severity": severity,
                    "confidence": 85,
                    "finding_type": "confirmed finding",
                }
            )

    if maturity <= 2:
        findings.append(
            {
                "title": "Material capability gap",
                "function": "Cross-functional",
                "affected_kpi": "Maturity",
                "severity": 4,
                "confidence": 65,
                "finding_type": "likely finding",
            }
        )

    return findings
