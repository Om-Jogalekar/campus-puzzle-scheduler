from typing import Dict, List, Set, Tuple

from src.greedy_solver import room_is_feasible, slot_available
from src.models import Assignment, CourseClass, Professor, Room, ScheduleResult, TimeSlot


def build_busy_sets(
    assignments: List[Assignment],
    classes: Dict[str, CourseClass],
) -> Tuple[Set[Tuple[str, str]], Set[Tuple[str, str]], Set[Tuple[str, str]]]:


    used_rooms: Set[Tuple[str, str]] = set()
    busy_professors: Set[Tuple[str, str]] = set()
    busy_student_groups: Set[Tuple[str, str]] = set()

    for assignment in assignments:
        course = classes[assignment.class_id]

        used_rooms.add((assignment.slot_id, assignment.room_id))
        busy_professors.add((assignment.slot_id, course.professor_id))

        for group_id in course.student_groups:
            busy_student_groups.add((assignment.slot_id, group_id))

    return used_rooms, busy_professors, busy_student_groups


def assignment_is_valid(
    course: CourseClass,
    professor: Professor,
    room: Room,
    slot_id: str,
    used_rooms: Set[Tuple[str, str]],
    busy_professors: Set[Tuple[str, str]],
    busy_student_groups: Set[Tuple[str, str]],
) -> bool:
   

    if not slot_available(professor.available_slots, slot_id):
        return False

    if not room_is_feasible(course, room, slot_id):
        return False

    if (slot_id, room.room_id) in used_rooms:
        return False

    if (slot_id, course.professor_id) in busy_professors:
        return False

    for group_id in course.student_groups:
        if (slot_id, group_id) in busy_student_groups:
            return False

    return True


def repair_with_backtracking(
    base_result: ScheduleResult,
    classes: Dict[str, CourseClass],
    rooms: Dict[str, Room],
    professors: Dict[str, Professor],
    time_slots: Dict[str, TimeSlot],
) -> ScheduleResult:


    assignments = list(base_result.assignments)
    unscheduled_ids = list(base_result.unscheduled.keys())

    used_rooms, busy_professors, busy_student_groups = build_busy_sets(
        assignments=assignments,
        classes=classes,
    )

    still_unscheduled: Dict[str, str] = {}

    def backtrack(index: int) -> bool:


        if index == len(unscheduled_ids):
            return True

        class_id = unscheduled_ids[index]
        course = classes[class_id]
        professor = professors[course.professor_id]

        candidate_moves = []

        for slot_id in time_slots.keys():
            for room in rooms.values():
                if assignment_is_valid(
                    course=course,
                    professor=professor,
                    room=room,
                    slot_id=slot_id,
                    used_rooms=used_rooms,
                    busy_professors=busy_professors,
                    busy_student_groups=busy_student_groups,
                ):
                    waste = room.capacity - course.students
                    candidate_moves.append((waste, slot_id, room))

        candidate_moves.sort(key=lambda item: item[0])

        for waste, slot_id, room in candidate_moves:
            new_assignment = Assignment(
                class_id=course.class_id,
                slot_id=slot_id,
                room_id=room.room_id,
                waste=waste,
            )

            assignments.append(new_assignment)
            used_rooms.add((slot_id, room.room_id))
            busy_professors.add((slot_id, course.professor_id))

            for group_id in course.student_groups:
                busy_student_groups.add((slot_id, group_id))

            if backtrack(index + 1):
                return True

            assignments.pop()
            used_rooms.remove((slot_id, room.room_id))
            busy_professors.remove((slot_id, course.professor_id))

            for group_id in course.student_groups:
                busy_student_groups.remove((slot_id, group_id))

        still_unscheduled[class_id] = "Backtracking could not find a valid repair."
        return False

    backtrack(0)

    scheduled_ids = {assignment.class_id for assignment in assignments}

    final_unscheduled = {
        class_id: reason
        for class_id, reason in still_unscheduled.items()
        if class_id not in scheduled_ids
    }

    total_waste = sum(assignment.waste for assignment in assignments)

    return ScheduleResult(
        assignments=assignments,
        unscheduled=final_unscheduled,
        total_waste=total_waste,
    )