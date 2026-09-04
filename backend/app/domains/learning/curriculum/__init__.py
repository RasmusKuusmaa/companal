"""The curriculum registry: every topic and every stage, in roadmap order.

`TOPICS` and `COURSES` together are the whole syllabus, and the seed loader
treats them as authoritative - anything in the database whose slug isn't
found here is removed. Adding a stage means writing its module and appending
it to `COURSES`; that list *is* the roadmap's order.

Both lists are empty until the content lands in Phase J. Seeding an empty
curriculum is a legitimate no-op, not an error, so the loader and its tests
work from here on.
"""

from app.domains.learning.curriculum.definitions import (
    CourseDef,
    LessonDef,
    StepDef,
    TopicDef,
)

__all__ = ["CourseDef", "LessonDef", "StepDef", "TopicDef", "TOPICS", "COURSES"]

TOPICS: list[TopicDef] = []

COURSES: list[CourseDef] = []
