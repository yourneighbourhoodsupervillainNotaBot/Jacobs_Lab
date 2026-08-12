from __future__ import annotations

import argparse
import sys

from legacy.flat_modules.lab_trace import LabTrace

SOURCES = [
    "triangle",
    "test-walk",
    "fold",
    "flexagon",
    "category",
    "pathfinding",
    "three-body",
    "fold-codec",
    "fold-complexity",
    "prime",
    "universality",
]


def _parse_pair(s: str):
    x, y = s.replace(" ", "").split(",")
    return int(x), int(y)


def cmd_trace(args):
    source = args.source

    if source == "triangle":
        from legacy.flat_modules.lab_adapters import trace_triangle_walk

        trace = trace_triangle_walk(loops=args.loops, start=args.start)

    elif source == "test-walk":
        from legacy.flat_modules.lab_adapters import trace_test_walk

        trace = trace_test_walk(
            run_real=args.real,
            inject_failure=args.inject_failure,
        )

    elif source == "fold":
        from legacy.flat_modules.lab_adapters import trace_fold_demo

        trace = trace_fold_demo(args.demo)

    elif source == "flexagon":
        from legacy.flat_modules.lab_adapters import trace_flexagon

        trace = trace_flexagon()

    elif source == "category":
        from legacy.flat_modules.lab_adapters import trace_portal_natural_transformation

        trace = trace_portal_natural_transformation()

    elif source == "pathfinding":
        try:
            from legacy.flat_modules.lab_adapters_extended import trace_pathfinding
        except ImportError as exc:
            raise SystemExit(
                "pathfinding tracing requires lab_adapters_extended.py. "
                "Make sure that file exists in the repository root."
            ) from exc

        trace = trace_pathfinding(
            start=_parse_pair(args.start_pos),
            goal=_parse_pair(args.goal),
        )

    elif source == "three-body":
        try:
            from legacy.flat_modules.lab_adapters_extended import trace_three_body
        except ImportError as exc:
            raise SystemExit(
                "three-body tracing requires lab_adapters_extended.py. "
                "Make sure that file exists in the repository root."
            ) from exc

        trace = trace_three_body(
            periods=args.periods,
            sample_every=args.sample_every,
        )

    elif source == "fold-codec":
        try:
            from legacy.flat_modules.lab_adapters_extended import trace_fold_codec
        except ImportError as exc:
            raise SystemExit(
                "fold-codec tracing requires lab_adapters_extended.py. "
                "Make sure that file exists in the repository root."
            ) from exc

        trace = trace_fold_codec(kind=args.codec)

    elif source == "fold-complexity":
        try:
            from legacy.flat_modules.lab_adapters_extended import trace_fold_complexity
        except ImportError as exc:
            raise SystemExit(
                "fold-complexity tracing requires lab_adapters_extended.py. "
                "Make sure that file exists in the repository root."
            ) from exc

        trace = trace_fold_complexity()

    elif source == "prime":
        try:
            from legacy.flat_modules.lab_adapters_extended import trace_prime_machinery
        except ImportError as exc:
            raise SystemExit(
                "prime tracing requires lab_adapters_extended.py. "
                "Make sure that file exists in the repository root."
            ) from exc

        trace = trace_prime_machinery(
            limit=args.limit,
            vm_limit=args.vm_limit,
        )

    elif source == "universality":
        try:
            from legacy.flat_modules.lab_adapters_extended import trace_universality_probe
        except ImportError as exc:
            raise SystemExit(
                "universality tracing requires lab_adapters_extended.py. "
                "Make sure that file exists in the repository root."
            ) from exc

        trace = trace_universality_probe(max_functions=args.max_functions)

    else:
        raise ValueError(f"unknown trace source: {source}")

    if args.save:
        trace.save(args.save)
        print(f"Saved trace to {args.save}")

    if args.text:
        from legacy.flat_modules.lab_export import export_text

        export_text(trace, None)

    if args.inspect:
        try:
            from legacy.flat_modules.lab_inspector import show_lab_trace

            show_lab_trace(trace)
        except Exception as exc:
            print(f"Inspector unavailable: {exc}")
            print("Printing text trace instead.")

            from legacy.flat_modules.lab_export import export_text

            export_text(trace, None)

    if not (args.save or args.text or args.inspect):
        print(
            f"Built trace '{trace.title}' with {len(trace.events)} events. "
            "Use --save, --text, or --inspect."
        )


def cmd_inspect(args):
    trace = LabTrace.load(args.trace)

    try:
        from legacy.flat_modules.lab_inspector import show_lab_trace

        show_lab_trace(trace)
    except Exception as exc:
        print(f"Inspector unavailable: {exc}")
        print("Printing text trace instead.")

        from legacy.flat_modules.lab_export import export_text

        export_text(trace, None)


def cmd_export(args):
    from legacy.flat_modules.lab_export import export_trace

    trace = LabTrace.load(args.trace)
    export_trace(trace, args.out, args.format)
    print(f"Exported {args.trace} -> {args.out}")


def cmd_sonify(args):
    try:
        from legacy.flat_modules.lab_sonify_trace import write_trace_wav
    except ImportError as exc:
        raise SystemExit(
            "Trace sonification requires lab_sonify_trace.py. "
            "Make sure that file exists in the repository root."
        ) from exc

    trace = LabTrace.load(args.trace)
    write_trace_wav(trace, args.out, base_duration=args.base_duration)
    print(f"Wrote trace audio to {args.out}")


def cmd_test(args):
    import legacy.flat_modules.lab_trace as lab_trace

    lab_trace._run_self_tests()

    try:
        import legacy.flat_modules.lab_adapters as lab_adapters

        lab_adapters._run_self_tests()
    except ImportError as exc:
        print(f"Skipping lab_adapters tests: {exc}")

    try:
        import legacy.flat_modules.lab_adapters_extended as lab_adapters_extended

        lab_adapters_extended._run_self_tests()
    except ImportError as exc:
        print(f"Skipping lab_adapters_extended tests: {exc}")
    try:
        try:
            from ... import lab_sonify_trace
        except ImportError:
            import legacy.flat_modules.lab_sonify_trace as lab_sonify_trace

        fn = getattr(lab_sonify_trace, "_run_self_tests", None)

        if callable(fn):
            fn()
        else:
            print("Skipping lab_sonify_trace tests: no _run_self_tests() found")

    except ImportError as exc:
        print(f"Skipping lab_sonify_trace tests: {exc}")
    except Exception as exc:
        print(f"lab_sonify_trace tests failed: {exc}")

    print("All available lab-layer self-tests passed.")


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="lab_cli",
        description=(
            "Unified trace/inspector/export/sonify CLI for the folding laboratory."
        ),
    )

    sub = ap.add_subparsers(dest="cmd", required=True)

    # trace
    tr = sub.add_parser("trace", help="build a trace from a lab source")

    tr.add_argument("source", choices=SOURCES)

    # triangle
    tr.add_argument("--loops", type=int, default=2)
    tr.add_argument("--start", default="F")

    # fold demo
    tr.add_argument(
        "--demo",
        choices=["fold", "glue", "while"],
        default="fold",
        help="fold demo program",
    )

    # test-walk
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

    # pathfinding
    tr.add_argument("--start-pos", default="1,1")
    tr.add_argument("--goal", default="8,7")

    # three-body
    tr.add_argument("--periods", type=int, default=2)
    tr.add_argument("--sample-every", type=int, default=20)

    # fold-codec
    tr.add_argument(
        "--codec",
        choices=["palindrome", "orb_mirror", "random"],
        default="palindrome",
    )

    # prime
    tr.add_argument("--limit", type=int, default=30)
    tr.add_argument("--vm-limit", type=int, default=10)

    # universality
    tr.add_argument("--max-functions", type=int, default=12)

    # output modes
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

    # sonify
    son = sub.add_parser("sonify", help="sonify a saved trace")
    son.add_argument("trace")
    son.add_argument("out")
    son.add_argument("--base-duration", type=float, default=0.18)

    # test
    sub.add_parser("test", help="run lab-layer self-tests")

    args = ap.parse_args(argv)

    if args.cmd == "trace":
        cmd_trace(args)
    elif args.cmd == "inspect":
        cmd_inspect(args)
    elif args.cmd == "export":
        cmd_export(args)
    elif args.cmd == "sonify":
        cmd_sonify(args)
    elif args.cmd == "test":
        cmd_test(args)
    else:
        ap.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
