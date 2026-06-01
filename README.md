# Intelligent Candidate Discovery & Ranking System

## Redrob Hackathon — AI-Powered Candidate Ranking

An AI system that ranks candidates the way a great recruiter would — not by matching keywords, but by actually understanding who fits the role.

### Architecture

```
100K Candidates → [Stage 1: Fast Filter] → 3K Shortlist
                                               ↓
                  [Stage 2: TF-IDF Text Model] → Semantic Similarity
                                               ↓
                  [Stage 3: Deep 6-Dimension Scoring] → Composite Score
                                               ↓
                  [Stage 4: Honeypot Detection] → Filter Impossible Profiles
                                               ↓
                  [Stage 5: Reasoning Generation] → Top 100 CSV
```

### The 6 Scoring Dimensions

| Dimension | Weight | What it captures |
|-----------|--------|------------------|
| **Role Fit** | 28% | Title relevance, career trajectory toward ML, company type (product vs consulting) |
| **Skills Match** | 22% | Semantic skill categories, proficiency depth, anti-keyword-stuffing |
| **Text Similarity** | 18% | TF-IDF cosine similarity + production experience keyword detection |
| **Career Quality** | 15% | Production deployment signals, career stability, company quality |
| **Behavioral** | 12% | Platform engagement, recruiter response rate, GitHub activity |
| **Education** | 3% | Field relevance, institution tier |
| **Logistics** | 2% | Location, notice period, work mode |

### Key Design Decisions

1. **Anti-Keyword-Stuffing**: The JD explicitly warns that "candidates with all AI keywords but Marketing Manager title" are traps. Our system detects skill-career mismatches and penalizes keyword stuffers.

2. **Two-Stage Pipeline**: Fast filtering on 100K (cheap features) → Deep analysis on top 3K (TF-IDF + full features). Ensures runtime stays under 5 minutes.

3. **TF-IDF Text Understanding**: Goes beyond structured fields to analyze career descriptions for production ML experience indicators. Catches candidates who describe building "recommendation systems" without listing "embeddings" as a skill.

4. **Behavioral Signal Integration**: A "perfect-on-paper" candidate with 5% recruiter response rate and 6-month inactivity gets down-weighted. Recency and responsiveness are 45% of the behavioral score.

5. **Honeypot Detection**: 10 cross-validation checks catch impossible profiles (expert in 10+ skills with 0 duration, career description mismatches, experience/tenure impossibilities).

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the ranking system
python rank.py --candidates ./India_runs_data_and_ai_challenge/candidates.jsonl --out ./submission.csv

# With custom settings
python rank.py --candidates ./candidates.jsonl --out ./submission.csv --top-n 5000
```

### Reproduce the Submission

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

This single command produces the submission CSV from the candidates file. Runtime: ~2-3 minutes on a 16GB CPU machine.

### Project Structure

```
├── rank.py                        # Main entry point
├── src/
│   ├── config.py                  # JD requirements, skill taxonomy, weights
│   ├── feature_engine.py          # 6-dimension feature extraction
│   ├── text_analyzer.py           # TF-IDF similarity + production keyword detection
│   ├── honeypot_detector.py       # Impossible profile detection (10 checks)
│   ├── scorer.py                  # Two-stage ranking engine
│   └── reasoning_generator.py     # Fact-based reasoning generation
├── requirements.txt               # Dependencies (numpy, scikit-learn, pandas)
├── submission.csv                 # Generated output
└── India_runs_data_and_ai_challenge/
    ├── candidates.jsonl           # 100K candidate profiles
    ├── job_description.docx       # Target JD
    ├── candidate_schema.json      # Data schema
    └── ...
```

### Compute Requirements

- **Runtime**: ~2-3 minutes (well under 5-minute limit)
- **Memory**: ~2-3 GB RAM (well under 16 GB limit)
- **CPU only**: No GPU required
- **No network**: Zero external API calls

### Tech Stack

- Python 3.10+
- scikit-learn (TF-IDF vectorization)
- NumPy (numerical operations)
- No LLM APIs, no GPU, no external services

### How It Works (Detailed)

**Stage 1 — Fast Filter**: Streams all 100K candidates and computes cheap features (title keyword match, skill category count, experience band check, career description ML keyword scan). Keeps the top 3,000 candidates.

**Stage 2 — TF-IDF Model**: Fits a TF-IDF vectorizer on the shortlisted candidates' text (headline + summary + career descriptions + skills). Computes cosine similarity between each candidate's text vector and the JD vector.

**Stage 3 — Deep Scoring**: For each shortlisted candidate, extracts 50+ features across 6 dimensions. Computes a weighted composite score. The weights reflect the JD's priorities: role fit and skills matter most, but behavioral signals ensure we surface only *hirable* candidates.

**Stage 4 — Honeypot Filtering**: Runs 10 cross-validation checks per candidate to detect impossible profiles. Candidates flagged as honeypots receive a score multiplier of 0.0 (hard elimination).

**Stage 5 — Reasoning**: Generates specific, fact-based, varied reasoning for each ranked candidate. References actual skills, years of experience, company names, and behavioral metrics from the profile. Acknowledges gaps honestly.

### Author

Built for the Redrob Intelligent Candidate Discovery & Ranking Challenge.
