from src.parser import load_problem, validate_problem


def main():
    data_path = "data/processed/constraints.json"

    time_slots, rooms, professors, student_groups, classes = load_problem(data_path)

    print("=== DATASET SUMMARY ===")
    print(f"Time slots: {len(time_slots)}")
    print(f"Rooms: {len(rooms)}")
    print(f"Professors: {len(professors)}")
    print(f"Student groups: {len(student_groups)}")
    print(f"Classes: {len(classes)}")

    errors = validate_problem(
        rooms=rooms,
        professors=professors,
        student_groups=student_groups,
        classes=classes,
    )

    print("\n=== VALIDATION ===")

    if errors:
        print("Dataset has problems:")
        for error in errors:
            print(f"- {error}")
    else:
        print("Dataset is valid and ready for scheduling.")


if __name__ == "__main__":
    main()