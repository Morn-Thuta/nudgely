"""Who came back after a campaign, read from the shop's own sales file.

The shop uploads its purchases (CSV or Excel, one row per purchase). Every
customer in the campaign log, messaged or kept back, is marked the same way:

    1      bought at least once within `window` days after the send
    0      the file covers the whole window and they did not buy
    blank  the file stops before their window closes, so it is too early to say

Counting both groups the same way is the point. A coupon code only exists for
people who were messaged, so counting redemptions would make the kept-back group
look like it never returns, and every campaign would look like a win.

Messy files are expected. Rows that cannot be used are kept, with the reason,
so the owner can fix them in the Excel report and upload them again.
"""

import io
import re
from datetime import date, datetime

import numpy as np
import pandas as pd

WINDOW = 30
START_SLACK = 3      # the file may start this many days after a send and still settle a No
WHO_HINTS = ("phone", "mobile", "contact", "hp", "customer", "member", "client", "id")
WHEN_HINTS = ("date", "time", "day", "when")
EXCEL_EPOCH = pd.Timestamp("1899-12-30")
ISO = re.compile(r"^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}")


# ---- reading a messy file -----------------------------------------------------

def read_file(data, name):
    """Every sheet of an upload as {sheet name: DataFrame}, all values kept as text or dates.

    Phones stay text, so a leading +65 or 0 is not lost.
    """
    lower = name.lower()
    if lower.endswith((".xlsx", ".xlsm")):
        book = pd.read_excel(io.BytesIO(data), sheet_name=None, dtype=object)
        return {sheet: frame.dropna(how="all") for sheet, frame in book.items()}
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            frame = pd.read_csv(io.BytesIO(data), dtype=str, keep_default_na=False,
                                sep=None, engine="python", encoding=encoding)
            return {"file": frame}
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not read the file. Save it as CSV (UTF-8) or Excel and try again.")


def guess_column(columns, hints):
    for hint in hints:
        for column in columns:
            if hint in str(column).strip().lower():
                return column
    return None


def clean_id(value):
    """Make the same customer look the same: '+65 9123-4567' -> '91234567', ' c001 ' -> 'C001'."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0", text):        # Excel stored the phone as a number
        text = text[:-2]
    digits = re.sub(r"\D", "", text)
    if len(digits) >= 7 and re.fullmatch(r"[\d\s+()\-.]+", text):
        if len(digits) == 10 and digits.startswith("65"):
            digits = digits[2:]                  # Singapore country code
        return digits
    if text.lower() in ("", "nan", "none", "null", "-", "n/a"):
        return ""
    return re.sub(r"\s+", "", text).upper()


def parse_date(value):
    """One date, read the way a Singapore shop writes it. NaT if it cannot be read."""
    if value is None or value is pd.NaT:
        return pd.NaT
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return pd.Timestamp(value)
    if isinstance(value, (int, float, np.integer, np.floating)) and not pd.isna(value):
        if 20000 < float(value) < 80000:        # an Excel date that lost its format
            return EXCEL_EPOCH + pd.Timedelta(days=float(value))
        return pd.NaT
    text = str(value).strip()
    if not text or text.lower() in ("nan", "nat", "none", "null"):
        return pd.NaT
    if re.fullmatch(r"\d{5}(\.\d+)?", text):
        return parse_date(float(text))
    try:
        # 2026-08-03 is year-month-day. Anything else is day first: 03/08/2026 is 3 August.
        return pd.Timestamp(pd.to_datetime(text, dayfirst=not ISO.match(text)))
    except (ValueError, OverflowError):
        return pd.NaT


def read_purchases(frame, who, when, today=None):
    """Split the upload into usable purchases and rows that need fixing.

    Returns (purchases, problems). purchases has row, who, when. problems is the
    original rows, with the spreadsheet row number and what is wrong with each.
    """
    today = pd.Timestamp(today or pd.Timestamp.now().normalize())
    # A 'Needs fixing' sheet coming back carries our own two columns; they describe the old file.
    frame = frame.drop(columns=[c for c in ("row", "problem") if c in frame.columns and c not in (who, when)])
    rows = pd.Series(np.arange(2, len(frame) + 2), index=frame.index)   # row 1 is the header
    ids = frame[who].map(clean_id)
    dates = frame[when].map(parse_date)

    problem = pd.Series("", index=frame.index)
    problem[dates.isna()] = "Date not readable - write it as 3/8/2026 or 2026-08-03"
    problem[dates.notna() & ((dates.dt.year < 2000) | (dates > today + pd.Timedelta(days=1)))] = \
        "Date looks wrong - in the future, or before 2000"
    problem[ids == ""] = "No customer ID or phone"

    ok = problem == ""
    purchases = pd.DataFrame({"row": rows[ok], "who": ids[ok], "when": dates[ok].dt.normalize()})
    problems = frame[~ok].copy()
    problems.insert(0, "problem", problem[~ok])
    problems.insert(0, "row", rows[~ok])
    return purchases.reset_index(drop=True), problems.reset_index(drop=True)


# ---- matching ------------------------------------------------------------------

def match_returns(log, purchases, window=WINDOW):
    """Mark every customer in the campaign log from the purchases.

    Returns (results, unmatched). results is the log with came_back, returned_at
    and evidence filled in. unmatched is the purchases whose customer is in no
    campaign: normal for most of a shop, but a typo in an ID also lands here.
    """
    results = log.copy()
    sent = pd.to_datetime(results["sent_at"], errors="coerce").dt.normalize()
    keys = results["customer_id"].map(clean_id)
    covered_until = purchases["when"].max() if len(purchases) else pd.NaT
    first_seen = purchases["when"].min() if len(purchases) else pd.NaT
    bought = {k: g.sort_values() for k, g in purchases.groupby("who")["when"]} if len(purchases) else {}

    came_back, returned_at, evidence = [], [], []
    for key, start in zip(keys, sent):
        end = start + pd.Timedelta(days=window)
        visits = bought.get(key)
        inside = visits[(visits > start) & (visits <= end)] if visits is not None else pd.Series(dtype="datetime64[ns]")
        if pd.isna(start):
            came_back.append(np.nan); returned_at.append(""); evidence.append("Campaign has no send date")
        elif len(inside):
            came_back.append(1); returned_at.append(inside.iloc[0].date().isoformat())
            evidence.append(f"Bought on {inside.iloc[0]:%d %b %Y}, {(inside.iloc[0] - start).days} days after the send")
        elif pd.notna(first_seen) and first_seen > start + pd.Timedelta(days=START_SLACK):
            # A quiet day or two after the send is normal; a file that starts weeks later
            # could be missing the very purchase that counts, so do not call it a No.
            came_back.append(np.nan); returned_at.append("")
            evidence.append(f"File starts {first_seen:%d %b %Y}, too long after the {start:%d %b} send "
                            "- include sales from the send date")
        elif pd.notna(covered_until) and covered_until >= end:
            came_back.append(0); returned_at.append("")
            evidence.append(f"No purchase between {start:%d %b} and {end:%d %b %Y}")
        else:
            came_back.append(np.nan); returned_at.append("")
            evidence.append(f"Too early: their 30 days end {end:%d %b %Y}, the file ends "
                            + (f"{covered_until:%d %b %Y}" if pd.notna(covered_until) else "with no usable rows"))
    results["came_back"] = came_back
    results["returned_at_new"] = returned_at
    results["evidence"] = evidence

    unmatched = purchases[~purchases["who"].isin(set(keys))].copy()
    lookalike = {_confusable(k): k for k in keys}
    unmatched["check"] = [f"Probably {lookalike[_confusable(w)]} typed wrong - fix it and upload again"
                          if _confusable(w) in lookalike else "" for w in unmatched["who"]]
    unmatched = unmatched.sort_values(["check", "row"], ascending=[False, True]).reset_index(drop=True)
    return results, unmatched


def _confusable(text):
    """O for 0, I or L for 1: the slips that turn a campaign customer into a stranger."""
    return str(text).upper().translate(str.maketrans({"O": "0", "I": "1", "L": "1"}))


def apply_to_log(log, results):
    """Write new outcomes into the log. A purchase (1) always wins; a 0 only fills a blank.

    So uploading a fixed file later can turn a 0 into a 1, never the other way.
    """
    log = log.copy()
    old = pd.to_numeric(log["returned"], errors="coerce")
    new = results["came_back"]
    take = (new == 1) | (old.isna() & (new == 0))
    log["returned"] = log["returned"].astype(object)
    log["returned_at"] = log["returned_at"].astype(object)
    log.loc[take, "returned"] = new[take].astype(int)
    log.loc[take & (new == 1), "returned_at"] = results.loc[take & (new == 1), "returned_at_new"]
    return log, int(take.sum())


# ---- the Excel report ------------------------------------------------------------

def report(results, problems, unmatched, source_name, frame=None):
    """An .xlsx the owner can read, fix and upload again. Returns bytes.

    `frame` is the uploaded sheet. With it, rows whose ID looks mistyped join the
    unreadable ones on 'Needs fixing' in their original columns, so that one
    sheet can be corrected and uploaded straight back.
    """
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    typos = unmatched[unmatched["check"] != ""]
    if frame is not None and len(typos):
        original = frame.iloc[(typos["row"] - 2).tolist()].copy()
        original.insert(0, "problem", typos["check"].tolist())
        original.insert(0, "row", typos["row"].tolist())
        problems = pd.concat([problems, original]).sort_values("row").reset_index(drop=True)
        unmatched = unmatched[unmatched["check"] == ""]
    unmatched = unmatched.drop(columns="check")

    status = results["came_back"].map({1: "Yes", 0: "No"}).fillna("Not yet")
    sheet1 = pd.DataFrame({
        "Campaign": results["campaign_id"],
        "Sent": pd.to_datetime(results["sent_at"], errors="coerce").dt.date,
        "Customer ID": results["customer_id"],
        "Name": results["name"],
        "Group": results["group"].map({"messaged": "Messaged", "holdout": "Kept back"}).fillna(results["group"]),
        "Came back": status,
        "First purchase after send": results["returned_at_new"],
        "How we know": results["evidence"],
    })
    summary = []
    for group, label in (("messaged", "Messaged"), ("holdout", "Kept back")):
        part = results[(results["group"] == group) & results["came_back"].isin([0, 1])]
        if len(part):
            summary.append(f"{label}: {int(part.came_back.sum())} of {len(part)} came back "
                           f"({part.came_back.mean():.0%})")
    notes = pd.DataFrame({"Nudgely - who came back": [
        f"Made from: {source_name}, on {pd.Timestamp.now():%d %b %Y %H:%M}",
        *summary,
        "",
        "Sheets",
        "Campaign results - every customer in the campaign, messaged or kept back, and whether they came back.",
        "Needs fixing - rows we could not use, and IDs that look mistyped, with the reason. Fix them "
        "here, save, and upload this file again, picking this sheet. The 'row' and 'problem' columns "
        "are ignored on the way back in.",
        "Not in a campaign - purchases by customers who were not part of any campaign. That is normal: "
        "most of a shop is not in any one campaign.",
        "",
        "Rules",
        f"Came back = bought at least once within {WINDOW} days after the send.",
        "Not yet = the file ends before their 30 days are up. Upload a later file to settle it.",
        "Dates are read day first (3/8/2026 is 3 August), except year-first dates like 2026-08-03.",
        "Phones: spaces, dashes and a leading +65 are ignored, so +65 9123 4567 and 91234567 match.",
    ]})
    sheet3 = unmatched.rename(columns={"row": "Row in your file", "who": "Customer ID or phone",
                                       "when": "Purchase date"})
    if len(sheet3):
        sheet3["Purchase date"] = sheet3["Purchase date"].dt.date

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        notes.to_excel(writer, sheet_name="Read me", index=False)
        sheet1.to_excel(writer, sheet_name="Campaign results", index=False)
        problems.to_excel(writer, sheet_name="Needs fixing", index=False)
        sheet3.to_excel(writer, sheet_name="Not in a campaign", index=False)

        head = PatternFill("solid", fgColor="0E9F6E")
        fills = {"Yes": PatternFill("solid", fgColor="D9F2E6"), "No": PatternFill("solid", fgColor="EEF1EF"),
                 "Not yet": PatternFill("solid", fgColor="FFF4D6")}
        for name, ws in writer.sheets.items():
            ws.freeze_panes = "A2"
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = head
            for i, column in enumerate(ws.columns, 1):
                longest = max((len(str(c.value)) for c in column if c.value is not None), default=8)
                ws.column_dimensions[get_column_letter(i)].width = min(max(10, longest + 2), 70 if name == "Read me" else 45)
            if name == "Read me":
                ws.column_dimensions["A"].width = 110
                for row in ws.iter_rows(min_row=2):
                    row[0].alignment = Alignment(wrap_text=True)
                    if row[0].value in ("Sheets", "Rules"):
                        row[0].font = Font(bold=True)
            if name == "Campaign results":
                for cell in ws["F"][1:]:
                    cell.fill = fills.get(cell.value, PatternFill())
            if name == "Needs fixing":
                for cell in ws["B"][1:]:
                    cell.fill = fills["Not yet"]
    return buffer.getvalue()
