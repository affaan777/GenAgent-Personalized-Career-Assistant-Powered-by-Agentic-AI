#!/usr/bin/env python3
"""
Script to add all Coursera courses from a JSON file to the FAISS database.
"""

import json
from tools.course_fetcher import add_coursera_course_to_faiss

COURSE_JSON = "complete_courses_20250629_151826.json"

def add_all_coursera_courses_from_json():
    with open(COURSE_JSON, "r", encoding="utf-8") as f:
        courses = json.load(f)
    added = 0
    for i, course in enumerate(courses, 1):
        # Defensive: skip if not a dict or missing required fields
        if not isinstance(course, dict):
            print(f"Skipping non-dict entry at index {i}")
            continue
        title = course.get("title", "").strip()
        url = course.get("url", "").strip()
        institution = course.get("instructor", "").strip() or course.get("platform", "").strip()
        rating = str(course.get("rating", ""))
        description = course.get("description", "").strip()
        if not title or not url:
            print(f"Skipping entry missing title or url at index {i}")
            continue
        result = add_coursera_course_to_faiss(title, url, institution, rating, description)
        print(f"{i}. {title} - {result}")
        added += 1
    print(f"\n✅ Added {added} Coursera courses to FAISS from {COURSE_JSON}")

if __name__ == "__main__":
    add_all_coursera_courses_from_json() 