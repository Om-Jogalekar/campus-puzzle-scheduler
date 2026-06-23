from typing import Dict, List, Set

from src.models import CourseClass, Professor, TimeSlot


def classes_conflict(class_a: CourseClass, class_b: CourseClass) -> bool:


    same_professor = class_a.professor_id == class_b.professor_id
    shared_student_group = bool(class_a.student_groups.intersection(class_b.student_groups))

    return same_professor or shared_student_group


def build_conflict_graph(
    classes: Dict[str, CourseClass],
) -> Dict[str, Set[str]]:


    graph = {class_id: set() for class_id in classes.keys()}

    class_list = list(classes.values())

    for i in range(len(class_list)):
        for j in range(i + 1, len(class_list)):
            class_a = class_list[i]
            class_b = class_list[j]

            if classes_conflict(class_a, class_b):
                graph[class_a.class_id].add(class_b.class_id)
                graph[class_b.class_id].add(class_a.class_id)

    return graph


def professor_available(professor: Professor, slot_id: str) -> bool:


    if professor.available_slots == "ALL":
        return True

    return slot_id in professor.available_slots


def welsh_powell_coloring(
    graph: Dict[str, Set[str]],
    classes: Dict[str, CourseClass],
    professors: Dict[str, Professor],
    time_slots: Dict[str, TimeSlot],
) -> Dict[str, str]:


    ordered_class_ids = sorted(
        graph.keys(),
        key=lambda class_id: len(graph[class_id]),
        reverse=True,
    )

    color_assignment: Dict[str, str] = {}

    for class_id in ordered_class_ids:
        course = classes[class_id]
        professor = professors[course.professor_id]

        for slot_id in time_slots.keys():
            if not professor_available(professor, slot_id):
                continue

            neighbour_slots = {
                color_assignment[neighbour_id]
                for neighbour_id in graph[class_id]
                if neighbour_id in color_assignment
            }

            if slot_id not in neighbour_slots:
                color_assignment[class_id] = slot_id
                break

        if class_id not in color_assignment:
            color_assignment[class_id] = "UNCOLORED"

    return color_assignment


def graph_summary(graph: Dict[str, Set[str]]) -> Dict[str, int]:


    number_of_nodes = len(graph)
    number_of_edges = sum(len(neighbours) for neighbours in graph.values()) // 2
    max_degree = max((len(neighbours) for neighbours in graph.values()), default=0)

    return {
        "nodes": number_of_nodes,
        "edges": number_of_edges,
        "max_degree": max_degree,
    }