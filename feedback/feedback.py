"""Feedback persistence (SQLite). No UI — use FastAPI ``POST /feedback``."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime

import pandas as pd

_DATA_DIR = os.environ.get(
    "DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
)
os.makedirs(_DATA_DIR, exist_ok=True)


class FeedbackManager:
    def __init__(self) -> None:
        self.db_path = os.path.join(_DATA_DIR, "feedback.db")
        self.setup_database()

    def setup_database(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rating INTEGER,
                    usability_score INTEGER,
                    feature_satisfaction INTEGER,
                    missing_features TEXT,
                    improvement_suggestions TEXT,
                    user_experience TEXT,
                    timestamp DATETIME
                )
            """
            )
            conn.commit()
        finally:
            conn.close()

    def save_feedback(self, feedback_data: dict) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO feedback (
                    rating, usability_score, feature_satisfaction,
                    missing_features, improvement_suggestions,
                    user_experience, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    feedback_data["rating"],
                    feedback_data["usability_score"],
                    feedback_data["feature_satisfaction"],
                    feedback_data["missing_features"],
                    feedback_data["improvement_suggestions"],
                    feedback_data["user_experience"],
                    datetime.now(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_feedback_stats(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query("SELECT * FROM feedback", conn)
        finally:
            conn.close()
        if df.empty:
            return {
                "avg_rating": 0,
                "avg_usability": 0,
                "avg_satisfaction": 0,
                "total_responses": 0,
            }
        return {
            "avg_rating": float(df["rating"].mean()),
            "avg_usability": float(df["usability_score"].mean()),
            "avg_satisfaction": float(df["feature_satisfaction"].mean()),
            "total_responses": int(len(df)),
        }
