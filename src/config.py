"""
config.py — JD Requirements, Skill Taxonomy, Scoring Weights

Encodes the *real* requirements from the Senior AI Engineer JD at Redrob AI.
The JD explicitly warns: "The right answer is NOT find candidates whose skills
section contains the most AI keywords. That's a trap."

This config captures what the JD *means*, not just what it *says*.
"""

# ─────────────────────────────────────────────────────────────────
# SKILL TAXONOMY — Grouped by relevance to the role
# Each category: (importance_weight, [lowercased skill name variants])
# ─────────────────────────────────────────────────────────────────

SKILL_CATEGORIES = {
    # Tier 1: Absolute must-haves per the JD
    "embeddings_retrieval": {
        "weight": 1.0,
        "skills": [
            "embeddings", "sentence-transformers", "sentence transformers",
            "bge", "e5", "retrieval", "information retrieval",
            "dense retrieval", "semantic search", "vector search",
            "neural search", "rag", "retrieval augmented generation",
            "search ranking", "ranking systems", "re-ranking",
        ],
    },
    "vector_databases": {
        "weight": 0.95,
        "skills": [
            "pinecone", "weaviate", "qdrant", "milvus", "faiss",
            "elasticsearch", "opensearch", "vector database",
            "chromadb", "pgvector", "annoy", "hnswlib", "scann",
        ],
    },
    "nlp_ir": {
        "weight": 0.90,
        "skills": [
            "nlp", "natural language processing", "bert", "transformers",
            "huggingface", "hugging face", "spacy", "text classification",
            "named entity recognition", "ner", "text mining",
            "sentiment analysis", "language models", "tokenization",
            "word embeddings", "word2vec", "glove", "fasttext",
        ],
    },
    "ml_evaluation": {
        "weight": 0.85,
        "skills": [
            "ndcg", "mrr", "mean average precision", "evaluation",
            "a/b testing", "ab testing", "a/b test", "metrics",
            "precision recall", "f1 score", "roc", "auc",
            "offline evaluation", "online evaluation",
        ],
    },
    "python": {
        "weight": 0.80,
        "skills": ["python", "pyspark", "flask", "fastapi", "django"],
    },
    "deep_learning": {
        "weight": 0.80,
        "skills": [
            "deep learning", "neural networks", "pytorch", "tensorflow",
            "keras", "cnn", "rnn", "lstm", "attention mechanism",
            "transformer architecture", "neural network",
        ],
    },

    # Tier 2: Nice-to-have / adjacent
    "llm_finetuning": {
        "weight": 0.70,
        "skills": [
            "llm", "large language models", "fine-tuning", "fine tuning",
            "finetuning", "lora", "qlora", "peft", "instruction tuning",
            "rlhf", "prompt engineering", "gpt", "llama", "mistral",
            "fine-tuning llms",
        ],
    },
    "ml_algorithms": {
        "weight": 0.65,
        "skills": [
            "machine learning", "supervised learning", "unsupervised learning",
            "classification", "regression", "clustering", "random forest",
            "gradient boosting", "xgboost", "lightgbm", "catboost",
            "learning to rank", "recommendation system", "recommendation systems",
            "collaborative filtering", "content-based filtering",
            "statistical modeling", "bayesian", "ensemble methods",
        ],
    },
    "mlops_infra": {
        "weight": 0.55,
        "skills": [
            "mlops", "ml ops", "model deployment", "model serving",
            "mlflow", "kubeflow", "sagemaker", "vertex ai",
            "bentoml", "triton", "onnx", "tensorrt", "model monitoring",
            "feature store", "feature engineering", "weights & biases",
            "weights and biases", "wandb",
        ],
    },
    "data_engineering": {
        "weight": 0.45,
        "skills": [
            "data engineering", "spark", "apache spark", "airflow",
            "apache airflow", "kafka", "apache kafka", "data pipeline",
            "etl", "dbt", "snowflake", "bigquery", "databricks",
            "data warehouse", "hadoop", "data modeling",
            "apache beam", "apache flink",
        ],
    },
    "cloud_devops": {
        "weight": 0.35,
        "skills": [
            "aws", "gcp", "azure", "docker", "kubernetes", "k8s",
            "terraform", "ci/cd", "github actions", "jenkins",
        ],
    },
    "general_programming": {
        "weight": 0.20,
        "skills": [
            "java", "scala", "go", "golang", "c++", "rust",
            "sql", "nosql", "mongodb", "postgresql", "redis",
            "git", "linux", "bash",
        ],
    },
}

# Skills that are NEGATIVE signals (non-technical domain)
NEGATIVE_SKILL_NAMES = {
    "photoshop", "illustrator", "indesign", "powerpoint", "excel",
    "seo", "content writing", "marketing", "sales", "accounting",
    "six sigma", "sap", "tally", "hr", "recruitment", "canva",
    "autocad", "solidworks", "creo", "ansys", "catia",
    "content marketing", "social media", "brand management",
    "financial modeling", "bookkeeping", "supply chain",
}

# ─────────────────────────────────────────────────────────────────
# TITLE SCORING
# ─────────────────────────────────────────────────────────────────

# Title keywords that strongly indicate ML/AI role fit
# (lowercased, matched as substrings)
STRONG_POSITIVE_TITLE_KEYWORDS = [
    "ml engineer", "machine learning engineer", "ai engineer",
    "artificial intelligence", "data scientist", "nlp engineer",
    "deep learning", "research engineer", "research scientist",
    "applied scientist", "ml", "machine learning",
    "senior machine learning", "senior ai", "senior ml",
    "junior ml", "staff ml", "principal ml",
]

MODERATE_POSITIVE_TITLE_KEYWORDS = [
    "software engineer", "backend engineer", "data engineer",
    "full stack", "platform engineer", "infrastructure engineer",
    "site reliability", "devops",
]

# Titles that indicate NO fit for this ML role
NEGATIVE_TITLE_KEYWORDS = [
    "marketing manager", "hr manager", "human resources",
    "operations manager", "accountant", "sales executive",
    "customer support", "content writer", "graphic designer",
    "civil engineer", "mechanical engineer", "business analyst",
    "project manager", "product manager", "financial analyst",
    "teacher", "professor", "lecturer", "consultant",
    "recruiter", "brand manager", "ux designer", "ui designer",
]

# ─────────────────────────────────────────────────────────────────
# COMPANY TYPE
# ─────────────────────────────────────────────────────────────────

# Consulting/services firms — JD explicitly penalizes consulting-only careers
CONSULTING_SERVICES_FIRMS = {
    "tcs", "tata consultancy", "tata consultancy services",
    "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "hcl", "hcl technologies",
    "tech mahindra", "mindtree", "mphasis",
    "l&t infotech", "lt infotech", "lti", "ltimindtree",
    "persistent", "persistent systems", "zensar",
    "hexaware", "cyient", "niit", "birlasoft",
    "sonata software", "coforge",
}

# Known product/tech companies (bonus)
PRODUCT_COMPANIES = {
    "google", "microsoft", "amazon", "meta", "facebook", "apple",
    "netflix", "uber", "airbnb", "stripe", "spotify", "twitter",
    "linkedin", "salesforce", "adobe", "oracle", "ibm",
    "flipkart", "swiggy", "zomato", "razorpay", "cred",
    "phonepe", "paytm", "meesho", "zerodha", "dream11",
    "freshworks", "zoho", "postman", "browserstack", "hasura",
    "ola", "myntra", "nykaa", "dunzo", "groww", "upstox",
    "sharechat", "dailyhunt", "inmobi", "cleartax",
    "atlassian", "datadog", "snowflake", "databricks",
    "openai", "anthropic", "cohere", "hugging face",
    "redrob",
}

# Fictional/synthetic company names in the dataset
FICTIONAL_COMPANIES = {
    "dunder mifflin", "acme corp", "globex inc", "initech",
    "stark industries", "wayne enterprises", "umbrella corp",
    "oscorp", "cyberdyne", "soylent corp",
}

# ─────────────────────────────────────────────────────────────────
# EXPERIENCE BANDS
# ─────────────────────────────────────────────────────────────────

EXP_IDEAL_MIN = 5.0
EXP_IDEAL_MAX = 9.0
EXP_ACCEPTABLE_MIN = 3.5
EXP_ACCEPTABLE_MAX = 13.0

# ─────────────────────────────────────────────────────────────────
# LOCATION
# ─────────────────────────────────────────────────────────────────

# India preferred, with some cities getting a bonus
PREFERRED_CITIES = {"pune", "noida"}
GOOD_CITIES = {
    "hyderabad", "mumbai", "delhi", "ncr", "gurgaon", "gurugram",
    "bangalore", "bengaluru", "chennai",
}
INDIA_KEYWORDS = {
    "india", "pune", "noida", "hyderabad", "mumbai", "delhi",
    "ncr", "gurgaon", "gurugram", "bangalore", "bengaluru",
    "chennai", "kolkata", "ahmedabad", "jaipur", "lucknow",
    "chandigarh", "indore", "bhopal", "nagpur", "coimbatore",
    "kochi", "trivandrum", "visakhapatnam", "vizag",
    "tamil nadu", "karnataka", "telangana", "maharashtra",
    "uttar pradesh", "haryana", "rajasthan", "gujarat",
    "madhya pradesh", "west bengal", "kerala",
}

# ─────────────────────────────────────────────────────────────────
# BEHAVIORAL THRESHOLDS
# ─────────────────────────────────────────────────────────────────

# Days since last active — beyond this the candidate is "stale"
RECENCY_EXCELLENT_DAYS = 30
RECENCY_GOOD_DAYS = 90
RECENCY_STALE_DAYS = 180

# Notice period thresholds
NOTICE_IDEAL_DAYS = 30
NOTICE_ACCEPTABLE_DAYS = 60
NOTICE_PENALTY_DAYS = 90

# Response rate thresholds
RESPONSE_RATE_GOOD = 0.50
RESPONSE_RATE_MINIMUM = 0.20

# ─────────────────────────────────────────────────────────────────
# SCORING WEIGHTS (Final composite)
# ─────────────────────────────────────────────────────────────────

DIMENSION_WEIGHTS = {
    "role_fit": 0.28,
    "skills_match": 0.22,
    "text_similarity": 0.18,
    "career_quality": 0.15,
    "behavioral": 0.12,
    "education": 0.03,
    "logistics": 0.02,
}

# ─────────────────────────────────────────────────────────────────
# PRODUCTION EXPERIENCE KEYWORDS
# Used to detect real production ML work in career descriptions
# ─────────────────────────────────────────────────────────────────

PRODUCTION_ML_KEYWORDS = [
    # Deployment & production
    "production", "deployed", "shipped", "launched", "live",
    "real users", "real-world", "end-to-end", "e2e",
    "serving", "inference", "latency", "throughput",
    "scale", "scalable", "millions", "thousands",

    # Ranking, search, retrieval
    "ranking", "search", "retrieval", "recommendation",
    "candidate ranking", "matching", "scoring", "re-ranking",
    "search engine", "search infrastructure", "query",

    # Embeddings & vectors
    "embedding", "vector", "similarity", "cosine",
    "nearest neighbor", "approximate nearest",
    "semantic", "dense retrieval",

    # ML systems
    "model training", "model serving", "feature store",
    "training pipeline", "inference pipeline",
    "a/b test", "experiment", "evaluation",
    "metrics", "ndcg", "mrr", "precision",
    "offline evaluation", "online evaluation",

    # NLP specific
    "nlp", "natural language", "text",
    "transformer", "bert", "language model",
    "tokeniz", "fine-tun",

    # Data/ML infrastructure
    "data pipeline", "ml pipeline", "mlops",
    "feature engineering", "model monitoring",
    "data quality", "model drift",
]

# Anti-production keywords (consulting/non-technical)
NON_PRODUCTION_KEYWORDS = [
    "advisory", "consulting", "strategy",
    "stakeholder management", "slide-craft",
    "executive communication", "process re-engineering",
    "brand identity", "packaging design",
    "marketing", "seo", "content",
    "bookkeeping", "compliance", "audit",
    "supply chain", "logistics", "warehouse",
    "customer support", "ticket", "escalation",
]

# ─────────────────────────────────────────────────────────────────
# EDUCATION FIELD RELEVANCE
# ─────────────────────────────────────────────────────────────────

STRONG_FIELDS = {
    "computer science", "machine learning", "artificial intelligence",
    "data science", "computational linguistics", "statistics",
    "applied mathematics", "information technology",
    "natural language processing",
}

MODERATE_FIELDS = {
    "electrical engineering", "electronics",
    "mathematics", "physics", "operations research",
    "information systems", "software engineering",
}

WEAK_FIELDS = {
    "mechanical engineering", "civil engineering",
    "chemical engineering", "biotechnology",
    "commerce", "business administration",
}

# Education institution tiers
TIER_SCORES = {
    "tier_1": 1.0,
    "tier_2": 0.75,
    "tier_3": 0.45,
    "tier_4": 0.20,
    "unknown": 0.30,
}

# ─────────────────────────────────────────────────────────────────
# JD TEXT (for TF-IDF similarity computation)
# ─────────────────────────────────────────────────────────────────

JD_TEXT = """
Senior AI Engineer founding team at AI-native talent intelligence platform.
5-9 years experience in applied ML AI at product companies.
Own the intelligence layer: ranking, retrieval, and matching systems.
Ship v2 ranking system with embeddings, hybrid retrieval, LLM-based re-ranking.
Set up evaluation infrastructure: offline benchmarks, online A/B testing, recruiter feedback loops.

Must have production experience with embeddings-based retrieval systems.
Sentence-transformers, OpenAI embeddings, BGE, E5 deployed to real users.
Handled embedding drift, index refresh, retrieval-quality regression in production.
Production experience with vector databases or hybrid search infrastructure.
Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS.
Strong Python code quality.
Hands-on experience designing evaluation frameworks for ranking systems.
NDCG, MRR, MAP, offline-to-online correlation, A/B test interpretation.

Nice to have: LLM fine-tuning experience LoRA QLoRA PEFT.
Learning-to-rank models XGBoost neural.
HR-tech recruiting tech marketplace products.
Distributed systems large-scale inference optimization.
Open-source contributions in AI ML space.

Looking for product engineers who ship, not pure researchers.
Need someone who built recommendation search ranking system at scale.
Career in applied ML at product companies, not consulting services firms.
Strong NLP information retrieval background.
Hybrid remote location Pune Noida India.
"""
