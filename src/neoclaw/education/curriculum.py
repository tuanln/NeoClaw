"""Bộ bài học Python cho ClawBot.

Mỗi bài dạy một khái niệm Python bằng chính chuyển động của robot: đi tới, đi
ngang, xoay, gắp. Tên hàm trong starter_code phải là hàm mà sandbox học sinh
thật sự cung cấp (neoclaw.agent.code_executor.generate_claw_wrapper_code) —
tests/test_education/test_curriculum_contract.py giữ cho hai bên không lệch
nhau như bộ bài cũ, vốn viết cho máy gắp thùng kính trong khi sản phẩm là robot.
"""
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
        title="Chào ClawBot!",
        description="Gọi hàm để robot đi và gắp — dòng lệnh đầu tiên của em",
        concepts=["import", "function_call"],
        exercises=[
            Exercise(
                id="c1_l1_e1",
                title="Bước đi đầu tiên",
                description="Cho robot đi tới trong 1 giây",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "# Cho robot đi tới trong 1 giây\n"
                    "forward(duration=___)\n"
                ),
                expected_concepts=["import", "function_call"],
                difficulty=1,
            ),
            Exercise(
                id="c1_l1_e2",
                title="Gắp một món đồ",
                description="Hạ tay xuống rồi đóng kẹp lại",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "# Bước 1: hạ tay xuống chỗ món đồ\n"
                    "arm_pose('reach_down')\n"
                    "\n"
                    "# Bước 2: đóng kẹp để giữ món đồ\n"
                    "___\n"
                ),
                expected_concepts=["function_call"],
                difficulty=1,
            ),
        ],
    ),
    Lesson(
        id=2,
        title="Biến và tốc độ",
        description="Dùng biến để đổi tốc độ của xe, từ 0 đến 100",
        concepts=["variables", "float"],
        exercises=[
            Exercise(
                id="c1_l2_e1",
                title="Chỉnh tốc độ",
                description="Đặt tốc độ vào một biến rồi dùng lại",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "# Tốc độ nhận số từ 0 đến 100\n"
                    "toc_do = ___\n"
                    "\n"
                    "# Đi tới với tốc độ vừa đặt\n"
                    "forward(duration=1.0, speed=toc_do)\n"
                ),
                expected_concepts=["variables", "float"],
                difficulty=2,
            ),
            Exercise(
                id="c1_l2_e2",
                title="Chậm và nhanh",
                description="So sánh hai tốc độ bằng chính mắt em",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "cham = 30\n"
                    "nhanh = ___\n"
                    "\n"
                    "# Đi ngang sang phải thật chậm\n"
                    "strafe_right(duration=2.0, speed=cham)\n"
                    "\n"
                    "# Rồi đi ngang về bên trái thật nhanh\n"
                    "strafe_left(duration=1.0, speed=nhanh)\n"
                ),
                expected_concepts=["variables", "float"],
                difficulty=2,
            ),
        ],
    ),
    Lesson(
        id=3,
        title="Vòng lặp cho chuyển động",
        description="Lặp lại một chuyển động mà không phải chép đi chép lại",
        concepts=["for_loop", "range"],
        exercises=[
            Exercise(
                id="c1_l3_e1",
                title="Đường zigzag",
                description="Dùng vòng lặp cho xe đi ngang qua lại",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "# Cho xe zigzag 3 lần\n"
                    "for i in range(___):\n"
                    "    strafe_right(duration=0.5)\n"
                    "    strafe_left(duration=0.5)\n"
                ),
                expected_concepts=["for_loop", "range"],
                difficulty=2,
            ),
            Exercise(
                id="c1_l3_e2",
                title="Mỗi vòng một nhanh hơn",
                description="Tính tốc độ mới trong mỗi vòng lặp",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "# Xoay 5 lần, lần sau nhanh hơn lần trước\n"
                    "for i in range(5):\n"
                    "    toc_do = (i + 1) * ___\n"
                    "    turn_right(duration=0.3, speed=toc_do)\n"
                    "    print(f'Tốc độ: {toc_do}')\n"
                ),
                expected_concepts=["for_loop", "range", "f-string"],
                difficulty=3,
            ),
        ],
    ),
    Lesson(
        id=4,
        title="Hỏi robot rồi mới quyết định",
        description="Đọc trạng thái robot và dùng if/else để chọn việc cần làm",
        concepts=["if_else", "boolean", "dict_access"],
        exercises=[
            Exercise(
                id="c1_l4_e1",
                title="Đừng gắp hai lần",
                description="Chỉ đóng kẹp khi tay đang trống",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "trang_thai = get_state()\n"
                    "\n"
                    "# Chỉ gắp khi tay chưa giữ gì cả\n"
                    "if not trang_thai['gripper_holding']:\n"
                    "    ___\n"
                    "else:\n"
                    "    print('Tay đang giữ đồ rồi!')\n"
                ),
                expected_concepts=["if_else", "dict_access", "boolean"],
                difficulty=3,
            ),
        ],
    ),
    Lesson(
        id=5,
        title="Tự viết hàm của em",
        description="Gói một chuỗi việc thành một cái tên, rồi gọi lại tuỳ thích",
        concepts=["def", "parameters"],
        exercises=[
            Exercise(
                id="c1_l5_e1",
                title="Hàm đi tới một chỗ",
                description="Viết hàm nhận hai khoảng thời gian rồi đưa xe tới đó",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "def di_toi_cho(giay_ngang, giay_thang):\n"
                    "    # Đưa xe đi ngang rồi đi thẳng\n"
                    "    if giay_ngang > 0:\n"
                    "        strafe_right(duration=giay_ngang)\n"
                    "    elif giay_ngang < 0:\n"
                    "        strafe_left(duration=___)\n"
                    "\n"
                    "    if giay_thang > 0:\n"
                    "        forward(duration=giay_thang)\n"
                    "    elif giay_thang < 0:\n"
                    "        backward(duration=abs(giay_thang))\n"
                    "\n"
                    "# Thử: sang phải 1 giây, đi tới 0.5 giây\n"
                    "di_toi_cho(1.0, 0.5)\n"
                ),
                expected_concepts=["def", "parameters", "abs"],
                difficulty=3,
            ),
        ],
    ),
    Lesson(
        id=6,
        title="Chuyến gắp hoàn chỉnh",
        description="Ghép mọi thứ đã học thành một chuyến đi lấy đồ rồi mang về",
        concepts=["def", "function_call"],
        exercises=[
            Exercise(
                id="c1_l6_e1",
                title="Tự động lấy đồ",
                description="Đi tới chỗ đồ, gắp, mang về, rồi đặt xuống",
                starter_code=(
                    "from claw import *\n"
                    "\n"
                    "def di_lay_do(giay_ngang, giay_thang):\n"
                    "    # Bước 1: đi tới chỗ món đồ\n"
                    "    strafe_right(duration=giay_ngang)\n"
                    "    forward(duration=giay_thang)\n"
                    "\n"
                    "    # Bước 2: hạ tay, gắp, rồi nâng lên\n"
                    "    ___\n"
                    "\n"
                    "    # Bước 3: mang về chỗ cũ\n"
                    "    backward(duration=giay_thang)\n"
                    "    strafe_left(duration=giay_ngang)\n"
                    "\n"
                    "    # Bước 4: đặt món đồ xuống\n"
                    "    ___\n"
                    "\n"
                    "# Thử: sang phải 1.5 giây, đi tới 1 giây\n"
                    "di_lay_do(1.5, 1.0)\n"
                ),
                expected_concepts=["def", "parameters", "function_call"],
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
