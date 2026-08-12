from __future__ import annotations

import dataclasses
import enum
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = 1


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def jsonable(obj: Any) -> Any:
    """Convert arbitrary Python objects into JSON-safe structures."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, enum.Enum):
        return obj.value

    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [jsonable(x) for x in obj]

    if isinstance(obj, (set, frozenset)):
        try:
            return [jsonable(x) for x in sorted(obj)]
        except TypeError:
            return [jsonable(x) for x in obj]

    if dataclasses.is_dataclass(obj):
        return jsonable(dataclasses.asdict(obj))

    return str(obj)


@dataclass(frozen=True)
class LabEvent:
    step: int
    source: str
    kind: str
    path: str
    before: Dict[str, Any]
    after: Dict[str, Any]
    meta: Dict[str, Any]
    t: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "source": self.source,
            "kind": self.kind,
            "path": self.path,
            "before": self.before,
            "after": self.after,
            "meta": self.meta,
            "t": self.t,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LabEvent":
        return cls(
            step=int(d.get("step", 0)),
            source=str(d.get("source", "")),
            kind=str(d.get("kind", "")),
            path=str(d.get("path", "")),
            before=dict(d.get("before", {})),
            after=dict(d.get("after", {})),
            meta=dict(d.get("meta", {})),
            t=d.get("t"),
        )


@dataclass
class LabTrace:
    source: str
    title: str
    schema: int = SCHEMA_VERSION
    created: str = field(default_factory=_now)
    initial: Dict[str, Any] = field(default_factory=dict)
    events: List[LabEvent] = field(default_factory=list)
    final: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.events)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "source": self.source,
            "title": self.title,
            "created": self.created,
            "initial": self.initial,
            "events": [e.to_dict() for e in self.events],
            "final": self.final,
            "meta": self.meta,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LabTrace":
        return cls(
            source=str(d.get("source", "")),
            title=str(d.get("title", "")),
            schema=int(d.get("schema", SCHEMA_VERSION)),
            created=str(d.get("created", _now())),
            initial=dict(d.get("initial", {})),
            events=[LabEvent.from_dict(e) for e in d.get("events", [])],
            final=dict(d.get("final", {})),
            meta=dict(d.get("meta", {})),
        )

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "LabTrace":
        p = Path(path)
        return cls.from_dict(json.loads(p.read_text(encoding="utf-8")))


class TraceBuilder:
    """
    Convenience builder for constructing LabTrace objects.

    The builder keeps a current state dictionary. If you do not provide
    before/after explicitly, it reuses the current state.
    """

    def __init__(
        self,
        source: str,
        title: str,
        initial: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        self.source = source
        self.title = title
        self.initial = jsonable(initial or {})
        self.meta = jsonable(meta or {})
        self.events: List[LabEvent] = []
        self.state = self.initial

    def event(
        self,
        kind: str,
        path: str = "",
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        t: Optional[float] = None,
        **meta: Any,
    ) -> LabEvent:
        b = self.state if before is None else jsonable(before)
        a = b if after is None else jsonable(after)

        ev = LabEvent(
            step=len(self.events),
            source=self.source,
            kind=kind,
            path=path,
            before=b,
            after=a,
            meta=jsonable(meta),
            t=t,
        )

        self.events.append(ev)
        self.state = a
        return ev

    def build(self, final: Optional[Dict[str, Any]] = None) -> LabTrace:
        return LabTrace(
            source=self.source,
            title=self.title,
            schema=SCHEMA_VERSION,
            created=_now(),
            initial=self.initial,
            events=self.events,
            final=jsonable(self.state if final is None else final),
            meta=self.meta,
        )


def _run_self_tests():
    import tempfile

    b = TraceBuilder("demo", "Demo trace", initial={"x": 1})
    b.event("inc", path="root[0]", after={"x": 2}, delta=1)
    b.event("noop", path="root[1]")

    tr = b.build()

    assert len(tr) == 2
    assert tr.events[0].after["x"] == 2
    assert tr.events[1].before["x"] == 2
    assert tr.final["x"] == 2

    d = tr.to_dict()
    tr2 = LabTrace.from_dict(d)
    assert len(tr2) == 2
    assert tr2.events[0].kind == "inc"

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "trace.json"
        tr.save(p)
        tr3 = LabTrace.load(p)
        assert len(tr3) == 2
        assert tr3.final["x"] == 2

    print("All lab-trace self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()
