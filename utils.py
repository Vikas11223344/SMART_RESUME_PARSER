"""
Utility helpers for exporting parsed data to JSON/CSV and simple formatting.
"""

import json
import pandas as pd
from typing import Dict, Any


def to_json(parsed: Dict[str, Any]) -> str:
    return json.dumps(parsed, indent=2, ensure_ascii=False)


def parsed_to_dataframe(parsed: Dict[str, Any]) -> pd.DataFrame:
    """
    Flatten parsed object into a simple DataFrame with rows for skills, education, experience.
    """
    rows = []
    # contact info row
    contact = parsed.get("contact", {})
    rows.append({
        "section": "contact",
        "key": "emails",
        "value": ", ".join(contact.get("emails", []))
    })
    rows.append({
        "section": "contact",
        "key": "phones",
        "value": ", ".join(contact.get("phones", []))
    })
    rows.append({
        "section": "contact",
        "key": "linkedin",
        "value": ", ".join(contact.get("linkedin", []))
    })

    # summary
    rows.append({"section": "summary", "key": "summary", "value": parsed.get("summary", "")})

    # skills
    for s in parsed.get("skills", []):
        rows.append({"section": "skills", "key": "skill", "value": s})

    # education
    for edu in parsed.get("education", []):
        rows.append({"section": "education", "key": edu.get("degree", ""), "value": f'{edu.get("institution","")} | {edu.get("year","")}'})

    # experience
    for exp in parsed.get("experience", []):
        title = exp.get("title_company", "")
        dates = ", ".join(exp.get("date_tokens", []))
        details = "; ".join(exp.get("details", []))
        rows.append({"section": "experience", "key": title, "value": f"{dates} | {details}"})

    return pd.DataFrame(rows)


def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")