"""Measure candidate render formats against the JSON the server actually returned.

The premise of the CLI - that an agent reads something cheaper than JSON - is the part most
likely to be wrong, so it is decided here by counting rather than by taste. The corpus is real
traffic: the `--json` event streams of the recorded fresh-agent runs, which hold the response
body of every MCP call those agents made.

Tokens are the unit, not bytes. JSON punctuation costs one byte and about one token per
character, while prose costs about four characters per token, so a byte count answers a
different question than the one an agent pays for. Both are reported.

    python cli/tools/measure_formats.py <directory of recorded runs>

Needs `tiktoken` for the token counts. Without it the script still reports bytes and says so.
This file is a measurement tool, not CLI source, so it may name capabilities.
"""

import argparse
import collections
import glob
import json
import os
import sys

try:
    import tiktoken
    ENCODING = tiktoken.get_encoding("o200k_base")
    ENCODING_NAME = "o200k_base"
except ImportError:
    ENCODING = None
    ENCODING_NAME = "(tiktoken not installed - byte counts only)"


def tokens(text):
    return len(ENCODING.encode(text)) if ENCODING else 0


def as_json(value):
    """The control: what the server sends today, as the CLI forwards it."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def as_indented(value, indent=0):
    """One leaf per line, arrays indexed. The shape a person would write by hand."""
    pad = "  " * indent
    lines = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)) and item:
                lines.append(f"{pad}{key}:")
                lines.extend(as_indented(item, indent + 1))
            else:
                lines.append(f"{pad}{key}: {scalar(item)}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            if isinstance(item, (dict, list)) and item:
                lines.append(f"{pad}[{index}]:")
                lines.extend(as_indented(item, indent + 1))
            else:
                lines.append(f"{pad}[{index}]: {scalar(item)}")
    else:
        lines.append(f"{pad}{scalar(value)}")
    return lines


def as_paths(value, prefix=""):
    """Flattened paths, the shape the server's own error paths already use ($.steps[0].capability)."""
    lines = []
    if isinstance(value, dict):
        for key, item in value.items():
            lines.extend(as_paths(item, f"{prefix}.{key}" if prefix else key))
    elif isinstance(value, list):
        if not value:
            lines.append(f"{prefix} =")
        for index, item in enumerate(value):
            lines.extend(as_paths(item, f"{prefix}[{index}]"))
    else:
        lines.append(f"{prefix} = {scalar(value)}")
    return lines


def as_markdown(value, depth=2, title=None):
    """Sectioned Markdown, one heading per record."""
    lines = []
    if title:
        lines.append(f"{'#' * depth} {title}")
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)) and item:
                lines.extend(as_markdown(item, depth + 1, key))
            else:
                lines.append(f"- {key}: {scalar(item)}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            if isinstance(item, (dict, list)) and item:
                lines.extend(as_markdown(item, depth + 1, f"{title or 'item'}[{index}]"))
            else:
                lines.append(f"- {scalar(item)}")
    return lines


def as_table(value, indent=0):
    """Indented lines, except that a uniform array of flat records becomes one table.

    This is the only candidate that stops repeating a key per record, which is where a list
    response spends most of its structure. It is a generic shape rule - "uniform array of flat
    records" - and knows nothing about which capability produced the array.
    """
    pad = "  " * indent
    lines = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, list) and uniform_flat_records(item):
                lines.append(f"{pad}{key}:")
                lines.extend(table_rows(item, indent + 1))
            elif isinstance(item, (dict, list)) and item:
                lines.append(f"{pad}{key}:")
                lines.extend(as_table(item, indent + 1))
            else:
                lines.append(f"{pad}{key}: {scalar(item)}")
    elif isinstance(value, list):
        if uniform_flat_records(value):
            lines.extend(table_rows(value, indent))
        else:
            for index, item in enumerate(value):
                if isinstance(item, (dict, list)) and item:
                    lines.append(f"{pad}[{index}]:")
                    lines.extend(as_table(item, indent + 1))
                else:
                    lines.append(f"{pad}[{index}]: {scalar(item)}")
    return lines


def uniform_flat_records(value):
    """Two or more objects, same keys, no nested containers: the case a table can carry."""
    if not isinstance(value, list) or len(value) < 2:
        return False
    keys = None
    for item in value:
        if not isinstance(item, dict) or not item:
            return False
        if any(isinstance(field, (dict, list)) for field in item.values()):
            return False
        if keys is None:
            keys = list(item.keys())
        elif list(item.keys()) != keys:
            return False
    return True


def table_rows(value, indent):
    pad = "  " * indent
    keys = list(value[0].keys())
    lines = [pad + " | ".join(keys)]
    for item in value:
        lines.append(pad + " | ".join(scalar(item[key]) for key in keys))
    return lines


def scalar(value):
    """Identity strings are never re-cased, re-quoted or wrapped; only JSON's own spelling goes."""
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    return str(value)


FORMATS = {
    "json": as_json,
    "indented": lambda value: "\n".join(as_indented(value)),
    "paths": lambda value: "\n".join(as_paths(value)),
    "markdown": lambda value: "\n".join(as_markdown(value)),
    "table": lambda value: "\n".join(as_table(value)),
}


def recorded_responses(directory):
    """Every response body a recorded run received, newest file last."""
    found = []
    for path in sorted(glob.glob(os.path.join(directory, "*.jsonl"))):
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                item = (event or {}).get("item") or {}
                if item.get("type") != "mcp_tool_call" or item.get("status") == "in_progress":
                    continue
                body = (item.get("result") or {}).get("structured_content")
                if isinstance(body, dict) and body:
                    found.append((os.path.basename(path), item.get("tool", "?"), item.get("arguments") or {}, body))
    return found


def classify(tool, arguments, body):
    """The response classes MCP_FEEDBACK.md says dominated the runs."""
    if "error" in body:
        return "error + recovery" if not body.get("error", {}).get("detailRoute") else "oversized refusal"
    if body.get("page", {}).get("oversizedRecord"):
        return "oversized refusal"
    if tool == "jutsu_capabilities_search":
        return "search answer"
    if tool == "jutsu_capabilities_describe":
        return "describe invoke"
    if tool == "jutsu_recommend":
        return "recommend answer"
    if tool == "jutsu_execute":
        return "execute success" if body.get("success") is True else "execute full"
    if tool == "jutsu_inspect":
        return "inspect answer"
    return tool


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default=".artifacts/agent-runs")
    parser.add_argument("--top", type=int, default=0, help="Also list the N largest single responses.")
    arguments = parser.parse_args(argv)

    responses = recorded_responses(arguments.directory)
    if not responses:
        print("no recorded responses found in %s" % arguments.directory, file=sys.stderr)
        return 2

    names = list(FORMATS)
    totals = {name: [0, 0] for name in names}
    by_class = collections.defaultdict(lambda: {name: [0, 0] for name in names})
    counts = collections.Counter()

    for _, tool, call_arguments, body in responses:
        group = classify(tool, call_arguments, body)
        counts[group] += 1
        for name, render in FORMATS.items():
            text = render(body)
            measured = (tokens(text), len(text.encode("utf-8")))
            for index in (0, 1):
                totals[name][index] += measured[index]
                by_class[group][name][index] += measured[index]

    print("tokenizer: %s" % ENCODING_NAME)
    print("corpus: %d recorded responses from %s\n" % (len(responses), arguments.directory))

    header = "%-20s %5s" % ("response class", "n") + "".join("%12s" % name for name in names)
    print(header)
    print("-" * len(header))
    for group, _ in counts.most_common():
        row = "%-20s %5d" % (group, counts[group])
        control = by_class[group]["json"][0] or 1
        for name in names:
            share = by_class[group][name][0] * 100 // control
            row += "%12s" % ("%d (%d%%)" % (by_class[group][name][0], share))
        print(row)
    print("-" * len(header))
    control = totals["json"][0] or 1
    row = "%-20s %5d" % ("ALL, tokens", len(responses))
    for name in names:
        row += "%12s" % ("%d (%d%%)" % (totals[name][0], totals[name][0] * 100 // control))
    print(row)
    control_bytes = totals["json"][1] or 1
    row = "%-20s %5s" % ("ALL, bytes", "")
    for name in names:
        row += "%12s" % ("%d%%" % (totals[name][1] * 100 // control_bytes))
    print(row)

    if arguments.top:
        print("\nlargest single responses, tokens as JSON:")
        ranked = sorted(responses, key=lambda entry: tokens(as_json(entry[3])), reverse=True)
        for _, tool, call_arguments, body in ranked[: arguments.top]:
            best = min(names, key=lambda name: tokens(FORMATS[name](body)))
            print("  %6d  %-30s best=%s (%d)" % (
                tokens(as_json(body)), tool, best, tokens(FORMATS[best](body))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
