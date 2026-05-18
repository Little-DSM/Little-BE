from dataclasses import dataclass


@dataclass(frozen=True)
class MentorQueryDTO:
    mentor_id: int
