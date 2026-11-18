"""Run Product Intelligence Companion with JSON-over-stdio adapters."""
import argparse
import json
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SELECTION_MODES = ("manual", "augment", "discover")
FEEDBACK_GROUPS = ("competitors", "own")
SECTIONS = {
    "highlights": "Highlights",
    "releases": "Competitor releases",
    "competitor_feedback": "Competitor customer feedback",
    "own_feedback": "Our customer feedback",
    "outside_highlights": "Outside the focus area",
    "suggested_competitors": "Suggested competitors",
}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def invoke(command, request):
    if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
        raise ValueError("Adapters must be command argument arrays")
    result = subprocess.run(command, input=json.dumps(request), text=True,
                            stdout=subprocess.PIPE, check=True, timeout=600)
    return json.loads(result.stdout)


def validate_scope(scope):
    if scope["coverage"] not in ("focused", "focused_plus", "all"):
        raise ValueError("Invalid coverage mode")
    if scope["coverage"] != "all" and not scope.get("focus"):
        raise ValueError("A focus is required for focused coverage")
    if scope["competitor_mode"] not in SELECTION_MODES:
        raise ValueError("Invalid competitor mode")
    if not scope["company"].strip():
        raise ValueError("Enter a company name")
    ZoneInfo(scope["timezone"])
    feedback = scope.get("feedback_sources", {})
    if not isinstance(feedback, dict) or set(feedback) - set(FEEDBACK_GROUPS):
        raise ValueError("feedback_sources must contain only competitors and own settings")
    for group, selection in feedback.items():
        if not isinstance(selection, dict) or selection.get("mode") not in SELECTION_MODES:
            raise ValueError(f"Invalid feedback source mode for {group}")
        sources = selection.get("sources", [])
        if not isinstance(sources, list) or any(
            not isinstance(source, str) or not source.strip() for source in sources
        ):
            raise ValueError(f"Feedback sources for {group} must be a list of names or URLs")
        if selection["mode"] == "manual" and not sources:
            raise ValueError(f"Manual feedback source selection for {group} requires a source")
        if selection["mode"] == "discover" and sources:
            raise ValueError(f"Use augment mode to combine listed and discovered sources for {group}")


def validate_evidence(records):
    indexed = {}
    for row in records:
        key = row["id"]
        url = urlsplit(row["url"])
        if not key or key in indexed or url.scheme not in ("http", "https") or not url.hostname:
            raise ValueError("Evidence requires unique IDs and public source URLs")
        if row.get("date"):
            date.fromisoformat(row["date"])
        indexed[key] = row
    return indexed


def render(report, evidence, start, end, scope, coverage):
    lines = [f'# {scope["company"]} Product Intelligence Brief', "",
             f"{start} through {end} · {scope['timezone']}"]
    if set(report) != set(SECTIONS):
        raise ValueError("Report must contain all expected sections")
    for key, heading in SECTIONS.items():
        items = report[key]
        if not isinstance(items, list):
            raise ValueError(f"{key} must be an array")
        if key == "highlights" and len(items) > 3:
            raise ValueError("Use at most three highlights")
        if key == "outside_highlights" and scope["coverage"] != "focused_plus":
            if items:
                raise ValueError("Outside highlights require focused_plus coverage")
            continue
        if key == "suggested_competitors" and scope["competitor_mode"] == "manual":
            if items:
                raise ValueError("Competitor suggestions require discovery")
            continue
        lines += ["", f"## {heading}", ""]
        for item in items:
            citations = item["evidence_ids"]
            if not isinstance(citations, list) or not citations or any(i not in evidence for i in citations):
                raise ValueError(f"Missing or invalid evidence IDs in {key}")
            if key != "suggested_competitors" and not any(
                start.isoformat() <= (evidence[i].get("date") or "") <= end.isoformat()
                for i in citations
            ):
                raise ValueError(f"No reporting-window evidence in {key}")
            links = " ".join(f'<{evidence[i]["url"]}>' for i in dict.fromkeys(citations))
            lines.append(f'- {item["text"]} {links}')
        if not items:
            lines.append("No verified findings in the evidence reviewed.")
    lines += ["", "## Source coverage", ""]
    lines.extend(f"- {entry}" for entry in coverage)
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("discover", "run"))
    parser.add_argument("config")
    parser.add_argument("--as-of", type=date.fromisoformat)
    args = parser.parse_args()
    config = load(args.config)
    if config["version"] != 1:
        raise ValueError("Unsupported config version")
    scope = config["scope"]
    validate_scope(scope)
    scope["feedback_sources"] = {
        group: {"mode": "discover", "sources": [], **scope.get("feedback_sources", {}).get(group, {})}
        for group in FEEDBACK_GROUPS
    }
    end = (args.as_of or datetime.now(ZoneInfo(scope["timezone"])).date()) - timedelta(days=1)
    start = end - timedelta(days=6)
    adapters = config["adapters"]
    history = Path(config.get("report_directory", "reports"))
    prior = sorted(history.glob("*.md"))
    prior = [p for p in prior if p.stem < end.isoformat()]
    request = {
        "mode": args.mode, "scope": scope,
        "start": start.isoformat(), "end": end.isoformat(),
        "instructions": (ROOT / "WORKFLOW.md").read_text(encoding="utf-8"),
    }
    research = invoke(adapters["research"], request)
    evidence = validate_evidence(research["evidence"])
    result = invoke(adapters["model"], {
        **request, "evidence": list(evidence.values()), "coverage": research["coverage"],
        "prior_report": prior[-1].read_text(encoding="utf-8") if prior else None,
        "report_sections": list(SECTIONS),
    })
    if args.mode == "discover":
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    report = render(result, evidence, start, end, scope, research["coverage"])
    history.mkdir(parents=True, exist_ok=True)
    path = history / f"{end}.md"
    path.write_text(report, encoding="utf-8")
    if adapters.get("delivery"):
        invoke(adapters["delivery"], {"report": report, "period_end": end.isoformat()})
    print(report, end="")


if __name__ == "__main__":
    main()
