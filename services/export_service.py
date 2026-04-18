import pandas as pd
from sqlalchemy.orm import Session
from models.candidate import Candidate
import io

def export_candidates_to_csv(db: Session):
    """
    Export all candidates to a CSV file.
    """
    # Fetch all candidates
    candidates = db.query(Candidate).all()
    
    # Convert to list of dicts
    data = []
    for c in candidates:
        data.append({
            "Full Name": c.full_name,
            "Email": c.email,
            "Phone": c.phone,
            "Location": c.location,
            "Job Role": c.job_role,
            "Total Experience": c.total_experience,
            "Skills": ", ".join(c.skills) if c.skills else "",
            "ATS Score": c.ats_score,
            "Applied On": c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else ""
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to buffer
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    
    buffer.seek(0)
    return buffer

def export_candidates_to_excel(db: Session):
    """
    Export all candidates to an Excel file.
    """
    # Fetch all candidates
    candidates = db.query(Candidate).all()
    
    # Convert to list of dicts
    data = []
    for c in candidates:
        data.append({
            "Full Name": c.full_name,
            "Email": c.email,
            "Phone": c.phone,
            "Location": c.location,
            "Job Role": c.job_role,
            "Total Experience": c.total_experience,
            "Skills": ", ".join(c.skills) if c.skills else "",
            "ATS Score": c.ats_score,
            "Applied On": c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else ""
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to buffer
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Candidates')
    
    buffer.seek(0)
    return buffer
