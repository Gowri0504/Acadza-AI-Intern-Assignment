from app.utils import get_qid, load_json
import random
import os

def recommend_plan(analysis, questions):
    steps = []
    
    # Load DOST config for parameters
    config = load_json("data/dost_config.json")
    
    # 1. Normalize questions
    valid_questions = []
    for q in questions:
        qid = get_qid(q)
        if qid:
            valid_questions.append(q)

    # Helper to get questions
    def get_qs(topic, difficulty_range, count=5):
        filtered = [q for q in valid_questions if any(ch.lower() in (q.get("topic") or "").lower() or ch.lower() in (q.get("subtopic") or "").lower() for ch in [topic])]
        if not filtered:
            filtered = [q for q in valid_questions if topic.lower() in (q.get("subject") or "").lower()]
            
        diff_filtered = [q for q in filtered if q.get("difficulty", 3) in difficulty_range]
        if not diff_filtered:
            diff_filtered = filtered
            
        random.shuffle(diff_filtered)
        return diff_filtered[:count]

    weak_topics = analysis.get("weak_topics", [])
    speed_issues = analysis.get("speed_issues", [])
    metrics = analysis.get("metrics", {})
    
    current_step = 1

    # 1. Foundation: Concept/Formula
    if weak_topics:
        top_weak = weak_topics[0]["chapter"]
        steps.append({
            "step": current_step,
            "dost": "concept",
            "parameters": config.get("concept", {}).get("params", {}),
            "chapter": top_weak,
            "question_ids": [],
            "reasoning": f"Your score in {top_weak} ({weak_topics[0]['avg_score']}%) indicates a conceptual gap.",
            "message": f"Let's start by reinforcing your core understanding of {top_weak}."
        })
        current_step += 1
        
        steps.append({
            "step": current_step,
            "dost": "formula",
            "parameters": config.get("formula", {}).get("params", {}),
            "chapter": top_weak,
            "question_ids": [],
            "reasoning": "Quick formula recall is essential for solving JEE/NEET problems efficiently.",
            "message": f"Review these key formulas for {top_weak} before practice."
        })
        current_step += 1

    # 2. Accuracy: Picking Power
    if metrics.get("accuracy", 100) < 75:
        steps.append({
            "step": current_step,
            "dost": "pickingPower",
            "parameters": config.get("pickingPower", {}).get("params", {}),
            "reasoning": f"Your accuracy is {metrics['accuracy']}%. You need to work on option elimination.",
            "message": "Let's practice 'Picking Power' to help you identify correct options more reliably."
        })
        current_step += 1

    # 3. Practice: Practice Assignment
    if weak_topics:
        top_weak = weak_topics[0]["chapter"]
        easy_qs = get_qs(top_weak, [1, 2], 5)
        steps.append({
            "step": current_step,
            "dost": "practiceAssignment",
            "parameters": {**config.get("practiceAssignment", {}).get("params", {}), "difficulty": "easy"},
            "chapter": top_weak,
            "question_ids": [get_qid(q) for q in easy_qs],
            "reasoning": "Building confidence with easy-level application is the next logical step.",
            "message": f"Now, apply your knowledge with these 5 selected questions from {top_weak}."
        })
        current_step += 1

    # 4. Speed: Clicking Power or Speed Race
    if speed_issues:
        topic = speed_issues[0]["chapter"]
        if metrics.get("avg_score", 0) > 60:
            # High score but slow -> Speed Race (competitive)
            steps.append({
                "step": current_step,
                "dost": "speedRace",
                "parameters": config.get("speedRace", {}).get("params", {}),
                "chapter": topic,
                "question_ids": [get_qid(q) for q in get_qs(topic, [2, 3], 10)],
                "reasoning": f"You have good scores in {topic} but take too long. A competitive race will push your limits.",
                "message": "Challenge Mode! Race against a bot to improve your speed in this topic."
            })
        else:
            # Low score and slow -> Clicking Power (drill)
            steps.append({
                "step": current_step,
                "dost": "clickingPower",
                "parameters": config.get("clickingPower", {}).get("params", {}),
                "chapter": topic,
                "question_ids": [get_qid(q) for q in get_qs(topic, [1, 2], 10)],
                "reasoning": f"You're struggling with both speed and accuracy in {topic}. Rapid drills will help.",
                "message": "Speed Drill! Answer these questions as quickly as possible."
            })
        current_step += 1

    # 5. Long-term: Revision
    if len(weak_topics) > 3:
        steps.append({
            "step": current_step,
            "dost": "revision",
            "parameters": {**config.get("revision", {}).get("params", {}), "alloted_days": 5},
            "reasoning": f"You have {len(weak_topics)} weak chapters. A structured 5-day revision plan is recommended.",
            "message": "We've scheduled a comprehensive revision plan for you starting tomorrow."
        })
        current_step += 1

    # 6. Evaluation: Practice Test
    target_topic = weak_topics[0]["chapter"] if weak_topics else "Overall"
    test_qs = get_qs(target_topic, [2, 3, 4], 15)
    steps.append({
        "step": current_step,
        "dost": "practiceTest",
        "parameters": {**config.get("practiceTest", {}).get("params", {}), "duration_minutes": 45},
        "chapter": target_topic,
        "question_ids": [get_qid(q) for q in test_qs],
        "reasoning": "A final timed evaluation to measure your progress from this study session.",
        "message": "Final check! Complete this 45-minute test to see how much you've improved."
    })

    return {
        "student_id": analysis["student_id"],
        "plan_summary": f"Targeted improvement plan focusing on {target_topic} and overall {metrics.get('overall_trend', 'performance')}.",
        "steps": steps
    }