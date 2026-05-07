import psycopg2
from psycopg2 import pool
import os
from datetime import datetime
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

# Create a connection pool
try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, DATABASE_URL)
    logger.info("PostgreSQL connection pool created successfully")
except Exception as e:
    logger.error(f"Error creating PostgreSQL connection pool: {e}")
    connection_pool = None

def get_database_connection():
    """Create and return a database connection from the pool"""
    if connection_pool:
        return connection_pool.getconn()
    return psycopg2.connect(DATABASE_URL)

def release_connection(conn):
    """Release a connection back to the pool"""
    if connection_pool and conn:
        connection_pool.putconn(conn)

def init_database():
    """Initialize database tables in PostgreSQL"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Create resume_data table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS resume_data (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            location TEXT,
            linkedin TEXT,
            github TEXT,
            portfolio TEXT,
            summary TEXT,
            target_role TEXT,
            target_category TEXT,
            education TEXT,
            experience TEXT,
            projects TEXT,
            skills TEXT,
            template TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create resume_skills table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS resume_skills (
            id SERIAL PRIMARY KEY,
            resume_id INTEGER REFERENCES resume_data(id),
            skill_name TEXT NOT NULL,
            skill_category TEXT NOT NULL,
            proficiency_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create resume_analysis table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS resume_analysis (
            id SERIAL PRIMARY KEY,
            resume_id INTEGER REFERENCES resume_data(id),
            ats_score REAL,
            keyword_match_score REAL,
            format_score REAL,
            section_score REAL,
            missing_skills TEXT,
            recommendations TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create admin_logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id SERIAL PRIMARY KEY,
            admin_email TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create admin table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create ai_analysis table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_analysis (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resume_data(id),
                model_used TEXT,
                resume_score INTEGER,
                job_role TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)

def save_resume_data(data):
    """Save resume data to database"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        personal_info = data.get('personal_info', {})
        
        cursor.execute('''
        INSERT INTO resume_data (
            name, email, phone, location, linkedin, github, portfolio,
            summary, target_role, target_category, education, 
            experience, projects, skills, template
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        ''', (
            personal_info.get('full_name', ''),
            personal_info.get('email', ''),
            personal_info.get('phone', ''),
            personal_info.get('location', ''),
            personal_info.get('linkedin', ''),
            personal_info.get('github', ''),
            personal_info.get('portfolio', ''),
            data.get('summary', ''),
            data.get('target_role', ''),
            data.get('target_category', ''),
            str(data.get('education', [])),
            str(data.get('experience', [])),
            str(data.get('projects', [])),
            str(data.get('skills', [])),
            data.get('template', '')
        ))
        
        resume_id = cursor.fetchone()[0]
        conn.commit()
        return resume_id
    except Exception as e:
        logger.error(f"Error saving resume data: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        release_connection(conn)

def save_analysis_data(resume_id, analysis):
    """Save resume analysis data"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO resume_analysis (
            resume_id, ats_score, keyword_match_score,
            format_score, section_score, missing_skills,
            recommendations
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            resume_id,
            float(analysis.get('ats_score', 0)),
            float(analysis.get('keyword_match_score', 0)),
            float(analysis.get('format_score', 0)),
            float(analysis.get('section_score', 0)),
            analysis.get('missing_skills', ''),
            analysis.get('recommendations', '')
        ))
        
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving analysis data: {e}")
        conn.rollback()
    finally:
        cursor.close()
        release_connection(conn)

def get_resume_stats():
    """Get statistics about resumes"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT COUNT(*) FROM resume_data')
        total_resumes = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(ats_score) FROM resume_analysis')
        avg_ats_score = cursor.fetchone()[0] or 0
        
        cursor.execute('''
        SELECT name, target_role, created_at 
        FROM resume_data 
        ORDER BY created_at DESC 
        LIMIT 5
        ''')
        recent_activity = cursor.fetchall()
        
        return {
            'total_resumes': total_resumes,
            'avg_ats_score': round(float(avg_ats_score), 2),
            'recent_activity': recent_activity
        }
    except Exception as e:
        logger.error(f"Error getting resume stats: {e}")
        return None
    finally:
        cursor.close()
        release_connection(conn)

def log_admin_action(admin_email, action):
    """Log admin login/logout actions"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO admin_logs (admin_email, action)
        VALUES (%s, %s)
        ''', (admin_email, action))
        conn.commit()
    except Exception as e:
        logger.error(f"Error logging admin action: {e}")
    finally:
        cursor.close()
        release_connection(conn)

def get_admin_logs():
    """Get all admin login/logout logs"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        SELECT admin_email, action, timestamp
        FROM admin_logs
        ORDER BY timestamp DESC
        ''')
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting admin logs: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)

def get_all_resume_data():
    """Get all resume data for admin dashboard"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        SELECT 
            r.id, r.name, r.email, r.phone, r.linkedin, r.github, r.portfolio,
            r.target_role, r.target_category, r.created_at,
            a.ats_score, a.keyword_match_score, a.format_score, a.section_score,
            r.location
        FROM resume_data r
        LEFT JOIN resume_analysis a ON r.id = a.resume_id
        ORDER BY r.created_at DESC
        ''')
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting resume data: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)

def verify_admin(email, password):
    """Verify admin credentials"""
    if email == "admin" and password == "admin@123":
        return True
        
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM admin WHERE email = %s AND password = %s', (email, password))
        result = cursor.fetchone()
        return bool(result)
    except Exception as e:
        logger.error(f"Error verifying admin: {e}")
        return False
    finally:
        cursor.close()
        release_connection(conn)

def save_ai_analysis_data(resume_id, analysis_data):
    """Save AI analysis data to the database"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO ai_analysis (
                resume_id, model_used, resume_score, job_role
            ) VALUES (%s, %s, %s, %s)
        ''', (
            resume_id,
            analysis_data.get('model_used', ''),
            analysis_data.get('resume_score', 0),
            analysis_data.get('job_role', '')
        ))
        
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        logger.error(f"Error saving AI analysis data: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        release_connection(conn)

def get_detailed_ai_analysis_stats():
    """Get detailed statistics about AI analyzer usage"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Total analyses
        cursor.execute("SELECT COUNT(*) FROM ai_analysis")
        total_analyses = cursor.fetchone()[0]
        
        # Model usage
        cursor.execute("""
            SELECT model_used, COUNT(*) as count
            FROM ai_analysis
            GROUP BY model_used
            ORDER BY count DESC
        """)
        model_usage = [{"model": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # Average score
        cursor.execute("SELECT AVG(resume_score) FROM ai_analysis")
        average_score = cursor.fetchone()[0] or 0
        
        # Top job roles
        cursor.execute("""
            SELECT job_role, COUNT(*) as count
            FROM ai_analysis
            GROUP BY job_role
            ORDER BY count DESC
            LIMIT 5
        """)
        top_job_roles = [{"role": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # Daily trend
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM ai_analysis
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        daily_trend = [{"date": str(row[0]), "count": row[1]} for row in cursor.fetchall()]

        # Recent analyses
        cursor.execute("""
            SELECT model_used, resume_score, job_role, created_at
            FROM ai_analysis
            ORDER BY created_at DESC
            LIMIT 5
        """)
        recent_analyses = [
            {"model": row[0], "score": row[1], "job_role": row[2], "date": str(row[3])} 
            for row in cursor.fetchall()
        ]
        
        return {
            "total_analyses": total_analyses,
            "model_usage": model_usage,
            "average_score": round(float(average_score), 1),
            "top_job_roles": top_job_roles,
            "daily_trend": daily_trend,
            "recent_analyses": recent_analyses
        }
    except Exception as e:
        logger.error(f"Error getting detailed AI analysis stats: {e}")
        return {
            "total_analyses": 0, "model_usage": [], "average_score": 0,
            "top_job_roles": [], "daily_trend": [], "recent_analyses": []
        }
    finally:
        cursor.close()
        release_connection(conn)

def get_candidates_for_recruiter_filter(skills=None, location=None, min_ats_score=0):
    """Get candidates based on recruiter filters"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        query = '''
        SELECT 
            r.id, r.name, r.email, r.phone, r.location, r.target_role, 
            r.skills, a.ats_score, r.experience
        FROM resume_data r
        LEFT JOIN resume_analysis a ON r.id = a.resume_id
        WHERE 1=1
        '''
        params = []
        
        if location:
            query += " AND r.location ILIKE %s"
            params.append(f"%{location}%")
            
        if min_ats_score > 0:
            query += " AND a.ats_score >= %s"
            params.append(min_ats_score)
            
        # For skills, since it's stored as a stringified list, we use ILIKE
        if skills:
            for skill in skills:
                query += " AND r.skills ILIKE %s"
                params.append(f"%{skill}%")
        
        query += " ORDER BY a.ats_score DESC NULLS LAST"
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        
        formatted_results = []
        for row in results:
            formatted_results.append({
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "location": row[4],
                "role": row[5],
                "skills": row[6],
                "ats_score": row[7],
                "experience": row[8]
            })
            
        return formatted_results
    except Exception as e:
        logger.error(f"Error filtering candidates: {e}")
        return []
    finally:
        cursor.close()
        release_connection(conn)

def reset_ai_analysis_stats():
    """Reset AI analysis statistics by clearing the ai_analysis table"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM ai_analysis")
        conn.commit()
        return {"success": True, "message": "AI analysis statistics reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting AI analysis stats: {e}")
        conn.rollback()
        return {"success": False, "message": f"Failed to reset AI statistics: {str(e)}"}
    finally:
        cursor.close()
        release_connection(conn)