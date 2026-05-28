"""
honeypot_detector.py — Detect Impossible/Trap Candidate Profiles

The dataset contains ~80 honeypot candidates with subtly impossible profiles.
Examples from the spec:
- 8 years of experience at a company founded 3 years ago
- "Expert" proficiency in 10 skills with 0 years used
- Skill/career mismatches that are statistically impossible

Submissions with honeypot rate > 10% in top 100 are disqualified.
"""


def detect_honeypot(candidate):
    """
    Returns a honeypot probability score (0.0 = definitely real, 1.0 = definitely honeypot).
    A candidate is flagged as honeypot if multiple impossible signals are detected.
    """
    red_flags = 0
    total_checks = 0

    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})

    # ─── Check 1: Experience vs career duration mismatch ───
    total_checks += 1
    claimed_yoe = profile.get("years_of_experience", 0)
    total_career_months = sum(j.get("duration_months", 0) for j in career)
    total_career_years = total_career_months / 12.0

    # If claimed experience is WAY more than sum of all jobs
    if claimed_yoe > 0 and total_career_years > 0:
        ratio = claimed_yoe / total_career_years
        if ratio > 2.0:  # Claims 2x more experience than career shows
            red_flags += 1

    # ─── Check 2: Expert in many skills with 0 duration ───
    total_checks += 1
    expert_zero_duration = 0
    expert_count = 0
    for skill in skills:
        if skill.get("proficiency") == "expert":
            expert_count += 1
            if skill.get("duration_months", 0) == 0:
                expert_zero_duration += 1

    if expert_count >= 5 and expert_zero_duration >= 3:
        red_flags += 1

    # ─── Check 3: Too many expert skills overall ───
    total_checks += 1
    if expert_count >= 10:
        red_flags += 1  # Nobody is "expert" in 10+ things

    # ─── Check 4: High skill count with 0 endorsements ───
    total_checks += 1
    skills_with_zero_endorsements = sum(
        1 for s in skills
        if s.get("endorsements", 0) == 0 and s.get("proficiency") in ("expert", "advanced")
    )
    if skills_with_zero_endorsements >= 5:
        red_flags += 1

    # ─── Check 5: Career description doesn't match title ───
    total_checks += 1
    title_desc_mismatches = 0
    for job in career:
        title = job.get("title", "").lower()
        desc = job.get("description", "").lower()

        # Check for obvious mismatches
        if "engineer" in title and any(kw in desc for kw in [
            "marketing", "brand", "seo", "content writing",
            "customer support", "accounting", "bookkeeping"
        ]):
            title_desc_mismatches += 1
        elif "marketing" in title and any(kw in desc for kw in [
            "neural network", "model training", "machine learning",
            "deep learning", "embedding"
        ]):
            title_desc_mismatches += 1
        elif "accountant" in title and any(kw in desc for kw in [
            "machine learning", "deep learning", "neural", "ml pipeline"
        ]):
            title_desc_mismatches += 1
        elif "hr" in title and any(kw in desc for kw in [
            "machine learning", "deep learning", "neural network",
            "data pipeline", "model training"
        ]):
            title_desc_mismatches += 1

    if title_desc_mismatches >= 1:
        red_flags += 1

    # ─── Check 6: Title says non-tech but has ALL AI skills ───
    total_checks += 1
    current_title = profile.get("current_title", "").lower()
    non_tech_titles = [
        "marketing", "hr", "accountant", "sales", "customer support",
        "content writer", "graphic designer", "operations",
        "civil engineer", "mechanical engineer",
    ]
    is_non_tech = any(nt in current_title for nt in non_tech_titles)

    ai_skill_names = {
        "nlp", "deep learning", "machine learning", "pytorch", "tensorflow",
        "bert", "transformers", "neural networks", "rag",
        "embeddings", "fine-tuning llms", "gans", "computer vision",
        "image classification", "speech recognition", "tts",
        "object detection", "statistical modeling", "feature engineering",
    }
    ai_skills_count = sum(
        1 for s in skills
        if s.get("name", "").lower() in ai_skill_names
    )

    if is_non_tech and ai_skills_count >= 6:
        red_flags += 1  # Non-tech title but loaded with AI skills

    # ─── Check 7: Impossible tenure ───
    total_checks += 1
    for job in career:
        duration = job.get("duration_months", 0)
        if duration > 240:  # > 20 years at one company
            red_flags += 1
            break

    # ─── Check 8: Inconsistent profile completeness vs content ───
    total_checks += 1
    completeness = signals.get("profile_completeness_score", 0)
    if completeness > 90 and len(skills) <= 2 and len(career) <= 1:
        red_flags += 1  # Claims high completeness but almost no content

    # ─── Check 9: All career descriptions identical or very similar ───
    total_checks += 1
    if len(career) >= 3:
        descriptions = [j.get("description", "") for j in career]
        unique_descs = set(descriptions)
        if len(unique_descs) == 1 and len(descriptions) >= 3:
            red_flags += 1  # All descriptions identical

    # ─── Check 10: Headline contradicts current title ───
    total_checks += 1
    headline = profile.get("headline", "").lower()
    if current_title and headline:
        # Major contradiction between headline and title
        headline_is_tech = any(kw in headline for kw in [
            "ml", "ai", "machine learning", "data scien", "engineer"
        ])
        title_is_non_tech = any(nt in current_title for nt in non_tech_titles)
        if headline_is_tech and title_is_non_tech:
            pass  # Could be transitioning, mild flag only
        elif not headline_is_tech and not title_is_non_tech:
            pass  # Consistent

    # ─── Compute honeypot probability ───
    if total_checks > 0:
        honeypot_prob = red_flags / total_checks
    else:
        honeypot_prob = 0.0

    # Strong honeypot if 3+ red flags
    if red_flags >= 3:
        honeypot_prob = max(honeypot_prob, 0.8)
    elif red_flags >= 2:
        honeypot_prob = max(honeypot_prob, 0.5)

    return honeypot_prob


def is_honeypot(candidate, threshold=0.35):
    """
    Returns True if candidate is likely a honeypot.
    Uses a conservative threshold to avoid false positives.
    """
    return detect_honeypot(candidate) >= threshold
