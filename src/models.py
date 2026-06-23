from dataclasses import dataclass, field
from typing import Dict, List, Set, Union


@dataclass(frozen=True)
class TimeSlot:

    slot_id: str
    day: str
    start: str
    end: str


@dataclass(frozen=True)
class Room:

    room_id: str
    campus: str
    capacity: int
    features: Set[str] = field(default_factory=set)
    available_slots: Union[str, Set[str]] = "ALL"


@dataclass(frozen=True)
class Professor:

    professor_id: str
    name: str
    professor_type: str
    availability_note: str
    available_slots: Union[str, Set[str]] = "ALL"


@dataclass(frozen=True)
class StudentGroup:

    group_id: str
    programme: str
    year: int
    size: int


@dataclass(frozen=True)
class CourseClass:

    class_id: str
    module: str
    students: int
    professor_id: str
    student_groups: Set[str]
    campus: str
    required_features: Set[str] = field(default_factory=set)
    priority: str = "MEDIUM"


@dataclass
class Assignment:

    class_id: str
    slot_id: str
    room_id: str
    waste: int


@dataclass
class ScheduleResult:

    assignments: List[Assignment]
    unscheduled: Dict[str, str]
    total_waste: int