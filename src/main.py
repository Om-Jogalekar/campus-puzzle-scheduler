import argparse
import csv
from pathlib import Path

from src.evaluator import evaluate_schedule
from src.graph_engine import build_conflict_graph, graph_summary, welsh_powell_coloring
from src.greedy_solver import solve_greedy
from src.parser import load_problem
from src.optimizer import optimise_rooms_from_coloring
from src.backtracker import repair_with_backtracking


def write_schedule_csv(output_path: Path, result, classes, rooms, time_slots) -> None:


    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "status",
            "class_id",
            "module",
            "slot_id",
            "day",
            "start",
            "end",
            "room_id",
            "campus",
            "students",
            "room_capacity",
            "waste_or_reason",
        ])

        for assignment in result.assignments:
            course = classes[assignment.class_id]
            room = rooms[assignment.room_id]
            slot = time_slots[assignment.slot_id]

            waste_text = "Perfect Fit" if assignment.waste == 0 else f"Wasted {assignment.waste} seats"

            writer.writerow([
                "Scheduled",
                course.class_id,
                course.module,
                slot.slot_id,
                slot.day,
                slot.start,
                slot.end,
                room.room_id,
                room.campus,
                course.students,
                room.capacity,
                waste_text,
            ])

        for class_id, reason in result.unscheduled.items():
            course = classes[class_id]

            writer.writerow([
                "Unscheduled",
                course.class_id,
                course.module,
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                course.campus,
                course.students,
                "N/A",
                reason,
            ])


def write_graph_coloring_csv(output_path: Path, color_assignment, classes, time_slots) -> None:


    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "class_id",
            "module",
            "assigned_slot_id",
            "day",
            "start",
            "end",
            "professor_id",
            "student_groups",
        ])

        for class_id, slot_id in color_assignment.items():
            course = classes[class_id]

            if slot_id == "UNCOLORED":
                writer.writerow([
                    class_id,
                    course.module,
                    "UNCOLORED",
                    "N/A",
                    "N/A",
                    "N/A",
                    course.professor_id,
                    ", ".join(sorted(course.student_groups)),
                ])
            else:
                slot = time_slots[slot_id]

                writer.writerow([
                    class_id,
                    course.module,
                    slot.slot_id,
                    slot.day,
                    slot.start,
                    slot.end,
                    course.professor_id,
                    ", ".join(sorted(course.student_groups)),
                ])


def print_schedule(result, classes, rooms, time_slots, title: str) -> None:


    print(f"\n=== {title} ===")

    for assignment in result.assignments:
        course = classes[assignment.class_id]
        room = rooms[assignment.room_id]
        slot = time_slots[assignment.slot_id]

        waste_text = "Perfect Fit" if assignment.waste == 0 else f"Wasted {assignment.waste} seats"

        print(
            f"Scheduled   {course.class_id:<10} "
            f"{course.module:<28} "
            f"{slot.day:<10} {slot.start}-{slot.end:<13} "
            f"{room.room_id:<15} "
            f"{waste_text}"
        )

    if result.unscheduled:
        print("\n=== UNSCHEDULED CLASSES ===")

        for class_id, reason in result.unscheduled.items():
            course = classes[class_id]
            print(
                f"Unscheduled {course.class_id:<10} "
                f"{course.module:<28} "
                f"Reason: {reason}"
            )


def print_metrics(metrics) -> None:


    print("\n=== GREEDY SUMMARY METRICS ===")

    for key, value in metrics.items():
        print(f"{key}: {value}")


def print_graph(graph, classes) -> None:


    print("\n=== STAGE 2: CONFLICT GRAPH ===")

    for class_id, neighbours in graph.items():
        neighbour_text = ", ".join(sorted(neighbours)) if neighbours else "No conflicts"
        print(f"{class_id:<10} -> {neighbour_text}")


def print_graph_coloring(color_assignment, classes, time_slots) -> None:
  

    print("\n=== STAGE 2: WELSH-POWELL TIME-SLOT ASSIGNMENT ===")

    for class_id, slot_id in color_assignment.items():
        course = classes[class_id]

        if slot_id == "UNCOLORED":
            print(f"{class_id:<10} {course.module:<28} UNCOLORED")
        else:
            slot = time_slots[slot_id]
            print(
                f"{class_id:<10} "
                f"{course.module:<28} "
                f"{slot.day:<10} {slot.start}-{slot.end}"
            )

def write_results_summary_csv(output_path: Path, rows) -> None:


    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "stage",
            "scheduled_classes",
            "room_conflicts",
            "professor_conflicts",
            "student_group_conflicts",
            "capacity_violations",
            "feature_violations",
            "campus_violations",
            "professor_availability_violations",
            "room_availability_violations",
            "total_waste",
        ])

        for row in rows:
            writer.writerow([
                row["stage"],
                row["metrics"]["scheduled_classes"],
                row["metrics"]["room_conflicts"],
                row["metrics"]["professor_conflicts"],
                row["metrics"]["student_group_conflicts"],
                row["metrics"]["capacity_violations"],
                row["metrics"]["feature_violations"],
                row["metrics"]["campus_violations"],
                row["metrics"]["professor_availability_violations"],
                row["metrics"]["room_availability_violations"],
                row["metrics"]["total_waste"],
            ])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Campus Puzzle Scheduler"
    )

    parser.add_argument(
        "--data",
        default="data/processed/constraints.json",
        help="Path to constraints JSON file",
    )

    parser.add_argument(
        "--greedy-output",
        default="outputs/greedy_schedule.csv",
        help="Path to save greedy CSV output",
    )

    parser.add_argument(
        "--graph-output",
        default="outputs/graph_coloring_schedule.csv",
        help="Path to save graph coloring CSV output",
    )
    parser.add_argument(
        "--dp-output",
        default="outputs/dp_optimised_schedule.csv",
        help="Path to save DP optimised schedule CSV output",
    )
    parser.add_argument(
    "--final-output",
    default="outputs/final_schedule.csv",
    help="Path to save final repaired schedule CSV output",
    )

    args = parser.parse_args()

    time_slots, rooms, professors, student_groups, classes = load_problem(args.data)

    
    greedy_result = solve_greedy(
        time_slots=time_slots,
        rooms=rooms,
        professors=professors,
        classes=classes,
    )

    greedy_metrics = evaluate_schedule(
        assignments=greedy_result.assignments,
        classes=classes,
        rooms=rooms,
        professors=professors,
    )

    print_schedule(
    greedy_result,
    classes,
    rooms,
    time_slots,
    title="STAGE 1: GREEDY BASELINE SCHEDULE",
)
    print_metrics(greedy_metrics)

    write_schedule_csv(
        output_path=Path(args.greedy_output),
        result=greedy_result,
        classes=classes,
        rooms=rooms,
        time_slots=time_slots,
    )

    
    graph = build_conflict_graph(classes)
    summary = graph_summary(graph)
    color_assignment = welsh_powell_coloring(
        graph=graph,
        classes=classes,
        professors=professors,
        time_slots=time_slots,
    )

    print_graph(graph, classes)

    print("\n=== GRAPH SUMMARY ===")
    for key, value in summary.items():
        print(f"{key}: {value}")

    print_graph_coloring(color_assignment, classes, time_slots)

    write_graph_coloring_csv(
        output_path=Path(args.graph_output),
        color_assignment=color_assignment,
        classes=classes,
        time_slots=time_slots,
    )

   
    dp_result = optimise_rooms_from_coloring(
        color_assignment=color_assignment,
        classes=classes,
        rooms=rooms,
        time_slots=time_slots,
    )

    dp_metrics = evaluate_schedule(
        assignments=dp_result.assignments,
        classes=classes,
        rooms=rooms,
        professors=professors,
    )

    print_schedule(
        dp_result,
        classes,
        rooms,
        time_slots,
        title="STAGE 3: DP ROOM-OPTIMISED SCHEDULE",
    )

    print("\n=== DP SUMMARY METRICS ===")
    for key, value in dp_metrics.items():
        print(f"{key}: {value}")

    if dp_result.unscheduled:
        print("\n=== DP UNSCHEDULED CLASSES ===")
        for class_id, reason in dp_result.unscheduled.items():
            print(f"{class_id}: {reason}")

    write_schedule_csv(
        output_path=Path(args.dp_output),
        result=dp_result,
        classes=classes,
        rooms=rooms,
        time_slots=time_slots,
    )

    # Stage 4: Backtracking repair
    final_result = repair_with_backtracking(
        base_result=dp_result,
        classes=classes,
        rooms=rooms,
        professors=professors,
        time_slots=time_slots,
    )

    final_metrics = evaluate_schedule(
        assignments=final_result.assignments,
        classes=classes,
        rooms=rooms,
        professors=professors,
    )

    print_schedule(
        final_result,
        classes,
        rooms,
        time_slots,
        title="STAGE 4: BACKTRACKING REPAIRED FINAL SCHEDULE",
    )

    print("\n=== FINAL SUMMARY METRICS ===")
    for key, value in final_metrics.items():
        print(f"{key}: {value}")

    if final_result.unscheduled:
        print("\n=== FINAL UNSCHEDULED CLASSES ===")
        for class_id, reason in final_result.unscheduled.items():
            print(f"{class_id}: {reason}")

    write_schedule_csv(
        output_path=Path(args.final_output),
        result=final_result,
        classes=classes,
        rooms=rooms,
        time_slots=time_slots,
    )

    print(f"\nSaved greedy CSV output to: {args.greedy_output}")
    print(f"Saved graph-coloring CSV output to: {args.graph_output}")
    print(f"Saved DP optimised CSV output to: {args.dp_output}")
    print(f"Saved final repaired CSV output to: {args.final_output}")
    write_results_summary_csv(
    output_path=Path("outputs/results_summary.csv"),
    rows=[
        {
            "stage": "Greedy Baseline",
            "metrics": greedy_metrics,
        },
        {
            "stage": "Graph Coloring + DP Room Optimisation",
            "metrics": dp_metrics,
        },
        {
            "stage": "Backtracking Final Repair",
            "metrics": final_metrics,
        },
        ],
    )

    print("Saved results summary to: outputs/results_summary.csv")

if __name__ == "__main__":
    main()