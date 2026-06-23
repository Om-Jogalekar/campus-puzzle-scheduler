from itertools import combinations
from typing import Dict, List, Optional, Tuple

from src.models import Assignment, CourseClass, Room, ScheduleResult, TimeSlot


def slot_available(available_slots, slot_id: str) -> bool:

    if available_slots == "ALL":
        return True

    return slot_id in available_slots


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


def solve_dp_exact(
    slot_id: str,
    slot_classes: List[CourseClass],
    room_list: List[Room],
) -> Optional[List[Assignment]]:

    n = len(slot_classes)
    m = len(room_list)

    INF = 10**9

    dp = [[INF for _ in range(m + 1)] for _ in range(n + 1)]
    decision: List[List[Optional[str]]] = [[None for _ in range(m + 1)] for _ in range(n + 1)]

    for j in range(m + 1):
        dp[0][j] = 0

    for i in range(1, n + 1):
        course = slot_classes[i - 1]

        for j in range(1, m + 1):
            room = room_list[j - 1]

            # Option 1: skip this room.
            dp[i][j] = dp[i][j - 1]
            decision[i][j] = "SKIP"

           
            if room_is_feasible(course, room, slot_id):
                waste = room.capacity - course.students
                candidate = dp[i - 1][j - 1] + waste

                if candidate < dp[i][j]:
                    dp[i][j] = candidate
                    decision[i][j] = "USE"

    if dp[n][m] >= INF:
        return None

    assignments: List[Assignment] = []

    i = n
    j = m

    while i > 0 and j > 0:
        course = slot_classes[i - 1]
        room = room_list[j - 1]

        if decision[i][j] == "USE":
            assignments.append(
                Assignment(
                    class_id=course.class_id,
                    slot_id=slot_id,
                    room_id=room.room_id,
                    waste=room.capacity - course.students,
                )
            )
            i -= 1
            j -= 1
        else:
            j -= 1

    assignments.reverse()
    return assignments


def optimise_rooms_for_slot(
    slot_id: str,
    class_ids: List[str],
    classes: Dict[str, CourseClass],
    rooms: Dict[str, Room],
) -> Tuple[List[Assignment], Dict[str, str]]:

    slot_classes = [classes[class_id] for class_id in class_ids]

    # Harder classes first helps subset selection.
    slot_classes.sort(
        key=lambda course: (
            course.students,
            len(course.required_features),
            len(course.student_groups),
        ),
        reverse=True,
    )

    room_list = list(rooms.values())
    room_list.sort(key=lambda room: room.capacity)

    # Try to schedule all classes first, then smaller subsets.
    for subset_size in range(len(slot_classes), 0, -1):
        best_assignments = None
        best_waste = None
        best_subset_ids = set()

        for subset in combinations(slot_classes, subset_size):
            subset = list(subset)

            # DP expects classes sorted by size ascending.
            subset.sort(key=lambda course: course.students)

            assignments = solve_dp_exact(
                slot_id=slot_id,
                slot_classes=subset,
                room_list=room_list,
            )

            if assignments is None:
                continue

            waste = sum(assignment.waste for assignment in assignments)

            if best_waste is None or waste < best_waste:
                best_assignments = assignments
                best_waste = waste
                best_subset_ids = {course.class_id for course in subset}

        if best_assignments is not None:
            unscheduled = {}

            for course in slot_classes:
                if course.class_id not in best_subset_ids:
                    unscheduled[course.class_id] = (
                        f"No feasible room assignment in slot {slot_id}"
                    )

            return best_assignments, unscheduled

    # If not even one class can be scheduled.
    unscheduled = {
        course.class_id: f"No feasible room assignment in slot {slot_id}"
        for course in slot_classes
    }

    return [], unscheduled


def optimise_rooms_from_coloring(
    color_assignment: Dict[str, str],
    classes: Dict[str, CourseClass],
    rooms: Dict[str, Room],
    time_slots: Dict[str, TimeSlot],
) -> ScheduleResult:

    classes_by_slot: Dict[str, List[str]] = {}
    unscheduled: Dict[str, str] = {}

    for class_id, slot_id in color_assignment.items():
        if slot_id == "UNCOLORED":
            unscheduled[class_id] = "Graph coloring could not assign a time slot."
            continue

        classes_by_slot.setdefault(slot_id, []).append(class_id)

    all_assignments: List[Assignment] = []

    for slot_id, class_ids in classes_by_slot.items():
        slot_assignments, slot_unscheduled = optimise_rooms_for_slot(
            slot_id=slot_id,
            class_ids=class_ids,
            classes=classes,
            rooms=rooms,
        )

        all_assignments.extend(slot_assignments)
        unscheduled.update(slot_unscheduled)

    scheduled_class_ids = {assignment.class_id for assignment in all_assignments}

    for class_id, slot_id in color_assignment.items():
        if slot_id != "UNCOLORED" and class_id not in scheduled_class_ids:
            unscheduled.setdefault(
                class_id,
                f"Class had slot {slot_id}, but no feasible room was assigned.",
            )

    total_waste = sum(assignment.waste for assignment in all_assignments)

    return ScheduleResult(
        assignments=all_assignments,
        unscheduled=unscheduled,
        total_waste=total_waste,
    )