import re

def normalize_marks(marks):
    if isinstance(marks, (int, float)):
        return float(marks)

    marks_str = str(marks).strip()
    
    # Handle "68/100" or "34/75 (45.3%)"
    if "/" in marks_str:
        nums = re.findall(r'(\d+\.?\d*)', marks_str)
        if len(nums) >= 2:
            return (float(nums[0]) / float(nums[1])) * 100

    # Handle "+52 -12"
    if "+" in marks_str or "-" in marks_str:
        nums = re.findall(r'([-+]?\d+\.?\d*)', marks_str)
        if nums:
            return sum(float(n) for n in nums)

    # Handle percentage or just number
    nums = re.findall(r'(\d+\.?\d*)', marks_str)
    if nums:
        return float(nums[0])
    
    return 0.0

def get_qid(q):
    if isinstance(q.get("_id"), dict):
        return q["_id"].get("$oid")
    return q.get("_id")

def load_json(path):
    import json
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)