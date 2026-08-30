"""Thang gợi ý 4 cấp — đẩy nhẹ, chỉ đường, nói thẳng, rồi mới tới lời giải."""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class HintLevel(IntEnum):
    NUDGE = 1       # Gentle direction
    GUIDANCE = 2    # More specific
    EXPLICIT = 3    # Clear instruction
    SOLUTION = 4    # Full solution


@dataclass
class Hint:
    level: HintLevel
    message: str


# Hints per exercise
# Thang gợi ý 4 cấp cho từng bài tập: đẩy nhẹ → chỉ đường → nói thẳng → lời giải.
# Cấp 4 là mã chạy được thật trên robot; test_curriculum_contract kiểm tra điều đó.
_HINTS: dict[str, list[Hint]] = {
    "c1_l1_e1": [
        Hint(HintLevel.NUDGE, "Em muốn robot đi trong bao lâu? Số giây viết vào đâu nhỉ?"),
        Hint(HintLevel.GUIDANCE, "duration nhận một số, tính bằng giây. 1 giây thì viết 1.0."),
        Hint(HintLevel.EXPLICIT, "Thay ___ bằng 1.0 để robot đi tới trong 1 giây."),
        Hint(HintLevel.SOLUTION, "forward(duration=1.0)"),
    ],
    "c1_l1_e2": [
        Hint(HintLevel.NUDGE, "Tay đã hạ xuống rồi. Giờ cần làm gì để giữ được món đồ?"),
        Hint(HintLevel.GUIDANCE, "Có một hàm đóng kẹp lại — tên nó nghĩa là *nắm chặt*."),
        Hint(HintLevel.EXPLICIT, "Thay ___ bằng grip() để đóng kẹp."),
        Hint(HintLevel.SOLUTION, "grip()"),
    ],
    "c1_l2_e1": [
        Hint(HintLevel.NUDGE, "Tốc độ là một con số. Số 0 là đứng yên, số 100 là hết sức."),
        Hint(HintLevel.GUIDANCE, "Thử một số ở khoảng giữa, ví dụ một nửa sức."),
        Hint(HintLevel.EXPLICIT, "Thay ___ bằng 50 (hoặc số nào em thích từ 0 đến 100)."),
        Hint(HintLevel.SOLUTION, "toc_do = 50"),
    ],
    "c1_l2_e2": [
        Hint(HintLevel.NUDGE, "cham đang là 30. Muốn nhanh hơn thì số phải thế nào?"),
        Hint(HintLevel.GUIDANCE, "Chọn một số lớn hơn 30 nhưng đừng quá 100."),
        Hint(HintLevel.EXPLICIT, "Thay ___ bằng 80 để thấy rõ sự khác nhau."),
        Hint(HintLevel.SOLUTION, "nhanh = 80"),
    ],
    "c1_l3_e1": [
        Hint(HintLevel.NUDGE, "Đề bài muốn zigzag mấy lần?"),
        Hint(HintLevel.GUIDANCE, "range(n) sẽ lặp đúng n lần."),
        Hint(HintLevel.EXPLICIT, "Thay ___ bằng 3."),
        Hint(HintLevel.SOLUTION, "for i in range(3):\n    strafe_right(duration=0.5)\n    strafe_left(duration=0.5)"),
    ],
    "c1_l3_e2": [
        Hint(HintLevel.NUDGE, "Vòng đầu i = 0, vòng cuối i = 4. Em muốn tốc độ cuối cùng là bao nhiêu?"),
        Hint(HintLevel.GUIDANCE, "(i + 1) chạy từ 1 đến 5. Nhân với số nào thì vòng cuối ra 100?"),
        Hint(HintLevel.EXPLICIT, "Thay ___ bằng 20 — vòng cuối sẽ là 5 * 20 = 100."),
        Hint(HintLevel.SOLUTION, "toc_do = (i + 1) * 20"),
    ],
    "c1_l4_e1": [
        Hint(HintLevel.NUDGE, "Nếu tay đang trống thì việc cần làm là gì?"),
        Hint(HintLevel.GUIDANCE, "Cùng hàm em đã dùng ở bài 1 để đóng kẹp."),
        Hint(HintLevel.EXPLICIT, "Thay ___ bằng grip()."),
        Hint(HintLevel.SOLUTION, "if not trang_thai['gripper_holding']:\n    grip()"),
    ],
    "c1_l5_e1": [
        Hint(HintLevel.NUDGE, "giay_ngang đang là số âm. duration mà âm thì robot hiểu sao được?"),
        Hint(HintLevel.GUIDANCE, "Có một hàm biến số âm thành số dương — em đã thấy nó ở dòng dưới."),
        Hint(HintLevel.EXPLICIT, "Thay ___ bằng abs(giay_ngang)."),
        Hint(HintLevel.SOLUTION, "strafe_left(duration=abs(giay_ngang))"),
    ],
    "c1_l6_e1": [
        Hint(HintLevel.NUDGE, "Hạ tay, gắp, rồi nâng lên — cả ba việc đó có một hàm làm sẵn."),
        Hint(HintLevel.GUIDANCE, "pick_up() làm trọn bước 2; put_down() làm trọn bước 4."),
        Hint(HintLevel.EXPLICIT, "Thay ___ thứ nhất bằng pick_up(), ___ thứ hai bằng put_down()."),
        Hint(HintLevel.SOLUTION, "pick_up()\n# ...\nput_down()"),
    ],
}

def get_hints(exercise_id: str) -> list[Hint]:
    """The full hint ladder for an exercise, level 1 → 4.

    HintManager hands them out one at a time as a student asks; this returns the
    whole ladder for callers that need to inspect it (curriculum checks, an
    author reviewing content, the education API).
    """
    return list(_HINTS.get(exercise_id, []))


class HintManager:
    """Manages hint progression per student per exercise."""

    def __init__(self):
        self._hint_indices: dict[str, int] = {}  # exercise_id → current level

    def get_hint(self, exercise_id: str) -> Hint | None:
        """Get the next hint for an exercise, advancing the level."""
        hints = _HINTS.get(exercise_id)
        if not hints:
            return None

        idx = self._hint_indices.get(exercise_id, 0)
        if idx >= len(hints):
            return hints[-1]  # Return solution repeatedly

        hint = hints[idx]
        self._hint_indices[exercise_id] = idx + 1
        return hint

    def reset(self, exercise_id: str) -> None:
        """Reset hint progression for an exercise."""
        self._hint_indices.pop(exercise_id, None)

    def reset_all(self) -> None:
        """Reset all hint progressions."""
        self._hint_indices.clear()

    def current_level(self, exercise_id: str) -> HintLevel:
        """Get current hint level for an exercise."""
        idx = self._hint_indices.get(exercise_id, 0)
        hints = _HINTS.get(exercise_id, [])
        if not hints or idx >= len(hints):
            return HintLevel.SOLUTION
        return hints[idx].level
