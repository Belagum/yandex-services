from dataclasses import dataclass, field

@dataclass(slots=True)
class CardConfig:
    name: str
    executor: str
    city: str
    time_in_card: int
    repeat_count: int
    click_phone: bool
    use_proxy: bool
    proxy_idx: list[int] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    @classmethod
    def from_raw(cls, name: str, raw: dict):
        s = raw.get("settings", {})
        return cls(
            name,
            s.get("name", ""),
            s.get("city", ""),
            max(45, int(s.get("time_in_card", 45))),
            max(1, int(s.get("repeat_count", 1))),
            bool(s.get("click_phone", False)),
            bool(s.get("use_proxy", False)),
            s.get("proxy_idx", []),
            s.get("keywords", [])
        )
