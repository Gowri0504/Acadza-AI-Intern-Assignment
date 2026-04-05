from app.utils import normalize_marks

def analyze_student(student):
    attempts = student.get("attempts", [])
    if not attempts:
        return {"error": "No attempts found for student"}

    chapter_stats = {}
    total_score = 0
    total_questions = 0
    total_attempted = 0
    total_time_taken = 0
    
    # Sort attempts by date to calculate trends
    sorted_attempts = sorted(attempts, key=lambda x: x["date"])
    recent_scores = [normalize_marks(a["marks"]) for a in sorted_attempts[-3:]]
    trend = "improving" if len(recent_scores) > 1 and recent_scores[-1] > recent_scores[0] else "declining" if len(recent_scores) > 1 and recent_scores[-1] < recent_scores[0] else "stable"

    for att in sorted_attempts:
        marks_percent = normalize_marks(att["marks"])
        total_score += marks_percent
        
        att_questions = att.get("total_questions", 0)
        att_attempted = att.get("attempted", 0)
        total_questions += att_questions
        total_attempted += att_attempted
        total_time_taken += att.get("time_taken_minutes", 0)
        
        for ch in att["chapters"]:
            if ch not in chapter_stats:
                chapter_stats[ch] = {"scores": [], "attempts": 0, "time": 0}
            chapter_stats[ch]["scores"].append(marks_percent)
            chapter_stats[ch]["attempts"] += 1
            chapter_stats[ch]["time"] += att.get("avg_time_per_question_seconds", 0)

    # Calculate metrics
    processed_chapters = []
    radar_data = {"labels": [], "values": []}

    for ch, stats in chapter_stats.items():
        avg_ch_score = sum(stats["scores"]) / len(stats["scores"])
        avg_ch_time = stats["time"] / stats["attempts"]
        
        ch_info = {
            "chapter": ch,
            "avg_score": round(avg_ch_score, 2),
            "avg_time_per_q": round(avg_ch_time, 2),
            "consistency": round(100 - (max(stats["scores"]) - min(stats["scores"])), 2) if len(stats["scores"]) > 1 else 100,
            "trend": "up" if len(stats["scores"]) > 1 and stats["scores"][-1] > stats["scores"][0] else "down" if len(stats["scores"]) > 1 and stats["scores"][-1] < stats["scores"][0] else "flat"
        }
        processed_chapters.append(ch_info)
        radar_data["labels"].append(ch)
        radar_data["values"].append(round(avg_ch_score, 2))

    # Sort chapters
    weak_chapters = sorted([c for c in processed_chapters if c["avg_score"] < 50], key=lambda x: x["avg_score"])
    strong_chapters = sorted([c for c in processed_chapters if c["avg_score"] >= 70], key=lambda x: x["avg_score"], reverse=True)
    
    # Speed issues - flag if > 180s per question
    speed_issues = sorted([c for c in processed_chapters if c["avg_time_per_q"] > 180], key=lambda x: x["avg_time_per_q"], reverse=True)

    avg_overall_score = total_score / len(attempts)
    overall_accuracy = (total_attempted / total_questions * 100) if total_questions > 0 else 0

    return {
        "student_id": student["student_id"],
        "name": student["name"],
        "metrics": {
            "avg_score": round(avg_overall_score, 2),
            "accuracy": round(overall_accuracy, 2),
            "total_time_spent_min": total_time_taken,
            "consistency_index": round(sum(c["consistency"] for c in processed_chapters) / len(processed_chapters), 2),
            "overall_trend": trend
        },
        "radar_chart": radar_data,
        "weak_topics": weak_chapters,
        "strong_topics": strong_chapters,
        "speed_issues": speed_issues,
        "all_chapters": processed_chapters
    }