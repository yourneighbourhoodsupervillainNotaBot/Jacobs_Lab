from __future__ import annotations

import argparse
import sys

from lab_trace import LabTrace


def cmd_trace(args):
    from lab_adapters import (
        trace_flexagon,
        trace_fold_demo,
        trace_portal_natural_transformation,
        trace_test_walk,
        trace_triangle_walk,
    )

    if args.source == "triangle":
        trace = trace_triangle_walk(loops=args.loops, start=args.start)

    elif args.source == "test-walk":
        trace = trace_test_walk(
            run_real=args.real,
            inject_failure=args.inject_failure,
        )

    elif args.source == "fold":
        trace = trace_fold_demo(args.demo)

    elif args.source == "flexagon":
        trace = trace_flexagon()

    elif args.source == "category":
        trace = trace_portal_natural_transformation()

    else:
        raise ValueError(f"unknown trace source: {args.source}")

    if args.save:
        trace.save(args.save)
        print(f"Saved trace to {args.save}")

    if args.text:
        from lab_export import export_text

        export_text(trace, None)

    if args.inspect:
        try:
            from lab_inspector import show_lab_trace

            show_lab_trace(trace)
        except Exception as exc:
            print(f"Inspector unavailable: {exc}")
            print("Printing text trace instead.")
            from lab_export import export_text

            export_text(trace, None)

    if not (args.save or args.text or args.inspect):
        print(
            f"Built trace '{trace.title}' with {len(trace.events)} events. "
            "Use --save, --text, or --inspect."
        )


def cmd_inspect(args):
    trace = LabTrace.load(args.trace)

    try:
        from lab_inspector import show_lab_trace

        show_lab_trace(trace)
    except Exception as exc:
        print(f"Inspector unavailable: {exc}")
        print("Printing text trace instead.")
        from lab_export import export_text

        export_text(trace, None)


def cmd_export(args):
    from lab_export import export_trace

    trace = LabTrace.load(args.trace)
    export_trace(trace, args.out, args.format)
    print(f"Exported {args.trace} -> {args.out}")


def cmd_test(args):
    import lab_adapters
    import lab_trace

    lab_trace._run_self_tests()
    lab_adapters._run_self_tests()

    print("All lab-layer self-tests passed.")


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="lab_cli",
        description="Unified trace/inspector/export CLI for the folding laboratory.",
    )

    sub = ap.add_subparsers(dest="cmd", required=True)

    # trace
    tr = sub.add_parser("trace", help="build a trace from a lab source")
    tr.add_argument(
        "source",
        choices=["triangle", "test-walk", "fold", "flexagon", "category"],
    )
    tr.add_argument("--loops", type=int, default=2)
    tr.add_argument("--start", default="F")
    tr.add_argument(
        "--demo",
        choices=["fold", "glue", "while"],
        default="fold",
        help="fold demo program",
    )
    tr.add_argument(
        "--real",
        action="store_true",
        help="for test-walk: run the real test suite instead of synthetic results",
    )
    tr.add_argument(
        "--inject-failure",
        action="store_true",
        help="for synthetic test-walk: inject one failure",
    )
    tr.add_argument("--save", help="save trace JSON to this path")
    tr.add_argument("--text", action="store_true", help="print text trace")
    tr.add_argument("--inspect", action="store_true", help="open pyglet inspector")

    # inspect
    ins = sub.add_parser("inspect", help="inspect a saved trace")
    ins.add_argument("trace")

    # export
    exp = sub.add_parser("export", help="export a saved trace")
    exp.add_argument("trace")
    exp.add_argument("out")
    exp.add_argument(
        "--format",
        choices=["json", "text", "html", "png"],
        default=None,
    )

    # test
    sub.add_parser("test", help="run lab-layer self-tests")

    args = ap.parse_args(argv)

    if args.cmd == "trace":
        cmd_trace(args)
    elif args.cmd == "inspect":
        cmd_inspect(args)
    elif args.cmd == "export":
        cmd_export(args)
    elif args.cmd == "test":
        cmd_test(args)
    else:
        ap.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
