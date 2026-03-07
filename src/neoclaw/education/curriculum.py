"""Curriculum and lesson definitions for claw machine Python education."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Exercise:
    """A single exercise."""
    id: str
    title: str
    description: str
    starter_code: str
    expected_concepts: list[str] = field(default_factory=list)
    difficulty: int = 1  # 1-5


@dataclass
class Lesson:
    """A lesson containing exercises."""
    id: int
    title: str
    description: str
    exercises: list[Exercise] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)


CLAW_LESSONS = [
    Lesson(
        id=1,
        title="Hello Claw!",
        description="Learn to import modules and call functions to move the claw",
        concepts=["import", "function_call"],
        exercises=[
            Exercise(
                id="c1_l1_e1",
                title="First Move",
                description="Import the claw module and move the claw left",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "# Move the claw to the left for 1 second\n"
                    "move_left(duration=___)\n"
                ),
                expected_concepts=["import", "function_call"],
                difficulty=1,
            ),
            Exercise(
                id="c1_l1_e2",
                title="Grab Something!",
                description="Move down and activate the magnet",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "# Step 1: Move down to reach the object\n"
                    "move_down(duration=2.0)\n"
                    "\n"
                    "# Step 2: Activate the magnet to grab\n"
                    "___\n"
                ),
                expected_concepts=["function_call"],
                difficulty=1,
            ),
        ],
    ),
    Lesson(
        id=2,
        title="Variables & Speed",
        description="Use variables to control speed and duration",
        concepts=["variables", "float", "PWM"],
        exercises=[
            Exercise(
                id="c1_l2_e1",
                title="Speed Control",
                description="Use a variable to set the claw speed",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "# Create a speed variable (0.0 to 1.0)\n"
                    "speed = ___\n"
                    "\n"
                    "# Move left at the chosen speed\n"
                    "move_left(duration=1.0, speed=speed)\n"
                ),
                expected_concepts=["variables", "float"],
                difficulty=2,
            ),
            Exercise(
                id="c1_l2_e2",
                title="Slow and Fast",
                description="Move at different speeds to see the difference",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "slow = 0.3\n"
                    "fast = ___\n"
                    "\n"
                    "# Move slowly to position\n"
                    "move_right(duration=2.0, speed=slow)\n"
                    "\n"
                    "# Move fast back\n"
                    "move_left(duration=1.0, speed=fast)\n"
                ),
                expected_concepts=["variables", "float", "comparison"],
                difficulty=2,
            ),
        ],
    ),
    Lesson(
        id=3,
        title="Loops for Motion",
        description="Use for loops to create repeated motions",
        concepts=["for_loop", "range"],
        exercises=[
            Exercise(
                id="c1_l3_e1",
                title="Zigzag Pattern",
                description="Use a loop to make the claw zigzag",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "# Make the claw zigzag 3 times\n"
                    "for i in range(___):\n"
                    "    move_right(duration=0.5)\n"
                    "    move_left(duration=0.5)\n"
                ),
                expected_concepts=["for_loop", "range"],
                difficulty=2,
            ),
            Exercise(
                id="c1_l3_e2",
                title="Increasing Speed",
                description="Loop with increasing speed each iteration",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "# Move right 5 times, each time faster\n"
                    "for i in range(5):\n"
                    "    speed = (i + 1) / ___\n"
                    "    move_right(duration=0.3, speed=speed)\n"
                    "    print(f'Speed: {speed}')\n"
                ),
                expected_concepts=["for_loop", "math", "f-string"],
                difficulty=3,
            ),
        ],
    ),
    Lesson(
        id=4,
        title="Conditionals & Sensors",
        description="Use if/else to respond to sensor data",
        concepts=["if_else", "boolean", "comparison"],
        exercises=[
            Exercise(
                id="c1_l4_e1",
                title="Smart Movement",
                description="Check state before moving",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "state = get_state()\n"
                    "\n"
                    "# Only grab if magnet is not already active\n"
                    "if not state['magnet']:\n"
                    "    ___\n"
                    "else:\n"
                    "    print('Magnet already active!')\n"
                ),
                expected_concepts=["if_else", "dict_access", "boolean"],
                difficulty=3,
            ),
        ],
    ),
    Lesson(
        id=5,
        title="Custom Functions",
        description="Create reusable functions for claw operations",
        concepts=["def", "parameters", "return"],
        exercises=[
            Exercise(
                id="c1_l5_e1",
                title="Move Function",
                description="Create a function that moves to a position",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "def move_to_position(x_duration, y_duration):\n"
                    "    '''Move claw to a position using duration.'''\n"
                    "    if x_duration > 0:\n"
                    "        move_right(duration=x_duration)\n"
                    "    elif x_duration < 0:\n"
                    "        move_left(duration=___)\n"
                    "    \n"
                    "    if y_duration > 0:\n"
                    "        move_forward(duration=y_duration)\n"
                    "    elif y_duration < 0:\n"
                    "        move_backward(duration=abs(y_duration))\n"
                    "\n"
                    "# Test: move right 1s, forward 0.5s\n"
                    "move_to_position(1.0, 0.5)\n"
                ),
                expected_concepts=["def", "parameters", "abs"],
                difficulty=3,
            ),
        ],
    ),
    Lesson(
        id=6,
        title="Full Grab Sequence",
        description="Build a complete grab-and-retrieve automation",
        concepts=["state_machine", "error_handling", "functions"],
        exercises=[
            Exercise(
                id="c1_l6_e1",
                title="Auto Grab",
                description="Write a complete sequence: position → lower → grab → lift → return",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "def auto_grab(x_time, y_time):\n"
                    "    '''Automated grab sequence.'''\n"
                    "    # Step 1: Move to position\n"
                    "    move_right(duration=x_time)\n"
                    "    move_forward(duration=y_time)\n"
                    "    \n"
                    "    # Step 2: Lower the claw\n"
                    "    ___\n"
                    "    \n"
                    "    # Step 3: Grab\n"
                    "    grab()\n"
                    "    \n"
                    "    # Step 4: Lift\n"
                    "    move_up(duration=2.0)\n"
                    "    \n"
                    "    # Step 5: Return to start\n"
                    "    move_backward(duration=y_time)\n"
                    "    move_left(duration=x_time)\n"
                    "    \n"
                    "    # Step 6: Release\n"
                    "    ___\n"
                    "\n"
                    "# Try grabbing at position (1.5s right, 1.0s forward)\n"
                    "auto_grab(1.5, 1.0)\n"
                ),
                expected_concepts=["state_machine", "functions", "sequence"],
                difficulty=4,
            ),
        ],
    ),
]


def get_lessons(phase: int = 1) -> list[Lesson]:
    """Get lessons for the given phase."""
    if phase == 1:
        return CLAW_LESSONS
    return []


def get_exercise(exercise_id: str) -> Exercise | None:
    """Find an exercise by ID."""
    for lesson in CLAW_LESSONS:
        for exercise in lesson.exercises:
            if exercise.id == exercise_id:
                return exercise
    return None


def get_lesson(lesson_id: int) -> Lesson | None:
    """Find a lesson by ID."""
    for lesson in CLAW_LESSONS:
        if lesson.id == lesson_id:
            return lesson
    return None
