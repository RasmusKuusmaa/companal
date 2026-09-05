"""Stage 0 - Fundamentals: notation, rhythm, scales and intervals.

Lessons land one at a time in their own commits; this module starts as the
shell `seed stage 0 fundamentals` creates and grows as each lands.
"""

from app.domains.learning.curriculum.definitions import CourseDef

COURSE = CourseDef(
    slug="fundamentals",
    title="Fundamentals",
    description=(
        "Reading music and the raw material it's built from: the staff, rhythm, scales, "
        "intervals and modes."
    ),
    level="beginner",
    lessons=[],
)
