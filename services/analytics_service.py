from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from models.candidate import Candidate
from collections import Counter
from datetime import datetime, timedelta

def get_dashboard_stats(db: Session):
    """
    Get top-level metrics for the Admin Dashboard.
    """
    total_candidates = db.query(Candidate).count()
    avg_ats = db.query(func.avg(Candidate.ats_score)).scalar() or 0
    
    # Today's submissions
    today = datetime.utcnow().date()
    today_count = db.query(Candidate).filter(func.date(Candidate.created_at) == today).count()
    
    # Percentile calculation for high scorers (>75)
    high_scorers = db.query(Candidate).filter(Candidate.ats_score >= 75).count()
    
    return {
        "total_candidates": total_candidates,
        "average_ats_score": round(avg_ats, 1),
        "today_submissions": today_count,
        "high_scorers": high_scorers,
        "success_rate": round((high_scorers / total_candidates * 100), 1) if total_candidates > 0 else 0
    }

def get_skill_distribution(db: Session, limit: int = 10):
    """
    Extract and count skill occurrences across all candidates.
    """
    # Fetch only the skills column
    all_skills_data = db.query(Candidate.skills).all()
    
    # Flatten the list of lists
    flat_skills = [skill for sublist in all_skills_data if sublist[0] for skill in sublist[0]]
    
    # Count frequencies
    counts = Counter(flat_skills)
    
    # Return top N
    return dict(counts.most_common(limit))

def get_job_role_distribution(db: Session, limit: int = 5):
    """
    Get distribution of job roles.
    """
    results = db.query(Candidate.job_role, func.count(Candidate.id)).\
        group_by(Candidate.job_role).\
        order_by(desc(func.count(Candidate.id))).\
        limit(limit).all()
        
    return {role: count for role, count in results}

def get_experience_distribution(db: Session):
    """
    Group candidates by experience buckets.
    """
    # Buckets: 0-1, 1-3, 3-5, 5-10, 10+
    exp_data = db.query(Candidate.total_experience).all()
    
    buckets = {
        "Entry (0-1)": 0,
        "Junior (1-3)": 0,
        "Mid (3-5)": 0,
        "Senior (5-10)": 0,
        "Expert (10+)": 0
    }
    
    for (exp,) in exp_data:
        if exp is None: continue
        if exp <= 1: buckets["Entry (0-1)"] += 1
        elif exp <= 3: buckets["Junior (1-3)"] += 1
        elif exp <= 5: buckets["Mid (3-5)"] += 1
        elif exp <= 10: buckets["Senior (5-10)"] += 1
        else: buckets["Expert (10+)"] += 1
        
    return buckets
