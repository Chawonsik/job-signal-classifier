from dataclasses import dataclass, field


@dataclass
class Posting:
    site: str
    company: str
    title: str
    url: str
    career_text: str = ""
    deadline: str | None = None
    is_rolling: bool = False
    is_closed: bool = False
    tags: list[str] = field(default_factory=list)
    requirement_text: str = ""
