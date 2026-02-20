import re
import streamlit as st

# =========================
# REACT: Radionuclide Therapy Toxicity Tool
# CTCAE v5.0 grading + FDA label-inspired dose-mod guidance
# Educational use only
# =========================

st.set_page_config(page_title="REACT Toxicity Tool", layout="wide")

# -------------------------
# Session state: acknowledgment
# -------------------------
if "acknowledged" not in st.session_state:
    st.session_state["acknowledged"] = False

if not st.session_state["acknowledged"]:
    st.warning(
        "⚠️ **IMPORTANT DISCLAIMER**\n\n"
        "This application is for educational and guidance purposes only. "
        "All results should be independently verified by qualified healthcare professionals. "
        "This tool does not replace clinical judgment or official prescribing information."
    )
    if st.button("I Acknowledge and Understand"):
        st.session_state["acknowledged"] = True
        st.rerun()

if not st.session_state["acknowledged"]:
    st.stop()

# -------------------------
# Helpers
# -------------------------
def parse_float(text: str):
    """Parse user text to float; empty/invalid -> None."""
    if text is None:
        return None
    s = str(text).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None

def normalize_grade_string(s: str):
    """
    Extract (op, n) from strings like:
      "Grade 2", "Grade ≥ 3", "Grade >=3", "Grade 3-4"
    Returns (op, n) where op is "=" or ">=" or None.
    """
    if not s:
        return None, None
    s = str(s)

    m_range = re.search(r"Grade\s*(\d+)\s*-\s*(\d+)", s)
    if m_range:
        return ">=", int(m_range.group(1))

    m = re.search(r"Grade\s*([≥>=]*)\s*(\d+)", s)
    if not m:
        return None, None

    op = m.group(1)
    n = int(m.group(2))
    if "≥" in op or ">=" in op:
        return ">=", n
    return "=", n

def pick_guidance(type_modifications: dict, grade_or_condition: str):
    """Deterministic guidance selection: exact match -> grade-aware threshold -> None."""
    if not type_modifications:
        return None

    if grade_or_condition in type_modifications:
        return type_modifications[grade_or_condition]

    op_q, n_q = normalize_grade_string(grade_or_condition)
    if n_q is not None:
        # Non-recurrent first
        best = None
        best_thresh = None
        for k, v in type_modifications.items():
            if "Recurrent" in k:
                continue
            op_k, n_k = normalize_grade_string(k)
            if n_k is None:
                continue
            if op_k == "=" and n_q == n_k:
                return v
            if op_k == ">=" and n_q >= n_k:
                if best_thresh is None or n_k > best_thresh:
                    best = v
                    best_thresh = n_k
        if best is not None:
            return best

        # Recurrent second
        best = None
        best_thresh = None
        for k, v in type_modifications.items():
            if "Recurrent" not in k:
                continue
            op_k, n_k = normalize_grade_string(k)
            if op_k == ">=" and n_q >= n_k:
                if best_thresh is None or n_k > best_thresh:
                    best = v
                    best_thresh = n_k
        if best is not None:
            return best

    return None

# -------------------------
# Unit normalization (to CTCAE units)
# CTCAE thresholds here are implemented in:
#   - Platelets: /mm^3 (same as /uL) numeric thresholds like 75,000
#   - WBC: /mm^3 numeric thresholds like 3,000
#   - ANC: /mm^3 numeric thresholds like 1,500
#
# Many clinical workflows enter:
#   - Platelets as K/uL (e.g., 100)
#   - WBC as K/uL (e.g., 2.0)
#   - ANC as K/uL (e.g., 4.0)
#
# We'll let the user choose their input unit system and normalize internally.
# -------------------------
def to_cells_per_uL_from_k(value_k):
    """Convert K/uL to /uL."""
    if value_k is None:
        return None
    return float(value_k) * 1000.0

def normalize_platelets(value, unit_mode: str):
    """
    unit_mode:
      - "K/uL" expects values like 100 (meaning 100,000/uL)
      - "/uL" expects values like 100000
    """
    if value is None:
        return None
    if unit_mode == "K/uL":
        return to_cells_per_uL_from_k(value)
    return float(value)

def normalize_wbc(value, unit_mode: str):
    if value is None:
        return None
    if unit_mode == "K/uL":
        return to_cells_per_uL_from_k(value)
    return float(value)

def normalize_anc(value, unit_mode: str):
    if value is None:
        return None
    if unit_mode == "K/uL":
        return to_cells_per_uL_from_k(value)
    return float(value)

def normalize_lln_cells(value, unit_mode: str):
    """LLN inputs for platelets/WBC/ANC in same unit mode as labs; normalize to /uL."""
    if value is None:
        return None
    if unit_mode == "K/uL":
        return to_cells_per_uL_from_k(value)
    return float(value)

# -------------------------
# CTCAE v5.0-like numeric grading (LLN-based for cytopenias)
# -------------------------
ctcae_criteria = {
    "Anemia": {
        "Grade 1": {"Hemoglobin": {"lt_lln_required": True, "min": 10.0, "max": None}},  # <LLN to 10
        "Grade 2": {"Hemoglobin": {"min": 8.0, "max": 9.999}},   # <10 to 8
        "Grade 3": {"Hemoglobin": {"min": 0.0, "max": 7.999}},  # <8
    },
    "Thrombocytopenia": {
        "Grade 1": {"Platelet": {"lt_lln_required": True, "min": 75000, "max": None}},  # <LLN to 75k
        "Grade 2": {"Platelet": {"min": 50000, "max": 74999}},
        "Grade 3": {"Platelet": {"min": 25000, "max": 49999}},
        "Grade 4": {"Platelet": {"min": 0, "max": 24999}},
    },
    "Leukopenia": {
        "Grade 1": {"WBC": {"lt_lln_required": True, "min": 3000, "max": None}},  # <LLN to 3000
        "Grade 2": {"WBC": {"min": 2000, "max": 2999}},
        "Grade 3": {"WBC": {"min": 1000, "max": 1999}},
        "Grade 4": {"WBC": {"min": 0, "max": 999}},
    },
    "Neutropenia": {
        "Grade 1": {"ANC": {"lt_lln_required": True, "min": 1500, "max": None}},  # <LLN to 1500
        "Grade 2": {"ANC": {"min": 1000, "max": 1499}},
        "Grade 3": {"ANC": {"min": 500, "max": 999}},
        "Grade 4": {"ANC": {"min": 0, "max": 499}},
    },
}

def determine_ctcae_grade(parameter: str, value, lln_map=None):
    """Determine CTCAE grade for a parameter using numeric criteria + LLN gating when required."""
    if value is None:
        return None
    if parameter not in ctcae_criteria:
        return None

    grade_hits = []
    grade_order = ["Grade 1", "Grade 2", "Grade 3", "Grade 4"]

    for grade, limits in ctcae_criteria[parameter].items():
        for lab, t in limits.items():
            if t.get("lt_lln_required"):
                if not lln_map or lab not in lln_map or lln_map[lab] is None:
                    continue
                if value >= lln_map[lab]:
                    continue

            min_ok = True if t.get("min") is None else (value >= t["min"])
            max_ok = True if t.get("max") is None else (value <= t["max"])
            if min_ok and max_ok:
                grade_hits.append(grade)

    for g in reversed(grade_order):
        if g in grade_hits:
            return g
    return None

def ctcae_creatinine_increase_grade(baseline_cr, current_cr, uln_cr):
    """
    Numeric implementation of CTCAE-like "Creatinine increased":
      - If baseline <= ULN (or unknown): grade by multiple of ULN
      - If baseline > ULN: grade by multiple of baseline
    """
    if current_cr is None or uln_cr is None or uln_cr <= 0:
        return None
    base = baseline_cr if baseline_cr is not None else None

    if base is None or base <= uln_cr:
        ref = uln_cr
    else:
        ref = base

    ratio = current_cr / ref if ref > 0 else None
    if ratio is None:
        return None

    if ratio > 6.0:
        return "Grade 4"
    if ratio > 3.0:
        return "Grade 3"
    if ratio > 1.5:
        return "Grade 2"
    if ratio > 1.0:
        return "Grade 1"
    return None

# -------------------------
# FDA-label-inspired dose modification guidance (educational; verify current label)
# -------------------------
dose_modifications = {
    "LUTATHERA": {
        "Thrombocytopenia": {
            "Grade 2": "Withhold dose until resolution to Grade 0–1. Resume at 3.7 GBq if resolved. If no recurrence, may return to 7.4 GBq. Recurrent Grade 2–4: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "Grade 3": "Withhold dose until resolution to Grade 0–1. Resume at 3.7 GBq if resolved. If no recurrence, may return to 7.4 GBq. Recurrent Grade 2–4: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "Grade 4": "Withhold dose until resolution to Grade 0–1. Resume at 3.7 GBq if resolved. If no recurrence, may return to 7.4 GBq. Recurrent Grade 2–4: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "Recurrent Grade ≥ 2": "Permanently discontinue LUTATHERA.",
        },
        "Anemia": {
            "Grade 3": "Withhold dose until resolution to Grade 0–2. Resume at 3.7 GBq if resolved. If no recurrence, may return to 7.4 GBq. Recurrent Grade 3–4: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "Grade 4": "Withhold dose until resolution to Grade 0–2. Resume at 3.7 GBq if resolved. If no recurrence, may return to 7.4 GBq. Recurrent Grade 3–4: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "Recurrent Grade ≥ 3": "Permanently discontinue LUTATHERA.",
        },
        "Neutropenia": {
            "Grade 3": "Withhold dose until resolution to Grade 0–2. Resume at 3.7 GBq if resolved. If no recurrence, may return to 7.4 GBq. Recurrent Grade 3–4: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "Grade 4": "Withhold dose until resolution to Grade 0–2. Resume at 3.7 GBq if resolved. If no recurrence, may return to 7.4 GBq. Recurrent Grade 3–4: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "Recurrent Grade ≥ 3": "Permanently discontinue LUTATHERA.",
        },
        "Leukopenia": {
            "Grade 2": "Withhold dose until resolution to Grade 0–1. Resume at 3.7 GBq if resolved. If no recurrence, may return to 7.4 GBq. Recurrent Grade 2–4: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "Grade 3": "Withhold dose until resolution to Grade 0–1. Resume at 3.7 GBq if resolved. If no recurrence, may return to 7.4 GBq. Recurrent Grade 2–4: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "Grade 4": "Withhold dose until resolution to Grade 0–1. Resume at 3.7 GBq if resolved. If no recurrence, may return to 7.4 GBq. Recurrent Grade 2–4: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "Recurrent Grade ≥ 2": "Permanently discontinue LUTATHERA.",
        },
        "Renal Toxicity": {
            "CLcr < 40 mL/min": "Withhold dose until resolution or return to baseline. Resume at 3.7 GBq if resolved. Recurrent renal toxicity: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "≥40% increase from baseline creatinine": "Withhold dose until resolution or return to baseline. Resume at 3.7 GBq if resolved. Recurrent renal toxicity: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "≥40% decrease from baseline CLcr": "Withhold dose until resolution or return to baseline. Resume at 3.7 GBq if resolved. Recurrent renal toxicity: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "Recurrent renal toxicity": "Permanently discontinue LUTATHERA.",
        },
        "Hepatotoxicity": {
            "Bilirubin > 3x ULN": "Withhold dose until resolution or return to baseline. Resume at 3.7 GBq if resolved. Recurrent hepatotoxicity: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "Albumin < 30 g/L with INR > 1.5": "Withhold dose until resolution or return to baseline. Resume at 3.7 GBq if resolved. Recurrent hepatotoxicity: permanently discontinue. If dose delayed >16 weeks due to toxicity: permanently discontinue.",
            "Recurrent hepatotoxicity": "Permanently discontinue LUTATHERA.",
        },
    },
    "PLUVICTO": {
        "Myelosuppression": {
            "Grade 2": "Withhold PLUVICTO until improvement to Grade 1 or baseline.",
            "Grade ≥ 3": "Withhold PLUVICTO until improvement to Grade 1 or baseline. Reduce dose by 20% to 5.9 GBq (160 mCi).",
            "Recurrent Grade ≥ 3 after one dose reduction": "Permanently discontinue PLUVICTO.",
        },
        "Renal Toxicity": {
            "Confirmed creatinine Grade ≥ 2 OR CLcr < 30": "Withhold PLUVICTO until improvement.",
            "≥40% creatinine increase AND >40% CLcr decrease": "Withhold PLUVICTO until improvement or return to baseline. Reduce dose by 20% to 5.9 GBq (160 mCi).",
            "Grade ≥ 3 renal toxicity": "Permanently discontinue PLUVICTO.",
            "Recurrent renal toxicity after one dose reduction": "Permanently discontinue PLUVICTO.",
        },
        "Dry Mouth": {
            "Grade 2": "Withhold PLUVICTO until improvement or return to baseline. Consider reducing dose by 20% to 5.9 GBq (160 mCi).",
            "Grade 3": "Withhold PLUVICTO until improvement or return to baseline. Reduce dose by 20% to 5.9 GBq (160 mCi).",
            "Recurrent Grade 3 after one dose reduction": "Permanently discontinue PLUVICTO.",
        },
        "Gastrointestinal toxicity": {
            "Grade ≥ 3 (not amenable to medical intervention)": "Withhold PLUVICTO until improvement to Grade 2 or baseline. Reduce dose by 20% to 5.9 GBq (160 mCi).",
            "Recurrent Grade ≥ 3 after one dose reduction": "Permanently discontinue PLUVICTO.",
        },
        "Fatigue": {"Grade ≥ 3": "Withhold PLUVICTO until improvement to Grade 2 or baseline."},
        "Electrolyte or metabolic abnormalities": {"Grade ≥ 2": "Withhold PLUVICTO until improvement to Grade 1 or baseline."},
        "Treatment delay > 4 weeks": {"Any": "Permanently discontinue PLUVICTO."},
        "Other non-hematologic toxicity": {
            "Any recurrent Grade 3 or 4 OR persistent/intolerable Grade 2 after one dose reduction": "Permanently discontinue PLUVICTO."
        },
        "Any unacceptable toxicity": {"Any": "Permanently discontinue PLUVICTO."},
    },
}

# -------------------------
# Toxicity assessment functions
# -------------------------
def assess_lutathera_renal(baseline_cr, current_cr, baseline_clcr, current_clcr):
    issues = []
    if current_clcr is not None and current_clcr < 40:
        issues.append("CLcr < 40 mL/min")
    if baseline_cr is not None and current_cr is not None and baseline_cr > 0:
        if (current_cr / baseline_cr) >= 1.4:
            issues.append("≥40% increase from baseline creatinine")
    if baseline_clcr is not None and current_clcr is not None and baseline_clcr > 0:
        frac_decrease = (baseline_clcr - current_clcr) / baseline_clcr
        if frac_decrease >= 0.40:
            issues.append("≥40% decrease from baseline CLcr")
    return issues

def assess_pluvicto_renal(baseline_cr, current_cr, uln_cr, baseline_clcr, current_clcr):
    issues = []
    cr_grade = ctcae_creatinine_increase_grade(baseline_cr, current_cr, uln_cr)
    _, n = normalize_grade_string(cr_grade) if cr_grade else (None, None)

    # Hold triggers
    if current_clcr is not None and current_clcr < 30:
        issues.append("Confirmed creatinine Grade ≥ 2 OR CLcr < 30")
    elif n is not None and n >= 2:
        issues.append("Confirmed creatinine Grade ≥ 2 OR CLcr < 30")

    # Dose reduction combo trigger
    if baseline_cr is not None and current_cr is not None and baseline_cr > 0:
        cr_increase = current_cr / baseline_cr
        if cr_increase >= 1.4:
            if baseline_clcr is not None and current_clcr is not None and baseline_clcr > 0:
                clcr_decrease = (baseline_clcr - current_clcr) / baseline_clcr
                if clcr_decrease > 0.40:
                    issues.append("≥40% creatinine increase AND >40% CLcr decrease")

    # Discontinue trigger (renal Grade ≥ 3)
    if n is not None and n >= 3:
        issues.append("Grade ≥ 3 renal toxicity")

    return issues, cr_grade

def assess_lutathera_hepatic(bilirubin, uln_bilirubin, albumin_g_l, inr):
    issues = []
    if bilirubin is not None and uln_bilirubin is not None and uln_bilirubin > 0:
        if bilirubin > 3.0 * uln_bilirubin:
            issues.append("Bilirubin > 3x ULN")
    if albumin_g_l is not None and inr is not None:
        if albumin_g_l < 30 and inr > 1.5:
            issues.append("Albumin < 30 g/L with INR > 1.5")
    return issues

def grade_to_num(grade_str):
    _, n = normalize_grade_string(grade_str)
    return n

# -------------------------
# UI
# -------------------------
st.title("🩺 REACT: Radiotheranostic Evaluation & Assessment for Clinical Toxicity")
st.markdown("**CTCAE v5.0 grading + FDA label-inspired dose modification guidance (educational)**")

drug = st.selectbox("**Select Radionuclide Therapy**", options=["LUTATHERA", "PLUVICTO"], key="drug_selection")

st.markdown("---")
st.subheader("🧮 Input Units (so entries match typical workflow)")

unit_mode = st.radio(
    "Choose how you enter CBC values:",
    options=["K/uL (typical: Plt 100, WBC 2.0, ANC 4.0)", "/uL (absolute: Plt 100000, WBC 2000, ANC 4000)"],
    index=0,
    horizontal=True
)
cbc_units = "K/uL" if unit_mode.startswith("K/uL") else "/uL"

st.caption(
    "Internally, the app normalizes to **/uL** for CTCAE grading. "
    "Switch units if your lab feed or workflow uses absolute counts."
)

st.markdown("---")
st.subheader("📊 Laboratory Values")

colA, colB = st.columns(2)

with colA:
    st.markdown("### Hematology")
    hgb_txt = st.text_input("Hemoglobin (g/dL)", value="", placeholder="e.g., 10.8")

    if cbc_units == "K/uL":
        plt_label = "Platelets (K/uL) — typical: 100"
        wbc_label = "WBC (K/uL) — typical: 2.0"
        anc_label = "ANC (K/uL) — typical: 4.0"
        plt_ph, wbc_ph, anc_ph = "e.g., 100", "e.g., 2.0", "e.g., 4.0"
    else:
        plt_label = "Platelets (/uL) — typical: 100000"
        wbc_label = "WBC (/uL) — typical: 2000"
        anc_label = "ANC (/uL) — typical: 4000"
        plt_ph, wbc_ph, anc_ph = "e.g., 100000", "e.g., 2000", "e.g., 4000"

    plt_txt = st.text_input(plt_label, value="", placeholder=plt_ph)
    wbc_txt = st.text_input(wbc_label, value="", placeholder=wbc_ph)
    anc_txt = st.text_input(anc_label, value="", placeholder=anc_ph)

with colB:
    st.markdown("### Renal")
    baseline_cr_txt = st.text_input("Baseline Creatinine (mg/dL)", value="", placeholder="e.g., 1.0")
    current_cr_txt = st.text_input("Current Creatinine (mg/dL)", value="", placeholder="e.g., 1.5")
    uln_cr_txt = st.text_input("ULN Creatinine (mg/dL)", value="1.2", placeholder="e.g., 1.2")
    baseline_clcr_txt = st.text_input("Baseline Creatinine Clearance (mL/min)", value="", placeholder="e.g., 85")
    current_clcr_txt = st.text_input("Current Creatinine Clearance (mL/min)", value="", placeholder="e.g., 55")

st.markdown("### Reference Ranges (LLN)")
st.caption(
    "Grade 1 cytopenias in CTCAE require values **below LLN**. "
    "Enter LLN in the **same units** you selected above for CBC values."
)

colLLN1, colLLN2, colLLN3, colLLN4 = st.columns(4)
with colLLN1:
    hgb_lln_txt = st.text_input("Hgb (g/dL)", value="10.0")
with colLLN2:
    if cbc_units == "K/uL":
        plt_lln_txt = st.text_input("Platelet (K/uL)", value="150")
    else:
        plt_lln_txt = st.text_input("Platelet (/uL)", value="150000")
with colLLN3:
    if cbc_units == "K/uL":
        wbc_lln_txt = st.text_input("WBC (K/uL)", value="3.0")
    else:
        wbc_lln_txt = st.text_input("WBC (/uL)", value="3000")
with colLLN4:
    if cbc_units == "K/uL":
        anc_lln_txt = st.text_input("ANC (K/uL)", value="1.5")
    else:
        anc_lln_txt = st.text_input("ANC (/uL)", value="1500")

st.markdown("### Hepatic")
colH1, colH2 = st.columns(2)
with colH1:
    bili_txt = st.text_input("Total Bilirubin (mg/dL)", value="", placeholder="e.g., 1.1")
    uln_bili_txt = st.text_input("ULN Bilirubin (mg/dL)", value="1.0", placeholder="e.g., 1.0")
with colH2:
    alb_txt = st.text_input("Albumin (g/L)", value="", placeholder="e.g., 38")
    inr_txt = st.text_input("INR", value="", placeholder="e.g., 1.1")

# PLUVICTO extras
pluvicto_extras = {}
if drug == "PLUVICTO":
    st.markdown("---")
    st.subheader("🧩 PLUVICTO Additional Assessments (optional)")
    colP1, colP2, colP3 = st.columns(3)
    with colP1:
        pluvicto_extras["dry_mouth_grade"] = st.selectbox("Dry Mouth Grade", options=[None, 1, 2, 3], index=0)
        pluvicto_extras["fatigue_grade"] = st.selectbox("Fatigue Grade", options=[None, 1, 2, 3, 4], index=0)
    with colP2:
        pluvicto_extras["gi_grade"] = st.selectbox("GI Toxicity Grade", options=[None, 1, 2, 3, 4], index=0)
        pluvicto_extras["gi_amenable"] = st.selectbox("GI toxicity amenable to medical intervention?", options=["Yes", "No"], index=0)
    with colP3:
        pluvicto_extras["electrolyte_grade"] = st.selectbox("Electrolyte/Metabolic Abnormality Grade", options=[None, 1, 2, 3, 4], index=0)
        pluvicto_extras["treatment_delay_weeks"] = st.text_input("Treatment delay (weeks) due to toxicity", value="", placeholder="e.g., 0")

lutathera_delay_weeks_txt = ""
if drug == "LUTATHERA":
    st.markdown("---")
    st.subheader("🧩 LUTATHERA Timing (optional)")
    lutathera_delay_weeks_txt = st.text_input("Dose delay (weeks) due to toxicity (if applicable)", value="", placeholder="e.g., 0")

st.markdown("---")

# -------------------------
# Analyze
# -------------------------
if st.button("🔍 **Analyze Laboratory Values**", type="primary"):
    # Parse raw (as entered)
    hgb_in = parse_float(hgb_txt)
    plt_in = parse_float(plt_txt)
    wbc_in = parse_float(wbc_txt)
    anc_in = parse_float(anc_txt)

    baseline_creatinine = parse_float(baseline_cr_txt)
    current_creatinine = parse_float(current_cr_txt)
    uln_creatinine = parse_float(uln_cr_txt)
    baseline_clcr = parse_float(baseline_clcr_txt)
    current_clcr = parse_float(current_clcr_txt)

    bilirubin = parse_float(bili_txt)
    uln_bilirubin = parse_float(uln_bili_txt)
    albumin = parse_float(alb_txt)
    inr = parse_float(inr_txt)

    # LLNs (as entered, may be K/uL for CBC values)
    hgb_lln = parse_float(hgb_lln_txt)
    plt_lln_in = parse_float(plt_lln_txt)
    wbc_lln_in = parse_float(wbc_lln_txt)
    anc_lln_in = parse_float(anc_lln_txt)

    # Normalize CBC values to /uL for CTCAE grading
    hemoglobin = hgb_in  # g/dL stays the same
    platelet = normalize_platelets(plt_in, cbc_units)   # /uL
    wbc = normalize_wbc(wbc_in, cbc_units)              # /uL
    anc = normalize_anc(anc_in, cbc_units)              # /uL

    # Normalize LLNs for CBC to /uL
    plt_lln = normalize_lln_cells(plt_lln_in, cbc_units)
    wbc_lln = normalize_lln_cells(wbc_lln_in, cbc_units)
    anc_lln = normalize_lln_cells(anc_lln_in, cbc_units)

    lln_map = {"Hemoglobin": hgb_lln, "Platelet": plt_lln, "WBC": wbc_lln, "ANC": anc_lln}

    # Determine if anything entered
    has_values = any([
        hemoglobin is not None,
        platelet is not None,
        wbc is not None,
        anc is not None,
        current_creatinine is not None,
        current_clcr is not None,
        bilirubin is not None,
        albumin is not None,
        inr is not None
    ])

    if drug == "PLUVICTO":
        has_values = has_values or any([
            pluvicto_extras.get("dry_mouth_grade") is not None,
            pluvicto_extras.get("fatigue_grade") is not None,
            pluvicto_extras.get("gi_grade") is not None,
            pluvicto_extras.get("electrolyte_grade") is not None,
            parse_float(pluvicto_extras.get("treatment_delay_weeks", "")) not in (None, 0.0),
        ])

    if drug == "LUTATHERA":
        has_values = has_values or (parse_float(lutathera_delay_weeks_txt) not in (None, 0.0))

    if not has_values:
        st.error("⚠️ Please enter at least one value to analyze.")
        st.stop()

    detected_issues = []
    supporting_heme = []

    # Hematology grading
    if hemoglobin is not None:
        g = determine_ctcae_grade("Anemia", hemoglobin, lln_map)
        if g:
            supporting_heme.append(("Anemia", g, hemoglobin))
    if platelet is not None:
        g = determine_ctcae_grade("Thrombocytopenia", platelet, lln_map)
        if g:
            supporting_heme.append(("Thrombocytopenia", g, platelet))
    if wbc is not None:
        g = determine_ctcae_grade("Leukopenia", wbc, lln_map)
        if g:
            supporting_heme.append(("Leukopenia", g, wbc))
    if anc is not None:
        g = determine_ctcae_grade("Neutropenia", anc, lln_map)
        if g:
            supporting_heme.append(("Neutropenia", g, anc))

    # Renal assessment
    cr_ctcae_grade = None
    if drug == "LUTATHERA":
        renal_issues = assess_lutathera_renal(baseline_creatinine, current_creatinine, baseline_clcr, current_clcr)
        for issue in renal_issues:
            detected_issues.append(("Renal Toxicity", issue, None))

    if drug == "PLUVICTO":
        renal_issues, cr_ctcae_grade = assess_pluvicto_renal(
            baseline_creatinine, current_creatinine, uln_creatinine, baseline_clcr, current_clcr
        )
        for issue in renal_issues:
            detected_issues.append(("Renal Toxicity", issue, cr_ctcae_grade))

    # Hepatic assessment (used primarily for LUTATHERA triggers included in this tool)
    hepatic_issues = assess_lutathera_hepatic(bilirubin, uln_bilirubin, albumin, inr)
    for issue in hepatic_issues:
        detected_issues.append(("Hepatotoxicity", issue, None))

    # PLUVICTO extras
    if drug == "PLUVICTO":
        dry = pluvicto_extras.get("dry_mouth_grade")
        if dry is not None and dry >= 2:
            detected_issues.append(("Dry Mouth", f"Grade {dry}", None))

        fatigue = pluvicto_extras.get("fatigue_grade")
        if fatigue is not None and fatigue >= 3:
            detected_issues.append(("Fatigue", "Grade ≥ 3", None))

        gi = pluvicto_extras.get("gi_grade")
        gi_amenable = pluvicto_extras.get("gi_amenable")
        if gi is not None and gi >= 3 and gi_amenable == "No":
            detected_issues.append(("Gastrointestinal toxicity", "Grade ≥ 3 (not amenable to medical intervention)", None))

        elec = pluvicto_extras.get("electrolyte_grade")
        if elec is not None and elec >= 2:
            detected_issues.append(("Electrolyte or metabolic abnormalities", "Grade ≥ 2", None))

        delay_weeks = parse_float(pluvicto_extras.get("treatment_delay_weeks", ""))
        if delay_weeks is not None and delay_weeks > 4:
            detected_issues.append(("Treatment delay > 4 weeks", "Any", delay_weeks))

    # LUTATHERA delay >16 weeks note (optional)
    if drug == "LUTATHERA":
        delay_weeks = parse_float(lutathera_delay_weeks_txt)
        if delay_weeks is not None and delay_weeks > 16:
            detected_issues.append(("Dose delayed > 16 weeks", "Any", delay_weeks))

    # Group myelosuppression for PLUVICTO
    if drug == "PLUVICTO" and supporting_heme:
        heme_grades = [grade_to_num(g) for _, g, _ in supporting_heme if grade_to_num(g) is not None]
        if heme_grades:
            highest = max(heme_grades)
            if highest >= 2:
                detected_issues.append((
                    "Myelosuppression",
                    "Grade 2" if highest == 2 else "Grade ≥ 3",
                    supporting_heme
                ))

    # Individual heme issues for LUTATHERA (label-triggered grades only)
    if drug == "LUTATHERA":
        for tox, g, v in supporting_heme:
            n = grade_to_num(g)
            if tox == "Thrombocytopenia" and n is not None and n >= 2:
                detected_issues.append(("Thrombocytopenia", g, [("Platelets", g, v)]))
            if tox == "Anemia" and n is not None and n >= 3:
                detected_issues.append(("Anemia", g, [("Hemoglobin", g, v)]))
            if tox == "Neutropenia" and n is not None and n >= 3:
                detected_issues.append(("Neutropenia", g, [("ANC", g, v)]))
            if tox == "Leukopenia" and n is not None and n >= 2:
                detected_issues.append(("Leukopenia", g, [("WBC", g, v)]))

    # -------------------------
    # Display results
    # -------------------------
    if detected_issues:
        st.success(f"✅ **Analysis Complete**: Found {len(detected_issues)} issue(s) to review")

        # Show normalized interpretation (quick audit trail)
        with st.expander("🔎 Input normalization (how your entries were interpreted)", expanded=False):
            st.markdown("**CBC units selected:** " + cbc_units)
            if platelet is not None:
                st.markdown(f"• Platelets interpreted as **{int(round(platelet)):,} /uL**")
            if wbc is not None:
                st.markdown(f"• WBC interpreted as **{int(round(wbc)):,} /uL**")
            if anc is not None:
                st.markdown(f"• ANC interpreted as **{int(round(anc)):,} /uL**")
            if plt_lln is not None:
                st.markdown(f"• Platelet LLN interpreted as **{int(round(plt_lln)):,} /uL**")
            if wbc_lln is not None:
                st.markdown(f"• WBC LLN interpreted as **{int(round(wbc_lln)):,} /uL**")
            if anc_lln is not None:
                st.markdown(f"• ANC LLN interpreted as **{int(round(anc_lln)):,} /uL**")

        st.markdown("---")
        st.subheader("📋 Dose Modification Recommendations (educational)")

        drug_modifications = dose_modifications.get(drug, {})

        for i, (issue_type, grade_or_condition, details) in enumerate(detected_issues, 1):
            title = f"**{i}. {issue_type}: {grade_or_condition}**"
            with st.expander(title, expanded=True):
                # LUTATHERA delay special-case
                if drug == "LUTATHERA" and issue_type == "Dose delayed > 16 weeks":
                    st.error("⛔ **Dose delay >16 weeks due to toxicity** is a discontinuation criterion in LUTATHERA dose-mod tables.")
                    st.markdown(f"**Entered delay (weeks):** {details}")
                    continue

                guidance = None
                if issue_type in drug_modifications:
                    guidance = pick_guidance(drug_modifications[issue_type], grade_or_condition)

                if guidance:
                    st.markdown(f"**📝 Recommendation:** {guidance}")
                else:
                    st.warning("⚠️ No specific dose modification guidance matched. Verify in the current FDA label.")

                # Supporting info
                if details is not None:
                    if isinstance(details, list):
                        st.markdown("**Supporting Data:**")
                        for a, b, c in details:
                            if c is None:
                                st.markdown(f"• {a}: {b}")
                            else:
                                # Show CBC values in the user's unit mode (friendlier)
                                if a in ("Platelets", "WBC", "ANC"):
                                    if cbc_units == "K/uL":
                                        c_disp = c / 1000.0
                                        st.markdown(f"• {a}: {c_disp:g} K/uL ({b})")
                                    else:
                                        st.markdown(f"• {a}: {int(round(c)):,} /uL ({b})")
                                else:
                                    st.markdown(f"• {a}: {c} ({b})")
                    else:
                        st.markdown(f"**Value/Detail:** {details}")

        st.markdown("---")
        st.info(
            "ℹ️ **Important Notes**\n"
            "• Recommendations are educational and must be verified against the current FDA prescribing information.\n"
            "• CTCAE grading may require clinical context (symptoms, transfusion indicated, life-threatening criteria).\n"
            "• Reassess prior to each cycle and integrate the patient’s overall condition."
        )
    else:
        st.success("✅ **No dose-modification triggers detected** from the values entered (per this tool’s rules).")
        st.info("Continue standard monitoring and reassess before the next cycle.")

# Footer
st.markdown("---")
st.caption("⚠️ Educational tool. Does not replace clinical judgment or official prescribing information.")
