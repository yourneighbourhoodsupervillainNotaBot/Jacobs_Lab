from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

try:
    from lab_trace import TraceBuilder
except ImportError:
    try:
        from jacobs_lab.testing.trace.lab_trace import TraceBuilder
    except ImportError:
        TraceBuilder = None


class _SimpleTrace:
    def __init__(self, source, title, initial, events, final, meta):
        self.source = source
        self.title = title
        self.initial = initial
        self.events = events
        self.final = final
        self.meta = meta
        self.schema = 1
        self.created = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return {
            "schema": self.schema,
            "source": self.source,
            "title": self.title,
            "created": self.created,
            "initial": self.initial,
            "events": self.events,
            "final": self.final,
            "meta": self.meta,
        }

    def save(self, path):
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(self.to_dict(), indent=2, default=str), encoding="utf-8"
        )


class _SimpleTraceBuilder:
    def __init__(self, source, title, initial=None, meta=None):
        self.source = source
        self.title = title
        self.initial = initial or {}
        self.meta = meta or {}
        self.events = []
        self.state = self.initial

    def event(self, kind, path="", before=None, after=None, t=None, **meta):
        event = {
            "step": len(self.events),
            "source": self.source,
            "kind": kind,
            "path": path,
            "before": before if before is not None else self.state,
            "after": after if after is not None else self.state,
            "meta": meta,
            "t": t,
        }

        self.events.append(event)

        if after is not None:
            self.state = after

        return event

    def build(self, final=None):
        return _SimpleTrace(
            source=self.source,
            title=self.title,
            initial=self.initial,
            events=self.events,
            final=final if final is not None else self.state,
            meta=self.meta,
        )


def make_builder(source, title, initial=None, meta=None):
    if TraceBuilder is not None:
        try:
            return TraceBuilder(
                source=source,
                title=title,
                initial=initial,
                meta=meta,
            )
        except TypeError:
            return TraceBuilder(source, title, initial, meta)

    return _SimpleTraceBuilder(source, title, initial=initial, meta=meta)


def trace_render(settings, band_stats, debug_events=None, fold_info=None):
    builder = make_builder(
        source="spectral_sdf",
        title="Spectral SDF ray-marching render",
        initial=settings,
        meta={"fold_info": fold_info},
    )

    builder.event("init", path="render", after=settings)

    if fold_info is not None:
        builder.event("fold_signature", path="fold", after=fold_info)

    for stats in band_stats:
        builder.event(
            "spectral_band",
            path=f"band[{stats['band']}]",
            after=stats,
            root=stats.get("root"),
            wavelength=stats.get("wavelength"),
        )

    if debug_events:
        for e in debug_events:
            builder.event(
                "ray_step",
                path=f"debug[{e['step']}]",
                before={"t": e["t"]},
                after=e,
                distance=e.get("distance"),
            )

    return builder.build(final={"bands": len(band_stats)})


def save_trace(trace, path):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    if hasattr(trace, "save"):
        trace.save(p)
    elif hasattr(trace, "to_dict"):
        p.write_text(
            json.dumps(trace.to_dict(), indent=2, default=str), encoding="utf-8"
        )
    else:
        p.write_text(json.dumps(trace, indent=2, default=str), encoding="utf-8")
