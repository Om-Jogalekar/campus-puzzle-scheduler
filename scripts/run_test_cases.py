import subprocess
import sys
from pathlib import Path


TEST_CASES = [
    "data/test_cases/easy_case.json",
    "data/test_cases/tight_rooms_case.json",
    "data/test_cases/professor_conflict_case.json",
    "data/test_cases/student_group_conflict_case.json",
    "data/test_cases/impossible_case.json",
]


def main():
    for test_case in TEST_CASES:
        path = Path(test_case)

        print("\n" + "=" * 80)
        print(f"RUNNING TEST CASE: {path}")
        print("=" * 80)

        if not path.exists():
            print(f"Missing file: {path}")
            continue

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.main",
                "--data",
                str(path),
                "--greedy-output",
                f"outputs/{path.stem}_greedy.csv",
                "--graph-output",
                f"outputs/{path.stem}_graph.csv",
                "--dp-output",
                f"outputs/{path.stem}_dp.csv",
                "--final-output",
                f"outputs/{path.stem}_final.csv",
            ],
            text=True,
            capture_output=True,
        )

        print(result.stdout)

        if result.stderr:
            print("ERRORS:")
            print(result.stderr)


if __name__ == "__main__":
    main()