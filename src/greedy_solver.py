from typing import Dict, Set, Tuple

from src.models import Assignment, CourseClass, Professor, Room, ScheduleResult, TimeSlot


PRIORITY_SCORE = {
    "HIGH": 30,
    "MEDIUM": 15,
    "LOW": 0,
}


def slot_available(available_slots, slot_id: str) -> bool:

    if available_slots == "ALL":
        return True

    return slot_id in available_slots


def class_difficulty(course: CourseClass) -> int:

    priority = PRIORITY_SCORE.get(course.priority, 0)

    return (
        course.students
        + 10 * len(course.student_groups)
        + 20 * len(course.required_features)
        + priority
    )


def room_is_feasible(course: CourseClass, room: Room, slot_id: str) -> bool:

    if course.campus != room.campus:
        return False

    if room.capacity < course.students:
        return False

    if not course.required_features.issubset(room.features):
        return False

    if not slot_available(room.available_slots, slot_id):
        return False

    return True


def solve_greedy(
    time_slots: Dict[str, TimeSlot],
    rooms: Dict[str, Room],
    professors: Dict[str, Professor],
    classes: Dict[str, CourseClass],
) -> ScheduleResult:


    sorted_classes = sorted(
        classes.values(),
        key=class_difficulty,
        reverse=True,
    )

    used_rooms: Set[Tuple[str, str]] = set()
    busy_professors: Set[Tuple[str, str]] = set()
    busy_student_groups: Set[Tuple[str, str]] = set()

    assignments = []
    unscheduled = {}

    for course in sorted_classes:
        placed = False

        professor = professors.get(course.professor_id)

        if professor is None:
            unscheduled[course.class_id] = f"Professor not found: {course.professor_id}"
            continue

        for slot_id in time_slots.keys():
            if not slot_available(professor.available_slots, slot_id):
                continue

            if (slot_id, course.professor_id) in busy_professors:
                continue

            student_group_clash = any(
                (slot_id, group_id) in busy_student_groups
                for group_id in course.student_groups
            )

            if student_group_clash:
                continue

            feasible_rooms = [
                room
                for room in rooms.values()
                if room_is_feasible(course, room, slot_id)
                and (slot_id, room.room_id) not in used_rooms
            ]

            feasible_rooms.sort(key=lambda room: room.capacity - course.students)

            if feasible_rooms:
                chosen_room = feasible_rooms[0]
                waste = chosen_room.capacity - course.students

                assignments.append(
                    Assignment(
                        class_id=course.class_id,
                        slot_id=slot_id,
                        room_id=chosen_room.room_id,
                        waste=waste,
                    )
                )

                used_rooms.add((slot_id, chosen_room.room_id))
                busy_professors.add((slot_id, course.professor_id))

                for group_id in course.student_groups:
                    busy_student_groups.add((slot_id, group_id))

                placed = True
                break

        if not placed:
            unscheduled[course.class_id] = "No valid slot and room combination found."

    total_waste = sum(assignment.waste for assignment in assignments)

    return ScheduleResult(
        assignments=assignments,
        unscheduled=unscheduled,
        total_waste=total_waste,
    )