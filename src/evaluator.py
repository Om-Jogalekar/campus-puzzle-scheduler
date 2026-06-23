from typing import Dict, List, Tuple

from src.models import Assignment, CourseClass, Professor, Room


def evaluate_schedule(
    assignments: List[Assignment],
    classes: Dict[str, CourseClass],
    rooms: Dict[str, Room],
    professors: Dict[str, Professor],
) -> Dict[str, int]:


    room_usage: Dict[Tuple[str, str], int] = {}
    professor_usage: Dict[Tuple[str, str], int] = {}
    group_usage: Dict[Tuple[str, str], int] = {}

    capacity_violations = 0
    feature_violations = 0
    campus_violations = 0
    professor_availability_violations = 0
    room_availability_violations = 0
    total_waste = 0

    for assignment in assignments:
        course = classes[assignment.class_id]
        room = rooms[assignment.room_id]
        professor = professors[course.professor_id]

        room_key = (assignment.slot_id, assignment.room_id)
        professor_key = (assignment.slot_id, course.professor_id)

        room_usage[room_key] = room_usage.get(room_key, 0) + 1
        professor_usage[professor_key] = professor_usage.get(professor_key, 0) + 1

        for group_id in course.student_groups:
            group_key = (assignment.slot_id, group_id)
            group_usage[group_key] = group_usage.get(group_key, 0) + 1

        if room.capacity < course.students:
            capacity_violations += 1

        if not course.required_features.issubset(room.features):
            feature_violations += 1

        if course.campus != room.campus:
            campus_violations += 1

        if professor.available_slots != "ALL" and assignment.slot_id not in professor.available_slots:
            professor_availability_violations += 1

        if room.available_slots != "ALL" and assignment.slot_id not in room.available_slots:
            room_availability_violations += 1

        total_waste += max(0, room.capacity - course.students)

    return {
        "scheduled_classes": len(assignments),
        "room_conflicts": sum(1 for count in room_usage.values() if count > 1),
        "professor_conflicts": sum(1 for count in professor_usage.values() if count > 1),
        "student_group_conflicts": sum(1 for count in group_usage.values() if count > 1),
        "capacity_violations": capacity_violations,
        "feature_violations": feature_violations,
        "campus_violations": campus_violations,
        "professor_availability_violations": professor_availability_violations,
        "room_availability_violations": room_availability_violations,
        "total_waste": total_waste,
    }