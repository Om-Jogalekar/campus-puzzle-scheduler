# Campus Puzzle Scheduler

Campus Puzzle Scheduler is a Python-based university timetabling system developed for the M603 Advanced Algorithms assessment.

The project solves a scheduling problem where university classes must be assigned to valid time slots and rooms while satisfying hard constraints such as professor availability, student group conflicts, room capacity, room features, room availability, and campus matching.

The final system uses a multi-stage algorithmic pipeline:

1. Greedy baseline scheduling
2. Conflict graph construction
3. Welsh-Powell graph coloring
4. Dynamic programming room optimisation
5. Backtracking repair

The final repaired schedule successfully assigns all 12 classes in the main dataset with zero hard-constraint violations.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Project Aim](#project-aim)
- [Dataset](#dataset)
- [Project Structure](#project-structure)
- [File Descriptions](#file-descriptions)
- [Algorithm Pipeline](#algorithm-pipeline)
- [Results](#results)
- [Output Files](#output-files)
- [How to Run](#how-to-run)
- [Running with a Custom JSON File](#running-with-a-custom-json-file)
- [Running All Test Cases](#running-all-test-cases)
- [Important Commands](#important-commands)
- [Important Note About Imports](#important-note-about-imports)
- [Requirements](#requirements)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)
- [Academic Note](#academic-note)
- [Conclusion](#conclusion)

---

## Project Overview

University timetabling is a constrained optimisation problem. A valid timetable must assign each class to a time slot and room while avoiding clashes between professors, student groups, rooms, capacities, room features, and availability.

This project implements a modular algorithmic solution for the Campus Puzzle scheduling problem. Instead of relying on one single algorithm, the system combines several techniques. Each stage solves a different part of the scheduling problem.

The main idea is:

```text
Input JSON dataset
        ↓
Validate data
        ↓
Greedy baseline schedule
        ↓
Conflict graph + Welsh-Powell coloring
        ↓
Dynamic programming room optimisation
        ↓
Backtracking repair
        ↓
Final schedule + CSV outputs
```

---

## Project Aim

The aim of this project is to generate a valid university timetable while satisfying all hard constraints.

A valid schedule must ensure that:

- A professor is not teaching two classes at the same time.
- A student group is not attending two classes at the same time.
- A room is not double-booked.
- Room capacity is sufficient for the class size.
- Required room features such as `PC_LAB` or `MAC_LAB` are available.
- Professor availability is respected.
- Room availability is respected.
- Class campus and room campus match.

The project also attempts to reduce wasted room capacity.

Wasted capacity is calculated as:

```text
waste = room_capacity - class_students
```

---

## Dataset

The main dataset is stored in:

```text
data/processed/constraints.json
```

The provided Excel workbook was used as a reference for realistic room capacities, campus names, room types, and lecturer availability patterns.

However, the final scheduling dataset was manually structured as JSON because the algorithms require complete class-level information, including:

- Classes
- Time slots
- Professors
- Professor availability
- Rooms
- Room capacity
- Room features
- Room availability
- Student groups
- Required room features
- Scheduling rules

The main dataset contains:

| Entity | Count |
|---|---:|
| Time slots | 14 |
| Rooms | 10 |
| Professors | 6 |
| Student groups | 6 |
| Classes | 12 |

Additional test datasets are stored in:

```text
data/test_cases/
```

These test cases check different scheduling behaviours such as professor conflicts, student group conflicts, tight room capacity, and impossible room assignments.

---

## Project Structure

```text
campus-puzzle-scheduler/
│
├── data/
│   ├── processed/
│   │   └── constraints.json
│   │
│   └── test_cases/
│       ├── easy_case.json
│       ├── tight_rooms_case.json
│       ├── professor_conflict_case.json
│       ├── student_group_conflict_case.json
│       └── impossible_case.json
│
├── outputs/
│   ├── greedy_schedule.csv
│   ├── graph_coloring_schedule.csv
│   ├── dp_optimised_schedule.csv
│   ├── final_schedule.csv
│   └── results_summary.csv
│
├── scripts/
│   └── run_test_cases.py
│
├── src/
│   ├── __init__.py
│   ├── models.py
│   ├── parser.py
│   ├── check_data.py
│   ├── greedy_solver.py
│   ├── graph_engine.py
│   ├── optimizer.py
│   ├── backtracker.py
│   ├── evaluator.py
│   └── main.py
│
└── README.md
```

---

## File Descriptions

| File | Purpose |
|---|---|
| `src/models.py` | Defines dataclasses such as rooms, professors, student groups, classes, assignments, and schedule results |
| `src/parser.py` | Loads the JSON dataset and converts it into Python objects |
| `src/check_data.py` | Validates the dataset before running the scheduler |
| `src/greedy_solver.py` | Implements the greedy baseline scheduler |
| `src/graph_engine.py` | Builds the conflict graph and applies Welsh-Powell graph coloring |
| `src/optimizer.py` | Applies dynamic programming for room allocation |
| `src/backtracker.py` | Repairs unscheduled classes using recursive backtracking |
| `src/evaluator.py` | Checks schedule validity and calculates metrics |
| `src/main.py` | Runs the full scheduling pipeline |
| `scripts/run_test_cases.py` | Runs the scheduler on all test datasets |

---

## Algorithm Pipeline

### Stage 1: Greedy Baseline Scheduler

The greedy scheduler sorts classes by difficulty and places each class into the first valid slot-room combination.

Difficulty is calculated using:

```text
difficulty = students + 10 × student_group_count + 20 × required_feature_count + priority_score
```

Harder classes are scheduled earlier because they are more difficult to place.

The greedy stage checks:

- Professor availability
- Professor conflicts
- Student group conflicts
- Room capacity
- Room features
- Room availability
- Campus matching
- Room double-booking

The greedy baseline is fast and useful for comparison, but it is not guaranteed to be globally optimal.

---

### Stage 2: Conflict Graph and Welsh-Powell Coloring

The conflict graph represents scheduling clashes.

In the graph:

```text
node = class
edge = conflict between two classes
```

Two classes are connected if:

- They share the same professor.
- They share at least one student group.

Welsh-Powell graph coloring is then used to assign time slots.

In this project:

```text
color = time slot
```

Connected classes cannot receive the same color, meaning conflicting classes cannot be scheduled at the same time.

The main dataset conflict graph produced:

| Metric | Value |
|---|---:|
| Nodes | 12 |
| Edges | 14 |
| Maximum degree | 4 |

---

### Stage 3: Dynamic Programming Room Optimisation

After graph coloring assigns time slots, rooms are assigned using dynamic programming.

For each time slot, the algorithm collects all classes assigned to that slot and chooses rooms that minimise wasted capacity.

The DP state is:

```text
dp[i][j] = minimum waste for assigning the first i classes using the first j rooms
```

The recurrence is:

```text
dp[i][j] = min(skip room j, use room j for class i)
```

If a room is feasible:

```text
dp[i][j] = min(dp[i][j], dp[i-1][j-1] + room_capacity - class_students)
```

This stage respects:

- Room capacity
- Room features
- Campus matching
- Room availability

If not all classes in a time slot can be assigned rooms, the optimiser attempts to schedule the largest feasible subset.

---

### Stage 4: Backtracking Repair

Graph coloring avoids professor and student group conflicts, but it does not consider room availability. Therefore, some classes may receive time slots where no suitable room is available.

The backtracking repair stage attempts to place unscheduled classes into alternative valid slot-room combinations.

It checks:

- Professor availability
- Professor conflicts
- Student group conflicts
- Room availability
- Room capacity
- Room features
- Campus matching
- Room double-booking

The backtracking repair is best-effort. It repairs unscheduled classes without globally rearranging every class.

---

## Results

The main dataset produced the following results:

| Stage | Scheduled Classes | Room Conflicts | Professor Conflicts | Student Group Conflicts | Total Waste |
|---|---:|---:|---:|---:|---:|
| Greedy Baseline | 12 | 0 | 0 | 0 | 43 |
| Graph Coloring + DP Room Optimisation | 10 | 0 | 0 | 0 | 43 |
| Backtracking Final Repair | 12 | 0 | 0 | 0 | 43 |

The graph-coloring and DP stage left two classes unscheduled:

| Class | Reason | Final Repair |
|---|---|---|
| `ML202` | Required `POT-MACPOOL`, but was assigned to an unavailable morning slot | Thursday 13:00–16:00, `POT-MACPOOL` |
| `MBA501` | Required a 60-seat Potsdam room, but was assigned to an unavailable evening slot | Tuesday 09:00–12:00, `POT-AUDITORIUM` |

The final repaired schedule successfully placed all 12 classes with:

- 0 room conflicts
- 0 professor conflicts
- 0 student group conflicts
- 0 capacity violations
- 0 feature violations
- 0 campus violations
- 0 professor availability violations
- 0 room availability violations

---

## Output Files

After running the scheduler, the following files are generated in the `outputs/` folder:

| Output File | Description |
|---|---|
| `greedy_schedule.csv` | Schedule produced by the greedy baseline |
| `graph_coloring_schedule.csv` | Time-slot assignment from Welsh-Powell graph coloring |
| `dp_optimised_schedule.csv` | Room allocation after dynamic programming |
| `final_schedule.csv` | Final repaired schedule after backtracking |
| `results_summary.csv` | Comparison metrics for all stages |

---

## How to Run

Run all commands from the project root folder:

```text
campus-puzzle-scheduler/
```

### Step 1: Validate the Dataset

```bash
python -m src.check_data
```

Expected output:

```text
=== DATASET SUMMARY ===
Time slots: 14
Rooms: 10
Professors: 6
Student groups: 6
Classes: 12

=== VALIDATION ===
Dataset is valid and ready for scheduling.
```

### Step 2: Run the Full Scheduler

```bash
python -m src.main
```

This executes the complete algorithmic pipeline:

1. Greedy baseline schedule
2. Conflict graph construction
3. Welsh-Powell time-slot coloring
4. Dynamic programming room optimisation
5. Backtracking repair
6. Final evaluation
7. CSV output generation

---

## Running with a Custom JSON File

You can run the scheduler with any JSON dataset that follows the same structure.

Example:

```bash
python -m src.main --data data/test_cases/easy_case.json
```

You can also specify custom output paths.

For Windows PowerShell:

```powershell
python -m src.main `
  --data data/test_cases/easy_case.json `
  --greedy-output outputs/easy_greedy.csv `
  --graph-output outputs/easy_graph.csv `
  --dp-output outputs/easy_dp.csv `
  --final-output outputs/easy_final.csv
```

For Windows Command Prompt:

```cmd
python -m src.main ^
  --data data/test_cases/easy_case.json ^
  --greedy-output outputs/easy_greedy.csv ^
  --graph-output outputs/easy_graph.csv ^
  --dp-output outputs/easy_dp.csv ^
  --final-output outputs/easy_final.csv
```

For macOS/Linux:

```bash
python -m src.main \
  --data data/test_cases/easy_case.json \
  --greedy-output outputs/easy_greedy.csv \
  --graph-output outputs/easy_graph.csv \
  --dp-output outputs/easy_dp.csv \
  --final-output outputs/easy_final.csv
```

---

## Running All Test Cases

To run all test cases:

```bash
python scripts/run_test_cases.py
```

The test cases are:

| Test Case | Purpose | Expected Behaviour |
|---|---|---|
| `easy_case.json` | Simple valid dataset | All classes scheduled |
| `tight_rooms_case.json` | Limited room capacity | No capacity violations |
| `professor_conflict_case.json` | Same professor teaches multiple classes | No professor overlaps |
| `student_group_conflict_case.json` | Shared student group dependency | No student group overlaps |
| `impossible_case.json` | Oversized class that cannot fit any room | Class remains unscheduled |

---

## Important Commands

Validate dataset:

```bash
python -m src.check_data
```

Run main scheduler:

```bash
python -m src.main
```

Run with custom JSON file:

```bash
python -m src.main --data data/test_cases/easy_case.json
```

Run all test cases:

```bash
python scripts/run_test_cases.py
```

List generated outputs on Windows PowerShell:

```powershell
dir outputs
```

---

## Important Note About Imports

This project uses package-style imports:

```python
from src.evaluator import evaluate_schedule
```

Because of this, the main file should be run using:

```bash
python -m src.main
```

instead of:

```bash
python src/main.py
```

Running `python src/main.py` may cause:

```text
ModuleNotFoundError: No module named 'src'
```

---

## Requirements

This project uses only the Python standard library.

No external Python packages are required.

Recommended Python version:

```text
Python 3.10+
```

---

## Limitations

The system is a best-effort scheduling pipeline, not a globally optimal solver.

Current limitations:

- The dataset is synthetic.
- The system assumes fixed class durations.
- Each class uses one room.
- Backtracking repairs only unscheduled classes.
- The scheduler does not globally rearrange every assignment.
- Soft constraints such as lecturer preferences and travel time are not deeply optimised.
- No graphical user interface is included.

---

## Future Improvements

Possible future improvements include:

- Full global backtracking search
- Larger real-world dataset testing
- Integration of room feasibility into graph coloring
- Better soft-constraint optimisation
- Professor workload balancing
- Student travel-time minimisation
- Graphical user interface
- Web-based timetable viewer

---

## Academic Note

This project was developed for academic purposes as part of the M603 Advanced Algorithms assessment.

The implementation demonstrates how multiple algorithmic techniques can be combined to solve a university timetabling problem.

---

## Conclusion

Campus Puzzle Scheduler demonstrates how multiple algorithms can be combined to solve a university timetabling problem.

The final pipeline shows that:

- Greedy scheduling gives a fast baseline.
- Conflict graphs identify professor and student group clashes.
- Welsh-Powell coloring assigns conflict-safe time slots.
- Dynamic programming optimises room allocation.
- Backtracking repairs classes that fail due to room-slot infeasibility.

The final repaired schedule places all 12 classes with zero hard-constraint violations and total room-capacity waste of 43 seats.
