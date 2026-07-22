"""
QLD SARA decisions supplement.

Loads the cached SARA decisions (data/inputs/qld_sara_decisions.json),
matches them to QLD DA projects, and:
  - Stores the approval date in a new `sara_decision_date` field
  - Sets stage = "Expired" for projects approved >= EXPIRY_YEARS ago
    with no evidence of a currency extension

Called from fetch_cer_da.main() after the QLD DA merge.
Run scripts/fetch_sara_decisions.py separately to refresh the cache.
"""
from __future__ import annotations

import json
import pathlib
import re
from datetime import date

ROOT       = pathlib.Path(__file__).resolve().parent.parent
SARA_FILE  = ROOT / "data" / "inputs" / "qld_sara_decisions.json"

EXPIRY_YEARS = 5   # DA currency period threshold (years)

# Words stripped before matching — too generic to be discriminating
SKIP_WORDS = {
    "solar", "wind", "farm", "battery", "bess", "energy", "power", "station",
    "park", "project", "stage", "hub", "facility", "hydro", "pumped", "storage",
    "and", "the", "renewable", "generation",
}

# Technology keywords for soft cross-check
SOLAR_RE   = re.compile(r"\bsolar\b", re.I)
WIND_RE    = re.compile(r"\bwind\b", re.I)
BATTERY_RE = re.compile(r"\b(bess|battery|storage)\b", re.I)
HYDRO_RE   = re.compile(r"\b(hydro|pumped)\b", re.I)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()


def _tech_of(project: dict) -> str:
    t = (project.get("technology") or "").lower()
    if "solar"   in t: return "solar"
    if "wind"    in t: return "wind"
    if "battery" in t or "bess" in t: return "battery"
    if "hydro"   in t: return "hydro"
    return "other"


def _sara_mentions_tech(text: str, tech: str) -> bool:
    """Does the SARA proposal text mention the same technology?"""
    if tech == "solar":   return bool(SOLAR_RE.search(text))
    if tech == "wind":    return bool(WIND_RE.search(text))
    if tech == "battery": return bool(BATTERY_RE.search(text))
    if tech == "hydro":   return bool(HYDRO_RE.search(text))
    return True   # "other" — no check


def _distinctive_words(name: str) -> list[str]:
    """Return the discriminating words from a project name."""
    words = _norm(name).split()
    return [w for w in words if len(w) > 3 and w not in SKIP_WORDS]


def _build_corpus(sara_records: list[dict]) -> list[tuple[str, dict]]:
    corpus = []
    for r in sara_records:
        text = _norm(" ".join([
            r.get("proposalDetails") or "",
            r.get("siteAddress")     or "",
            r.get("applicant")       or "",
        ]))
        corpus.append((text, r))
    return corpus


def _find_best_match(
    project: dict,
    corpus: list[tuple[str, dict]],
    min_score: int = 2,
) -> tuple[dict | None, int]:
    """
    Return (best_sara_record, score) or (None, 0).

    Matching rules:
      - Score = count of distinctive project-name words found in SARA text
      - Require score >= min_score (default 2)
      - EXCEPT: if score == 1, the single word must be >= 7 chars (very specific)
        AND the SARA proposal must mention the right technology
      - Technology must loosely match (solar ↔ solar, wind ↔ wind, etc.)
    """
    words = _distinctive_words(project.get("site_name", ""))
    if not words:
        return None, 0

    tech = _tech_of(project)
    best_r, best_score = None, 0

    for text, r in corpus:
        score = sum(1 for w in words if w in text)
        if score > best_score:
            best_score = score
            best_r = r

    if best_score == 0 or best_r is None:
        return None, 0

    # Apply score threshold
    if best_score < min_score:
        # Allow score=1 only for very long distinctive words
        if best_score == 1:
            matching_word = next((w for w in words if w in _norm(
                " ".join([best_r.get("proposalDetails") or "",
                          best_r.get("siteAddress") or "",
                          best_r.get("applicant") or ""])
            )), "")
            if len(matching_word) < 7:
                return None, 0
        else:
            return None, 0

    # Technology cross-check
    sara_text = (best_r.get("proposalDetails") or "") + (best_r.get("natureOfDevelopment") or "")
    if not _sara_mentions_tech(sara_text, tech):
        return None, 0

    return best_r, best_score


def apply_sara_decisions(projects: list[dict], dry_run: bool = False) -> int:
    """
    Match QLD DA projects to cached SARA decisions.
    Returns count of projects updated.
    """
    if not SARA_FILE.exists():
        print("  [QLD SARA] Cache not found — run scripts/fetch_sara_decisions.py first")
        return 0

    sara_all = json.loads(SARA_FILE.read_text(encoding="utf-8"))

    # Split: MCU original approvals vs currency-extension records
    mcu_records = [
        r for r in sara_all
        if "Material change of use" in (r.get("natureOfDevelopment") or "")
        and "Post-approval" not in (r.get("developmentApplicationType") or "")
    ]
    extension_records = [
        r for r in sara_all
        if r.get("natureOfDevelopment", "").strip() == "Extend period currency"
    ]

    mcu_corpus = _build_corpus(mcu_records)
    ext_corpus  = _build_corpus(extension_records)

    # QLD DA projects that are still in a proposed/unknown stage
    qld_proposed = [
        p for p in projects
        if "QLD_DA" in p.get("source", "")
        and p.get("state") == "QLD"
        and p.get("stage") not in ("Existing", "Committed")
    ]

    today = date.today()
    updated = 0
    expired_count = 0

    print(f"\n=== QLD SARA decisions supplement ({len(qld_proposed)} proposed QLD DA projects) ===")

    for p in qld_proposed:
        sara_r, score = _find_best_match(p, mcu_corpus)
        if not sara_r:
            continue

        fd_str = (sara_r.get("finalisedDate") or "")[:10]
        if not fd_str:
            continue

        try:
            approved = date.fromisoformat(fd_str)
        except ValueError:
            continue

        age_years = (today - approved).days / 365.25

        # Check for a currency extension for this project
        ext_r, _ = _find_best_match(p, ext_corpus, min_score=2)
        has_extension = ext_r is not None

        # Only expire projects whose stage comes solely from QLD_DA.
        # If NEM or KCI contributed, their stage information is more authoritative.
        source = p.get("source") or ""
        qld_da_only = source == "QLD_DA" or (
            "QLD_DA" in source
            and "NEM" not in source
            and "KCI" not in source
            and "CER" not in source
        )

        is_expired = age_years >= EXPIRY_YEARS and not has_extension and qld_da_only

        changed = False

        # Always store the approval date (regardless of source)
        if not p.get("sara_decision_date"):
            if not dry_run:
                p["sara_decision_date"] = fd_str
            changed = True

        # Mark expired
        if is_expired and p.get("stage") not in ("Existing", "Committed", "Expired"):
            if not dry_run:
                p["stage"] = "Expired"
            expired_count += 1
            changed = True
            ext_note = " (has extension)" if has_extension else ""
            print(f"  EXPIRED: {p['site_name']:<50s}  approved={fd_str}  "
                  f"({age_years:.1f}yr)  score={score}{ext_note}")
        elif changed:
            pass  # date stored silently

        if changed:
            updated += 1

    print(f"  Stored approval dates for {updated} projects; marked {expired_count} as Expired")
    return updated
