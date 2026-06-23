import json
from pathlib import Path
from typing import Dict, List, Tuple

from src.models import CourseClass, Professor, Room, StudentGroup, TimeSlot


def convert_slots(value):

    if value == "ALL":
        return "ALL"

    return set(value)


def load_problem(
    path: str,
) -> Tuple[
    Dict[str, TimeSlot],
    Dict[str, Room],
    Dict[str, Professor],
    Dict[str, StudentGroup],
    Dict[str, CourseClass],
]:

    data_path = Path(path)

    if not data_path.exists():
        raise FileNotFoundError(f"Could not find input file: {data_path}")

    with data_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    time_slots = {
        item["slot_id"]: TimeSlot(
            slot_id=item["slot_id"],
            day=item["day"],
            start=item["start"],
            end=item["end"],
        )
        for item in data["time_slots"]
    }

    rooms = {
        item["room_id"]: Room(
            room_id=item["room_id"],
            campus=item["campus"],
            capacity=int(item["capacity"]),
            features=set(item.get("features", [])),
            available_slots=convert_slots(item.get("available_slots", "ALL")),
        )
        for item in data["rooms"]
    }

    professors = {
        item["professor_id"]: Professor(
            professor_id=item["professor_id"],
            name=item["name"],
            professor_type=item["type"],
            availability_note=item.get("availability_note", ""),
            available_slots=convert_slots(item.get("available_slots", "ALL")),
        )
        for item in data["professors"]
    }

    student_groups = {
        item["group_id"]: StudentGroup(
            group_id=item["group_id"],
            programme=item["programme"],
            year=int(item["year"]),
            size=int(item["size"]),
        )
        for item in data["student_groups"]
    }

    classes = {
        item["class_id"]: CourseClass(
            class_id=item["class_id"],
            module=item["module"],
            students=int(item["students"]),
            professor_id=item["professor_id"],
            student_groups=set(item.get("student_groups", [])),
            campus=item["campus"],
            required_features=set(item.get("required_features", [])),
            priority=item.get("priority", "MEDIUM"),
        )
        for item in data["classes"]
    }

    return time_slots, rooms, professors, student_groups, classes


def validate_problem(
    rooms: Dict[str, Room],
    professors: Dict[str, Professor],
    student_groups: Dict[str, StudentGroup],
    classes: Dict[str, CourseClass],
) -> List[str]:

    errors = []

    for class_id, course in classes.items():
        if course.professor_id not in professors:
            errors.append(
                f"{class_id}: professor '{course.professor_id}' does not exist."
            )

        for group_id in course.student_groups:
            if group_id not in student_groups:
                errors.append(
                    f"{class_id}: student group '{group_id}' does not exist."
                )

        if course.students <= 0:
            errors.append(
                f"{class_id}: number of students must be greater than zero."
            )

        possible_rooms = [
            room
            for room in rooms.values()
            if room.campus == course.campus
            and room.capacity >= course.students
            and course.required_features.issubset(room.features)
        ]

        if not possible_rooms:
            errors.append(
                f"{class_id}: no room can satisfy campus, capacity, and feature requirements."
            )

    return errors