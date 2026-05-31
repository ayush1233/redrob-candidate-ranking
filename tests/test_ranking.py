import unittest
import sys
import os

# Add parent dir to path so we can import src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.honeypot_detector import detect_honeypot, is_honeypot
from src.feature_engine import extract_all_features, extract_fast_features
from src.text_analyzer import compute_production_experience_score

class TestHoneypotDetector(unittest.TestCase):
    
    def test_genuine_candidate(self):
        """A normal candidate should not trigger any honeypot flags."""
        cand = {
            "profile": {"current_title": "Machine Learning Engineer", "years_of_experience": 5.0},
            "career_history": [
                {"title": "Machine Learning Engineer", "duration_months": 36, "description": "Built models."},
                {"title": "Data Analyst", "duration_months": 24, "description": "SQL and dashboards."}
            ],
            "skills": [
                {"name": "Python", "proficiency": "advanced", "duration_months": 48, "endorsements": 10},
                {"name": "PyTorch", "proficiency": "intermediate", "duration_months": 24, "endorsements": 5}
            ],
            "redrob_signals": {"profile_completeness_score": 85}
        }
        prob = detect_honeypot(cand)
        self.assertEqual(prob, 0.0)
        self.assertFalse(is_honeypot(cand))

    def test_experience_duration_mismatch(self):
        """Claims 15 years experience, but career history only shows 2 years."""
        cand = {
            "profile": {"current_title": "AI Expert", "years_of_experience": 15.0},
            "career_history": [
                {"title": "AI Expert", "duration_months": 24, "description": "Worked on AI."}
            ],
            "skills": []
        }
        prob = detect_honeypot(cand)
        self.assertGreater(prob, 0)
        
    def test_expert_zero_duration(self):
        """Claims to be an expert in many skills but used them for 0 months."""
        skills = []
        for i in range(6):
            skills.append({"name": f"Skill {i}", "proficiency": "expert", "duration_months": 0, "endorsements": 0})
            
        cand = {
            "profile": {"current_title": "ML Engineer", "years_of_experience": 5.0},
            "career_history": [],
            "skills": skills
        }
        prob = detect_honeypot(cand)
        self.assertGreaterEqual(prob, 0.5) # Should trigger multiple flags (Zero duration + too many experts + zero endorsements)
        self.assertTrue(is_honeypot(cand))

    def test_non_tech_title_with_all_ai_skills(self):
        """Marketing Manager claiming expertise in deep learning, embeddings, etc."""
        cand = {
            "profile": {"current_title": "Marketing Manager", "years_of_experience": 10.0},
            "career_history": [{"title": "Marketing Manager", "description": "Ran SEO campaigns.", "duration_months": 120}],
            "skills": [
                {"name": "Deep Learning", "proficiency": "advanced"},
                {"name": "PyTorch", "proficiency": "advanced"},
                {"name": "Embeddings", "proficiency": "expert"},
                {"name": "NLP", "proficiency": "expert"},
                {"name": "RAG", "proficiency": "expert"},
                {"name": "Transformers", "proficiency": "expert"},
            ]
        }
        prob = detect_honeypot(cand)
        self.assertGreater(prob, 0)
        
    def test_title_description_mismatch(self):
        """Accountant who claims they built neural networks."""
        cand = {
            "profile": {"current_title": "Accountant", "years_of_experience": 5.0},
            "career_history": [
                {
                    "title": "Senior Accountant", 
                    "description": "I built machine learning pipelines and deep learning neural networks for vector embeddings.", 
                    "duration_months": 60
                }
            ],
            "skills": []
        }
        prob = detect_honeypot(cand)
        self.assertGreater(prob, 0)


class TestAntiKeywordStuffing(unittest.TestCase):
    
    def test_keyword_stuffer_penalty(self):
        """A non-technical person with many AI skills should score lower on skills than a technical person."""
        ai_skills = [
            {"name": "Python", "proficiency": "expert", "duration_months": 48},
            {"name": "PyTorch", "proficiency": "expert", "duration_months": 48},
            {"name": "Deep Learning", "proficiency": "expert", "duration_months": 48},
            {"name": "Embeddings", "proficiency": "expert", "duration_months": 48},
            {"name": "NLP", "proficiency": "expert", "duration_months": 48},
            {"name": "Machine Learning", "proficiency": "expert", "duration_months": 48},
            {"name": "Vector Search", "proficiency": "expert", "duration_months": 48},
        ]
        
        # Candidate 1: Real ML Engineer
        real_cand = {
            "profile": {"current_title": "Senior Machine Learning Engineer", "years_of_experience": 5.0},
            "skills": ai_skills,
            "redrob_signals": {},
            "career_history": []
        }
        
        # Candidate 2: Marketing Manager (Keyword Stuffer)
        fake_cand = {
            "profile": {"current_title": "Marketing Manager", "years_of_experience": 5.0},
            "skills": ai_skills,
            "redrob_signals": {},
            "career_history": []
        }
        
        real_features = extract_all_features(real_cand)
        fake_features = extract_all_features(fake_cand)
        
        # The fake candidate should suffer a heavy keyword stuffing penalty
        self.assertGreater(real_features["skills_match"], fake_features["skills_match"] + 0.2)


class TestBehavioralSignals(unittest.TestCase):

    def test_recency_and_response(self):
        """A candidate who hasn't logged in for 8 months and never responds should score very low."""
        base_cand = {
            "profile": {"current_title": "ML Engineer", "years_of_experience": 5.0, "location": "Pune", "country": "India"},
            "career_history": [],
            "skills": [],
            "education": []
        }
        
        # Candidate 1: Highly active
        active_cand = dict(base_cand)
        active_cand["redrob_signals"] = {
            "last_active_date": "2026-05-30", # Very recent relative to our 2026-06-01 reference
            "recruiter_response_rate": 0.85,
            "avg_response_time_hours": 12,
            "github_activity_score": 80
        }
        
        # Candidate 2: Completely stale
        stale_cand = dict(base_cand)
        stale_cand["redrob_signals"] = {
            "last_active_date": "2024-01-01", # Over 2 years ago
            "recruiter_response_rate": 0.05,
            "avg_response_time_hours": 300,
            "github_activity_score": 10
        }
        
        active_f = extract_all_features(active_cand)
        stale_f = extract_all_features(stale_cand)
        
        # The active candidate should have a massively higher behavioral score
        self.assertGreater(active_f["behavioral"], 0.7)
        self.assertLess(stale_f["behavioral"], 0.3)


class TestProductionExperience(unittest.TestCase):
    
    def test_production_detection(self):
        """Text analyzer should distinguish between building models and deploying to production."""
        
        # Candidate 1: Played with models in Jupyter
        research_cand = {
            "career_history": [
                {
                    "description": "Researched various neural networks. Trained a PyTorch model on a dataset. Presented slides on deep learning strategy and advisory."
                }
            ]
        }
        
        # Candidate 2: Shipped real systems
        prod_cand = {
            "career_history": [
                {
                    "description": "Deployed a vector search retrieval system to production serving real users at scale. Built end-to-end ML training pipelines."
                }
            ]
        }
        
        r_score = compute_production_experience_score(research_cand)
        p_score = compute_production_experience_score(prod_cand)
        
        self.assertGreater(p_score, r_score + 0.3)


class TestRoleFit(unittest.TestCase):
    
    def test_consulting_vs_product(self):
        """Product company experience should score higher than consulting-only."""
        base_cand = {
            "profile": {"current_title": "ML Engineer", "years_of_experience": 6.0},
            "skills": [],
            "redrob_signals": {},
        }
        
        # Consulting only
        consulting_cand = dict(base_cand)
        consulting_cand["career_history"] = [
            {"title": "ML Engineer", "company": "Tata Consultancy Services (TCS)", "duration_months": 36},
            {"title": "ML Engineer", "company": "Infosys", "duration_months": 36}
        ]
        
        # Product company
        product_cand = dict(base_cand)
        product_cand["career_history"] = [
            {"title": "ML Engineer", "company": "Flipkart", "duration_months": 36},
            {"title": "ML Engineer", "company": "Zomato", "duration_months": 36}
        ]
        
        c_feat = extract_all_features(consulting_cand)
        p_feat = extract_all_features(product_cand)
        
        self.assertGreater(p_feat["role_fit"], c_feat["role_fit"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
