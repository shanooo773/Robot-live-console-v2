from pathlib import Path

from services.learning_service import LearningService


class DummyDB:
    def __init__(self):
        self.progress = {}

    def get_learning_progress(self, user_id, course_id):
        lesson_status = self.progress.get((user_id, course_id), {})
        return {
            "course_id": course_id,
            "lesson_status": lesson_status,
            "completed_lessons": [lesson_id for lesson_id, done in lesson_status.items() if done],
            "updated_at": None,
        }

    def set_learning_progress(self, user_id, course_id, lesson_id, completed):
        key = (user_id, course_id)
        if key not in self.progress:
            self.progress[key] = {}
        self.progress[key][lesson_id] = bool(completed)
        return True


def _write(path: Path, text: str):
    path.write_text(text, encoding="utf-8")


def test_learning_service_returns_eight_lessons_when_intro_exists(tmp_path):
    course_dir = tmp_path / "ROS2 Foundations"
    course_dir.mkdir()
    for idx in range(0, 9):
        _write(course_dir / f"{idx}_Lesson_{idx}.md", f"# Lesson {idx}\n\nContent {idx}")

    service = LearningService(db_manager=DummyDB(), course_directory=course_dir)
    lessons = service.list_lessons()

    assert len(lessons) == 8
    assert all(lesson["filename"].startswith(tuple(str(n) for n in range(1, 9))) for lesson in lessons)


def test_learning_service_progress_roundtrip(tmp_path):
    course_dir = tmp_path / "ROS2 Foundations"
    course_dir.mkdir()
    _write(course_dir / "1_Alpha.md", "# Alpha")

    db = DummyDB()
    service = LearningService(db_manager=db, course_directory=course_dir)
    lesson = service.list_lessons()[0]

    progress = service.set_progress(
        user_id=5,
        course_id="ros2-foundation",
        lesson_id=lesson["id"],
        completed=True,
    )

    assert lesson["id"] in progress["completed_lessons"]
    assert progress["lesson_status"][lesson["id"]] is True
