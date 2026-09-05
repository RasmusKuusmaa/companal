"""The curriculum registry: every topic and every stage, in roadmap order.

`TOPICS` and `COURSES` together are the whole syllabus, and the seed loader
treats them as authoritative - anything in the database whose slug isn't
found here is removed. Adding a stage means writing its module and appending
it to `COURSES`; that list *is* the roadmap's order.

`COURSES` is empty until the stage shells land (Phase J). Seeding an empty
list of courses is a legitimate no-op, not an error, so the loader and its
tests work from here on.
"""

from app.domains.learning.curriculum import stage0, stage1, stage2, stage3, stage4
from app.domains.learning.curriculum.definitions import (
    CourseDef,
    LessonDef,
    StepDef,
    TopicDef,
)
from app.domains.learning.curriculum.topics import TOPICS

__all__ = ["CourseDef", "LessonDef", "StepDef", "TopicDef", "TOPICS", "COURSES"]

COURSES: list[CourseDef] = [
    stage0.COURSE,
    stage1.COURSE,
    stage2.COURSE,
    stage3.COURSE,
    stage4.COURSE,
]
