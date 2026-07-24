from __future__ import annotations


def run(args, mgr) -> None:
    issues = mgr.doctor(args.name)
    if not issues:
        print(f"{args.name}: healthy")
        return
    print(f"{args.name}: {len(issues)} issue(s)")
    for issue in issues:
        print(f"  - {issue}")
