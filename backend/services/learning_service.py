import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class LearningService:
    COURSE_ID = "ros2-foundation"
    COURSE_TITLE = "ROS2 Foundation"
    MAX_LESSONS = 9
    FALLBACK_SORT_ORDER = 10_000

    def __init__(self, db_manager, course_directory: Path):
        self.db = db_manager
        self.course_directory = course_directory

    @staticmethod
    def resolve_default_course_directory(repo_root: Path) -> Path:
        candidates = [repo_root / "ROS2 Foundation", repo_root / "ROS2 Foundations"]
        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return candidate
        return candidates[-1]

    @staticmethod
    def _lesson_order_from_name(stem: str) -> Optional[int]:
        match = re.match(r"^\s*(\d+)", stem)
        if not match:
            return None
        return int(match.group(1))

    @staticmethod
    def _lesson_id_from_stem(stem: str) -> str:
        lesson_id = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
        return lesson_id or f"lesson-{abs(hash(stem))}"

    @staticmethod
    def _lesson_title_from_stem(stem: str) -> str:
        title = re.sub(r"^\s*\d+\s*[_\-]?\s*", "", stem).strip()
        title = title.replace("_", " ")
        return title or stem

    def _discover_lesson_files(self) -> List[Path]:
        files = [path for path in self.course_directory.glob("*.md") if path.is_file()]

        def sort_key(path: Path):
            lesson_order = self._lesson_order_from_name(path.stem)
            return (
                lesson_order if lesson_order is not None else self.FALLBACK_SORT_ORDER,
                path.name.lower(),
            )

        files.sort(key=sort_key)

        numbered_non_zero = [p for p in files if self._lesson_order_from_name(p.stem) is not None]
        if len(numbered_non_zero) >= self.MAX_LESSONS:
            return numbered_non_zero[: self.MAX_LESSONS]
        return files[: self.MAX_LESSONS]

    def list_lessons(self) -> List[Dict[str, Any]]:
        lessons: List[Dict[str, Any]] = []
        for index, file_path in enumerate(self._discover_lesson_files(), start=1):
            stem = file_path.stem
            lesson_order = self._lesson_order_from_name(stem)
            lessons.append(
                {
                    "id": self._lesson_id_from_stem(stem),
                    "title": self._lesson_title_from_stem(stem),
                    "order": lesson_order if lesson_order is not None else index,
                    "filename": file_path.name,
                }
            )
        return lessons

    def get_lesson(self, lesson_id: str) -> Dict[str, Any]:
        for file_path in self._discover_lesson_files():
            stem = file_path.stem
            if self._lesson_id_from_stem(stem) != lesson_id:
                continue
            return {
                "id": lesson_id,
                "title": self._lesson_title_from_stem(stem),
                "content": file_path.read_text(encoding="utf-8"),
                "filename": file_path.name,
            }
        raise KeyError(f"Lesson '{lesson_id}' not found")

    def get_progress(self, user_id: int, course_id: str) -> Dict[str, Any]:
        progress = self.db.get_learning_progress(user_id, course_id)
        progress.setdefault("lesson_status", {})
        progress.setdefault("completed_lessons", [])
        return progress

    def set_progress(self, user_id: int, course_id: str, lesson_id: str, completed: bool) -> Dict[str, Any]:
        self.db.set_learning_progress(user_id, course_id, lesson_id, completed)
        return self.get_progress(user_id, course_id)
