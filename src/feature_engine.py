"""
feature_engine.py — Multi-Dimensional Feature Extraction

Extracts 50+ features per candidate across 6 dimensions:
  1. Role Fit      — Title, career trajectory, company type
  2. Skills Match  — Semantic skill matching with anti-keyword-stuffing
  3. Career Quality — Production experience, stability, depth
  4. Behavioral    — Platform engagement, responsiveness, availability
  5. Education     — Field relevance, institution tier
  6. Logistics     — Location, notice period, work mode
"""

import re
import math
from datetime import datetime, date

from src.config import (
    SKILL_CATEGORIES,
    NEGATIVE_SKILL_NAMES,
    STRONG_POSITIVE_TITLE_KEYWORDS,
    MODERATE_POSITIVE_TITLE_KEYWORDS,
    NEGATIVE_TITLE_KEYWORDS,
    CONSULTING_SERVICES_FIRMS,
    PRODUCT_COMPANIES,
    FICTIONAL_COMPANIES,
    EXP_IDEAL_MIN, EXP_IDEAL_MAX,
    EXP_ACCEPTABLE_MIN, EXP_ACCEPTABLE_MAX,
    PREFERRED_CITIES, GOOD_CITIES, INDIA_KEYWORDS,
    RECENCY_EXCELLENT_DAYS, RECENCY_GOOD_DAYS, RECENCY_STALE_DAYS,
    NOTICE_IDEAL_DAYS, NOTICE_ACCEPTABLE_DAYS, NOTICE_PENALTY_DAYS,
    RESPONSE_RATE_GOOD, RESPONSE_RATE_MINIMUM,
    PRODUCTION_ML_KEYWORDS, NON_PRODUCTION_KEYWORDS,
    STRONG_FIELDS, MODERATE_FIELDS, WEAK_FIELDS, TIER_SCORES,
)

# Reference date for recency calculations
REFERENCE_DATE = date(2026, 6, 1)


def _normalize(score, min_val=0.0, max_val=1.0):
    """Clamp score to [min_val, max_val]."""
    return max(min_val, min(max_val, score))


def _title_contains(title_lower, keywords):
    """Check if any keyword is a substring of the title."""
    return any(kw in title_lower for kw in keywords)


def _company_is_consulting(company_name):
    """Check if company is a known consulting/services firm."""
    name = company_name.lower().strip()
    return any(firm in name for firm in CONSULTING_SERVICES_FIRMS)


def _company_is_product(company_name):
    """Check if company is a known product company."""
    name = company_name.lower().strip()
    return any(firm in name for firm in PRODUCT_COMPANIES)


def _company_is_fictional(company_name):
    """Check if company is a fictional/synthetic dataset company."""
    name = company_name.lower().strip()
    return any(firm in name for firm in FICTIONAL_COMPANIES)


# ─────────────────────────────────────────────────────────────────
# 1. ROLE FIT SCORE
# ─────────────────────────────────────────────────────────────────

def compute_role_fit(candidate):
    """
    Score 0-1 based on how well the candidate's role/career matches
    the Senior AI Engineer position.

    Considers:
    - Current title relevance
    - Career history title progression
    - Company type (product vs consulting)
    - Experience band fit
    - Industry relevance
    """
    profile = candidate["profile"]
    career = candidate["career_history"]

    # --- Current title score ---
    current_title = profile.get("current_title", "").lower()
    if _title_contains(current_title, STRONG_POSITIVE_TITLE_KEYWORDS):
        title_score = 1.0
    elif _title_contains(current_title, MODERATE_POSITIVE_TITLE_KEYWORDS):
        title_score = 0.45
    elif _title_contains(current_title, NEGATIVE_TITLE_KEYWORDS):
        title_score = 0.0
    else:
        title_score = 0.15  # Unknown title, small benefit of doubt

    # --- Career history title analysis ---
    career_title_scores = []
    ml_roles_count = 0
    total_ml_months = 0
    consulting_only = True
    has_product_company_exp = False

    for job in career:
        job_title = job.get("title", "").lower()
        company = job.get("company", "")
        duration = job.get("duration_months", 0)

        # Title scoring per role
        if _title_contains(job_title, STRONG_POSITIVE_TITLE_KEYWORDS):
            career_title_scores.append(1.0)
            ml_roles_count += 1
            total_ml_months += duration
        elif _title_contains(job_title, MODERATE_POSITIVE_TITLE_KEYWORDS):
            career_title_scores.append(0.4)
        elif _title_contains(job_title, NEGATIVE_TITLE_KEYWORDS):
            career_title_scores.append(0.0)
        else:
            career_title_scores.append(0.1)

        # Company type analysis
        if not _company_is_consulting(company) and not _company_is_fictional(company):
            consulting_only = False
        if _company_is_product(company):
            has_product_company_exp = True

    avg_career_title = (
        sum(career_title_scores) / len(career_title_scores)
        if career_title_scores else 0.0
    )

    # --- Experience band fit ---
    yoe = profile.get("years_of_experience", 0)
    if EXP_IDEAL_MIN <= yoe <= EXP_IDEAL_MAX:
        exp_score = 1.0
    elif EXP_ACCEPTABLE_MIN <= yoe < EXP_IDEAL_MIN:
        exp_score = 0.5 + 0.5 * (yoe - EXP_ACCEPTABLE_MIN) / (EXP_IDEAL_MIN - EXP_ACCEPTABLE_MIN)
    elif EXP_IDEAL_MAX < yoe <= EXP_ACCEPTABLE_MAX:
        exp_score = 1.0 - 0.5 * (yoe - EXP_IDEAL_MAX) / (EXP_ACCEPTABLE_MAX - EXP_IDEAL_MAX)
    else:
        exp_score = 0.1

    # --- Company type score ---
    if consulting_only and len(career) > 1:
        # JD explicitly penalizes consulting-only careers
        company_score = 0.05
    elif has_product_company_exp:
        company_score = 1.0
    elif consulting_only:
        company_score = 0.15
    else:
        company_score = 0.50  # Unknown companies, neutral

    # --- Career direction (moving toward ML?) ---
    if len(career) >= 2:
        recent_title = career[0].get("title", "").lower()
        oldest_title = career[-1].get("title", "").lower()
        recent_ml = _title_contains(recent_title, STRONG_POSITIVE_TITLE_KEYWORDS)
        old_ml = _title_contains(oldest_title, STRONG_POSITIVE_TITLE_KEYWORDS)

        if recent_ml and not old_ml:
            direction_bonus = 0.15  # Growing into ML — great sign
        elif recent_ml and old_ml:
            direction_bonus = 0.10  # Consistent ML career
        elif not recent_ml and old_ml:
            direction_bonus = -0.10  # Moving away from ML
        else:
            direction_bonus = 0.0
    else:
        direction_bonus = 0.0

    # --- ML role depth bonus ---
    ml_depth_bonus = min(0.2, ml_roles_count * 0.08)

    # Composite
    role_fit = (
        0.30 * title_score +
        0.20 * avg_career_title +
        0.20 * exp_score +
        0.15 * company_score +
        direction_bonus +
        ml_depth_bonus
    )

    return _normalize(role_fit)


# ─────────────────────────────────────────────────────────────────
# 2. SKILLS MATCH SCORE
# ─────────────────────────────────────────────────────────────────

def compute_skills_match(candidate):
    """
    Score 0-1 based on skill relevance, proficiency, and depth.

    Key insight: Anti-keyword-stuffing. Many AI skills + non-technical
    career = keyword stuffer, not genuine AI engineer.
    """
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    profile = candidate["profile"]

    if not skills:
        return 0.0

    # Map proficiency to numeric
    prof_map = {"expert": 1.0, "advanced": 0.75, "intermediate": 0.50, "beginner": 0.25}

    # Categorize skills
    category_scores = {}
    core_skill_count = 0
    negative_skill_count = 0
    total_ai_skill_weight = 0.0

    for skill in skills:
        skill_name = skill.get("name", "").lower().strip()
        proficiency = prof_map.get(skill.get("proficiency", "beginner"), 0.25)
        duration = skill.get("duration_months", 0)
        endorsements = skill.get("endorsements", 0)

        # Check negative skills
        if skill_name in NEGATIVE_SKILL_NAMES:
            negative_skill_count += 1
            continue

        # Match against categories
        matched = False
        for cat_name, cat_info in SKILL_CATEGORIES.items():
            cat_skills = cat_info["skills"]
            cat_weight = cat_info["weight"]

            if any(cs in skill_name or skill_name in cs for cs in cat_skills):
                # Compute skill quality score
                duration_factor = min(1.0, duration / 36)  # 3 years = full credit
                endorsement_factor = min(1.0, endorsements / 20)  # 20 endorsements = full
                quality = (
                    0.40 * proficiency +
                    0.30 * duration_factor +
                    0.15 * endorsement_factor +
                    0.15 * cat_weight
                )

                if cat_name not in category_scores or quality > category_scores[cat_name]:
                    category_scores[cat_name] = quality

                if cat_weight >= 0.70:  # Tier 1 skills
                    core_skill_count += 1
                    total_ai_skill_weight += quality * cat_weight

                matched = True
                break

    # --- Skill assessment scores from Redrob platform ---
    assessments = signals.get("skill_assessment_scores", {})
    assessment_bonus = 0.0
    if assessments:
        high_scores = [v for v in assessments.values() if v >= 70]
        med_scores = [v for v in assessments.values() if 50 <= v < 70]
        assessment_bonus = min(0.15, len(high_scores) * 0.05 + len(med_scores) * 0.02)

    # --- Category coverage score ---
    # How many of the important categories does this candidate cover?
    tier1_categories = [c for c, info in SKILL_CATEGORIES.items() if info["weight"] >= 0.70]
    tier1_covered = sum(1 for c in tier1_categories if c in category_scores)
    coverage_score = tier1_covered / len(tier1_categories) if tier1_categories else 0

    # --- Anti-keyword-stuffing ---
    # If candidate has many AI skills but a non-technical title/career
    current_title = profile.get("current_title", "").lower()
    is_technical_title = (
        _title_contains(current_title, STRONG_POSITIVE_TITLE_KEYWORDS) or
        _title_contains(current_title, MODERATE_POSITIVE_TITLE_KEYWORDS)
    )

    if core_skill_count >= 6 and not is_technical_title:
        # Many AI skills but non-tech title → suspicious
        if _title_contains(current_title, NEGATIVE_TITLE_KEYWORDS):
            keyword_stuffing_penalty = 0.60  # Heavy penalty
        else:
            keyword_stuffing_penalty = 0.25  # Moderate penalty
    else:
        keyword_stuffing_penalty = 0.0

    # --- Compute final score ---
    if category_scores:
        avg_quality = sum(category_scores.values()) / len(category_scores)
    else:
        avg_quality = 0.0

    skills_score = (
        0.35 * coverage_score +
        0.30 * avg_quality +
        0.20 * min(1.0, total_ai_skill_weight / 3.0) +
        0.15 * assessment_bonus / 0.15  # normalize
        - keyword_stuffing_penalty
    )

    return _normalize(skills_score)


# ─────────────────────────────────────────────────────────────────
# 3. CAREER QUALITY SCORE
# ─────────────────────────────────────────────────────────────────

def compute_career_quality(candidate):
    """
    Score 0-1 based on career depth, stability, and production experience.

    The JD values:
    - Candidates who've shipped real systems
    - Career stability (not title-chasing every 1.5 years)
    - Product company experience
    """
    career = candidate["career_history"]

    if not career:
        return 0.0

    # --- Production experience in descriptions ---
    all_descriptions = " ".join(
        job.get("description", "").lower() for job in career
    )

    production_hits = sum(
        1 for kw in PRODUCTION_ML_KEYWORDS
        if kw in all_descriptions
    )
    non_production_hits = sum(
        1 for kw in NON_PRODUCTION_KEYWORDS
        if kw in all_descriptions
    )

    # Normalize: production signal is strong if many hits
    production_score = min(1.0, production_hits / 12)
    # Penalty for non-production career descriptions
    non_prod_penalty = min(0.3, non_production_hits * 0.04)

    # --- Career stability ---
    # JD warns against title-chasers switching every 1.5 years
    durations = [job.get("duration_months", 0) for job in career]
    avg_tenure = sum(durations) / len(durations) if durations else 0

    if avg_tenure >= 30:
        stability_score = 1.0  # 2.5+ years average
    elif avg_tenure >= 24:
        stability_score = 0.8  # 2+ years
    elif avg_tenure >= 18:
        stability_score = 0.5  # 1.5 years — borderline
    elif avg_tenure >= 12:
        stability_score = 0.3  # Title chaser territory
    else:
        stability_score = 0.1  # Very short tenures

    # --- Career depth (number of roles, total career span) ---
    depth_score = min(1.0, len(career) / 4)  # 4+ roles = full credit

    # --- Company quality ---
    product_roles = sum(
        1 for job in career
        if _company_is_product(job.get("company", ""))
    )
    company_quality = min(1.0, product_roles / 2)

    # Composite
    quality = (
        0.40 * production_score +
        0.25 * stability_score +
        0.20 * company_quality +
        0.15 * depth_score
        - non_prod_penalty
    )

    return _normalize(quality)


# ─────────────────────────────────────────────────────────────────
# 4. BEHAVIORAL/ENGAGEMENT SCORE
# ─────────────────────────────────────────────────────────────────

def compute_behavioral(candidate):
    """
    Score 0-1 based on platform engagement and availability signals.

    The JD explicitly says: "A perfect-on-paper candidate who hasn't
    logged in for 6 months and has a 5% recruiter response rate is,
    for hiring purposes, not actually available."
    """
    signals = candidate.get("redrob_signals", {})

    if not signals:
        return 0.3  # No signals = unknown

    # --- Recency ---
    last_active = signals.get("last_active_date", "")
    try:
        last_date = datetime.strptime(last_active, "%Y-%m-%d").date()
        days_inactive = (REFERENCE_DATE - last_date).days
    except (ValueError, TypeError):
        days_inactive = 365  # Assume stale if can't parse

    if days_inactive <= RECENCY_EXCELLENT_DAYS:
        recency_score = 1.0
    elif days_inactive <= RECENCY_GOOD_DAYS:
        recency_score = 0.7
    elif days_inactive <= RECENCY_STALE_DAYS:
        recency_score = 0.35
    else:
        recency_score = 0.05  # Very stale — almost dead

    # --- Recruiter response rate ---
    response_rate = signals.get("recruiter_response_rate", 0)
    if response_rate >= RESPONSE_RATE_GOOD:
        response_score = 1.0
    elif response_rate >= RESPONSE_RATE_MINIMUM:
        response_score = 0.5 + 0.5 * (response_rate - RESPONSE_RATE_MINIMUM) / (RESPONSE_RATE_GOOD - RESPONSE_RATE_MINIMUM)
    elif response_rate >= 0.10:
        response_score = 0.2
    else:
        response_score = 0.05  # Almost never responds

    # --- Response time ---
    resp_time = signals.get("avg_response_time_hours", 200)
    if resp_time <= 24:
        time_score = 1.0
    elif resp_time <= 48:
        time_score = 0.8
    elif resp_time <= 96:
        time_score = 0.5
    elif resp_time <= 168:
        time_score = 0.3
    else:
        time_score = 0.1

    # --- Profile completeness ---
    completeness = signals.get("profile_completeness_score", 0) / 100.0

    # --- Open to work ---
    open_to_work = 1.0 if signals.get("open_to_work_flag", False) else 0.4

    # --- GitHub activity (strong signal for AI engineer) ---
    github = signals.get("github_activity_score", -1)
    if github < 0:
        github_score = 0.3  # No GitHub, small penalty
    elif github >= 60:
        github_score = 1.0
    elif github >= 30:
        github_score = 0.6
    else:
        github_score = 0.3

    # --- Interview completion rate ---
    interview_rate = signals.get("interview_completion_rate", 0)
    interview_score = interview_rate  # Direct mapping 0-1

    # --- Offer acceptance rate ---
    offer_rate = signals.get("offer_acceptance_rate", -1)
    if offer_rate < 0:
        offer_score = 0.5  # Unknown
    else:
        offer_score = offer_rate

    # --- Verification signals ---
    verified = (
        (1 if signals.get("verified_email", False) else 0) +
        (1 if signals.get("verified_phone", False) else 0) +
        (1 if signals.get("linkedin_connected", False) else 0)
    ) / 3.0

    # --- Saved by recruiters (social proof) ---
    saved = signals.get("saved_by_recruiters_30d", 0)
    saved_score = min(1.0, saved / 10)

    # Composite — recency and response rate are the heaviest
    behavioral = (
        0.25 * recency_score +
        0.20 * response_score +
        0.10 * time_score +
        0.10 * open_to_work +
        0.10 * github_score +
        0.08 * interview_score +
        0.05 * completeness +
        0.05 * offer_score +
        0.04 * verified +
        0.03 * saved_score
    )

    return _normalize(behavioral)


# ─────────────────────────────────────────────────────────────────
# 5. EDUCATION SCORE
# ─────────────────────────────────────────────────────────────────

def compute_education(candidate):
    """
    Score 0-1 based on education relevance. Deliberately low-weighted
    since the JD cares much more about experience than degrees.
    """
    education = candidate.get("education", [])

    if not education:
        return 0.3  # No education info = neutral

    best_field_score = 0.0
    best_tier_score = 0.0
    best_degree_level = 0.0

    degree_levels = {
        "ph.d": 1.0, "phd": 1.0,
        "m.tech": 0.85, "m.s": 0.85, "m.sc": 0.8,
        "m.e.": 0.85, "mba": 0.5,
        "b.tech": 0.6, "b.e.": 0.6, "b.sc": 0.5,
        "b.s": 0.5, "diploma": 0.3,
    }

    for edu in education:
        field = edu.get("field_of_study", "").lower()
        tier = edu.get("tier", "unknown")
        degree = edu.get("degree", "").lower()

        # Field relevance
        if any(f in field for f in STRONG_FIELDS):
            field_score = 1.0
        elif any(f in field for f in MODERATE_FIELDS):
            field_score = 0.5
        elif any(f in field for f in WEAK_FIELDS):
            field_score = 0.15
        else:
            field_score = 0.25

        # Tier
        tier_score = TIER_SCORES.get(tier, 0.3)

        # Degree level
        dl = 0.4  # default
        for deg_key, deg_val in degree_levels.items():
            if deg_key in degree:
                dl = deg_val
                break

        best_field_score = max(best_field_score, field_score)
        best_tier_score = max(best_tier_score, tier_score)
        best_degree_level = max(best_degree_level, dl)

    education_score = (
        0.50 * best_field_score +
        0.30 * best_tier_score +
        0.20 * best_degree_level
    )

    return _normalize(education_score)


# ─────────────────────────────────────────────────────────────────
# 6. LOGISTICS FIT SCORE
# ─────────────────────────────────────────────────────────────────

def compute_logistics(candidate):
    """
    Score 0-1 based on location, notice period, work mode, and
    salary alignment.
    """
    profile = candidate["profile"]
    signals = candidate.get("redrob_signals", {})

    # --- Location ---
    location = profile.get("location", "").lower()
    country = profile.get("country", "").lower()

    if any(city in location for city in PREFERRED_CITIES):
        location_score = 1.0
    elif any(city in location for city in GOOD_CITIES):
        location_score = 0.8
    elif "india" in country or any(kw in location for kw in INDIA_KEYWORDS):
        location_score = 0.6
    else:
        # Outside India
        willing = signals.get("willing_to_relocate", False)
        location_score = 0.3 if willing else 0.15

    # --- Notice period ---
    notice = signals.get("notice_period_days", 90)
    if notice <= NOTICE_IDEAL_DAYS:
        notice_score = 1.0
    elif notice <= NOTICE_ACCEPTABLE_DAYS:
        notice_score = 0.7
    elif notice <= NOTICE_PENALTY_DAYS:
        notice_score = 0.4
    else:
        notice_score = 0.15

    # --- Work mode ---
    pref_mode = signals.get("preferred_work_mode", "")
    # JD says hybrid with flexible cadence
    mode_scores = {"hybrid": 1.0, "flexible": 0.9, "onsite": 0.7, "remote": 0.5}
    mode_score = mode_scores.get(pref_mode, 0.5)

    # Composite
    logistics = (
        0.50 * location_score +
        0.30 * notice_score +
        0.20 * mode_score
    )

    return _normalize(logistics)


# ─────────────────────────────────────────────────────────────────
# COMBINED FEATURE EXTRACTION
# ─────────────────────────────────────────────────────────────────

def extract_all_features(candidate):
    """
    Extract all 6 dimension scores for a candidate.
    Returns a dict of dimension_name → score (0-1).
    """
    return {
        "role_fit": compute_role_fit(candidate),
        "skills_match": compute_skills_match(candidate),
        "career_quality": compute_career_quality(candidate),
        "behavioral": compute_behavioral(candidate),
        "education": compute_education(candidate),
        "logistics": compute_logistics(candidate),
    }


def extract_fast_features(candidate):
    """
    Extract cheap features for Stage 1 filtering.
    Only computes title score + basic skill count + experience band.
    Used to quickly eliminate candidates with zero relevance.
    """
    profile = candidate["profile"]
    current_title = profile.get("current_title", "").lower()
    yoe = profile.get("years_of_experience", 0)

    # Title relevance (cheap check)
    if _title_contains(current_title, STRONG_POSITIVE_TITLE_KEYWORDS):
        title_score = 1.0
    elif _title_contains(current_title, MODERATE_POSITIVE_TITLE_KEYWORDS):
        title_score = 0.4
    elif _title_contains(current_title, NEGATIVE_TITLE_KEYWORDS):
        title_score = 0.02
    else:
        title_score = 0.1

    # Core AI skills count (cheap check)
    skills = candidate.get("skills", [])
    tier1_skills = set()
    for skill in skills:
        sn = skill.get("name", "").lower().strip()
        for cat_name, cat_info in SKILL_CATEGORIES.items():
            if cat_info["weight"] >= 0.65:  # Tier 1+2
                if any(cs in sn or sn in cs for cs in cat_info["skills"]):
                    tier1_skills.add(cat_name)
                    break

    skill_coverage = min(1.0, len(tier1_skills) / 5)

    # Experience band
    if EXP_ACCEPTABLE_MIN <= yoe <= EXP_ACCEPTABLE_MAX:
        exp_ok = 0.5 if not (EXP_IDEAL_MIN <= yoe <= EXP_IDEAL_MAX) else 1.0
    else:
        exp_ok = 0.05

    # Career description has ML keywords?
    desc_text = " ".join(
        j.get("description", "").lower() for j in candidate.get("career_history", [])
    )
    ml_in_desc = any(kw in desc_text for kw in [
        "machine learning", "ml", "deep learning", "neural",
        "nlp", "embedding", "retrieval", "ranking", "recommendation",
        "model", "training", "inference", "transformer", "bert",
        "pytorch", "tensorflow", "data science", "feature",
        "pipeline", "vector", "search",
    ])
    desc_bonus = 0.3 if ml_in_desc else 0.0

    fast_score = (
        0.35 * title_score +
        0.30 * skill_coverage +
        0.15 * exp_ok +
        0.20 * desc_bonus
    )

    return fast_score
