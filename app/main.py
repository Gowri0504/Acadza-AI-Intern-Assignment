from fastapi import FastAPI, HTTPException
import json
import os
import re

from app.analyze import analyze_student
from app.recommend import recommend_plan
from app.utils import load_json, get_qid

app = FastAPI()

# Load data once at startup
DATA_DIR = "data"
students = load_json(os.path.join(DATA_DIR, "student_performance.json"))
raw_questions = load_json(os.path.join(DATA_DIR, "question_bank.json"))

# Clean and index questions
questions_by_id = {}
invalid_questions_count = 0
for q in raw_questions:
    qid = get_qid(q)
    # Basic validation: must have qid, difficulty, and at least one type of content with answer
    has_content = any(q.get(t, {}).get("answer") for t in ["scq", "mcq", "integer"])
    if qid and q.get("difficulty") is not None and has_content:
        # Check for duplicates
        if qid not in questions_by_id:
            questions_by_id[qid] = q
        else:
            invalid_questions_count += 1 # duplicate
    else:
        invalid_questions_count += 1

questions = list(questions_by_id.values())

@app.get("/")
def home():
    return {
        "project": "JEE/NEET Recommender System",
        "status": "online",
        "stats": {
            "total_students": len(students),
            "total_questions_in_bank": len(questions),
            "invalid_questions_filtered": invalid_questions_count
        }
    }

@app.post("/analyze/{student_id}")
def analyze(student_id: str):
    student = next((s for s in students if s["student_id"] == student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return analyze_student(student)

@app.post("/recommend/{student_id}")
def recommend(student_id: str):
    student = next((s for s in students if s["student_id"] == student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    analysis = analyze_student(student)
    return recommend_plan(analysis, questions)

@app.get("/question/{question_id}")
def get_question(question_id: str):
    q = questions_by_id.get(question_id)
    if not q:
        # Check by internal 'qid' if it's different
        q = next((qu for qu in questions if qu.get("qid") == question_id), None)
    
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Extract plaintext preview
    q_type = q.get("questionType", "scq").lower()
    if q_type == "integerquestion": q_type = "integer"
    content = q.get(q_type, {})
    html_text = content.get("question", "")
    # Simple regex to remove HTML tags
    clean_text = re.sub('<[^<]+?>', '', html_text)
    # Limit to first 100 chars
    preview = clean_text[:100] + "..." if len(clean_text) > 100 else clean_text

    return {
        "question_id": question_id,
        "type": q_type,
        "subject": q.get("subject"),
        "topic": q.get("topic"),
        "difficulty": q.get("difficulty"),
        "preview": preview.strip(),
        "full_data": q
    }

@app.get("/leaderboard")
def get_leaderboard():
    leaderboard = []
    for student in students:
        analysis = analyze_student(student)
        metrics = analysis["metrics"]
        
        # Scoring Formula:
        # Score = (Avg Score * 0.6) + (Accuracy * 0.2) + (Consistency * 0.2)
        score = (metrics["avg_score"] * 0.6) + (metrics["accuracy"] * 0.2) + (metrics["consistency_index"] * 0.2)
        
        leaderboard.append({
            "student_id": student["student_id"],
            "name": student["name"],
            "score": round(score, 2),
            "avg_score": metrics["avg_score"],
            "accuracy": metrics["accuracy"],
            "strengths": [t["chapter"] for t in analysis["strong_topics"][:2]],
            "weaknesses": [t["chapter"] for t in analysis["weak_topics"][:2]],
            "focus_area": analysis["weak_topics"][0]["chapter"] if analysis["weak_topics"] else "General"
        })
    
    # Rank by score
    leaderboard.sort(key=lambda x: x["score"], reverse=True)
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
        
    return leaderboard