from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Optional

from jacobs_lab.testing.trace.lab_trace import LabTrace


def _write(path: str | Path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def format_text(trace: LabTrace) -> str:
    lines = []

    lines.append(f"Trace: {trace.title} ({trace.source})")
    lines.append(
        f"schema: {trace.schema}, created: {trace.created}, events: {len(trace.events)}"
    )
    lines.append("")
    lines.append(f"initial: {json.dumps(trace.initial, sort_keys=True, default=str)}")
    lines.append("")

    for e in trace.events:
        lines.append(f"#{e.step:04d} {e.kind:<16} {e.path}")

        if e.meta:
            lines.append(
                f"    meta:   {json.dumps(e.meta, sort_keys=True, default=str)}"
            )

        lines.append(f"    before: {json.dumps(e.before, sort_keys=True, default=str)}")
        lines.append(f"    after:  {json.dumps(e.after, sort_keys=True, default=str)}")
        lines.append("")

    lines.append(f"final: {json.dumps(trace.final, sort_keys=True, default=str)}")

    return "\n".join(lines)


def export_text(trace: LabTrace, path: Optional[str | Path] = None) -> str:
    text = format_text(trace)

    if path is None:
        print(text)
    else:
        _write(path, text)

    return text


_HTML_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>__TITLE__</title>
<style>
body {
  background: #111;
  color: #ddd;
  font-family: monospace;
  margin: 16px;
}

h1 {
  font-size: 18px;
}

#controls {
  margin: 10px 0;
}

#wrap {
  display: flex;
  gap: 18px;
}

#list {
  width: 430px;
  height: 620px;
  overflow: auto;
  border: 1px solid #333;
  padding: 8px;
}

#detail {
  flex: 1;
  height: 620px;
  overflow: auto;
  border: 1px solid #333;
  padding: 8px;
  white-space: pre-wrap;
}

.event {
  padding: 2px 4px;
  cursor: pointer;
}

.selected {
  background: #432;
  color: #ffd58a;
}
</style>
</head>
<body>

<h1>__TITLE__</h1>

<div id="status"></div>

<div id="controls">
  <button id="prev">&lt;</button>
  <button id="next">&gt;</button>
  <button id="play">play</button>
  <input id="slider" type="range" min="0" max="0" value="0" style="width: 600px;">
</div>

<div id="wrap">
  <div id="list"></div>
  <div id="detail"></div>
</div>

<script type="application/json" id="trace-data">__TRACE_JSON__</script>

<script>
const trace = JSON.parse(document.getElementById("trace-data").textContent);
const events = trace.events || [];

let i = 0;
let playing = false;
let timer = null;

const slider = document.getElementById("slider");
slider.max = Math.max(0, events.length - 1);

function short(s, n = 160) {
  s = String(s);
  return s.length > n ? s.slice(0, n - 3) + "..." : s;
}

function fmt(v) {
  if (v === null || v === undefined) return "null";
  if (typeof v === "object") return short(JSON.stringify(v));
  return short(v);
}

function render() {
  if (!events.length) {
    document.getElementById("status").textContent = "empty trace";
    return;
  }

  const e = events[i];
  slider.value = i;

  document.getElementById("status").textContent =
    trace.title + " [" + trace.source + "] step " + (i + 1) + "/" + events.length +
    " kind=" + e.kind;

  const list = document.getElementById("list");
  list.innerHTML = "";

  const top = Math.max(0, Math.min(i - 20, events.length - 41));
  const bottom = Math.min(events.length, top + 41);

  for (let j = top; j < bottom; j++) {
    const div = document.createElement("div");
    div.className = "event" + (j === i ? " selected" : "");
    div.textContent =
      (j === i ? "> " : "  ") +
      String(events[j].step).padStart(4, "0") + " " +
      events[j].kind + " " +
      (events[j].path || "");

    div.onclick = () => {
      i = j;
      render();
    };

    list.appendChild(div);
  }

  let lines = [];

  lines.push("kind: " + e.kind);
  lines.push("path: " + e.path);

  if (e.t !== null && e.t !== undefined) {
    lines.push("t: " + e.t);
  }

  lines.push("");
  lines.push("meta:");
  lines.push(JSON.stringify(e.meta || {}, null, 2));

  lines.push("");
  lines.push("before:");
  lines.push(JSON.stringify(e.before || {}, null, 2));

  lines.push("");
  lines.push("after:");
  lines.push(JSON.stringify(e.after || {}, null, 2));

  document.getElementById("detail").textContent = lines.join("\n");
}

function step(d) {
  i = Math.max(0, Math.min(events.length - 1, i + d));
  render();
}

document.getElementById("prev").onclick = () => step(-1);
document.getElementById("next").onclick = () => step(1);

document.getElementById("play").onclick = () => {
  playing = !playing;

  if (playing) {
    timer = setInterval(() => {
      if (i < events.length - 1) {
        step(1);
      } else {
        playing = false;
        clearInterval(timer);
      }
    }, 350);
  } else {
    clearInterval(timer);
  }
};

slider.oninput = () => {
  i = Number(slider.value);
  render();
};

render();
</script>

</body>
</html>
"""


def export_html(trace: LabTrace, path: str | Path) -> None:
    payload = json.dumps(trace.to_dict(), default=str).replace("</", "<\\/")
    title = html.escape(trace.title, quote=False)

    doc = _HTML_TEMPLATE.replace("__TITLE__", title)
    doc = doc.replace("__TRACE_JSON__", payload)

    _write(path, doc)


def export_png(trace: LabTrace, path: str | Path) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("matplotlib is required for PNG export") from exc

    fig, ax = plt.subplots(figsize=(14, 4))

    if trace.events:
        kinds = sorted({e.kind for e in trace.events})
        y_for_kind = {k: i for i, k in enumerate(kinds)}

        xs = [e.step for e in trace.events]
        ys = [y_for_kind[e.kind] for e in trace.events]

        ax.scatter(xs, ys, s=18)
        ax.set_yticks(range(len(kinds)))
        ax.set_yticklabels(kinds)
        ax.set_xlabel("step")
        ax.grid(True, alpha=0.25)
    else:
        ax.text(0.5, 0.5, "empty trace", ha="center", va="center")

    ax.set_title(f"{trace.title} ({trace.source})")
    fig.tight_layout()

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=150)
    plt.close(fig)


def export_trace(
    trace: LabTrace,
    path: str | Path,
    fmt: Optional[str] = None,
) -> None:
    p = Path(path)
    fmt = (fmt or p.suffix.lstrip(".")).lower()

    if fmt == "json":
        trace.save(p)
    elif fmt in ("txt", "text"):
        export_text(trace, p)
    elif fmt in ("html", "htm"):
        export_html(trace, p)
    elif fmt == "png":
        export_png(trace, p)
    else:
        raise ValueError(f"unsupported export format: {fmt}")
