"""Refuse CLI source that owns any of the server's vocabulary, using the live server as the list.

This is the real half of the forbidden-ownership rule. Nothing here maintains a list of tool
names, tags, capability ids or routing sentences: it asks a running editor for all of them and
then searches the CLI package for each. A capability added tomorrow is covered tomorrow.

    python cli/tools/check_cli_forwarding.py --port 19781

Only ``cli/jutsu_mcp`` and ``cli/jutsu_mcp_stdio.py`` are searched, and only their text - string
literals and comments. Tests and tools name capabilities on purpose.
"""

import argparse
import ast
import io
import os
import re
import sys
import tokenize

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jutsu_mcp.transport import Client, TransportError, resolve_port  # noqa: E402

SCANNED = ("jutsu_mcp", "jutsu_mcp_stdio.py")

#: A routing sentence worth searching for. Shorter fragments match by accident.
MINIMUM_SENTENCE_WORDS = 5

#: How a harvested term is matched against CLI text. Tool names, capability ids and routing
#: sentences cannot occur by accident, so any occurrence is a finding. Canonical tags are often
#: ordinary English words - "editor", "input", "project", "data" - and the CLI has every right to
#: use them in a sentence about its own transport. What it may not do is carry one as a value, so
#: a tag is a finding only when a whole string literal is exactly that tag.
ANYWHERE = "anywhere"
AS_A_VALUE = "as a value"


def cli_text(root):
    """Every string literal and comment in the scanned package.

    Each fragment carries its raw source text and, for a plain string literal, the value that
    literal actually holds - which is what a tag has to be compared against.
    """
    fragments = []
    for path in _python_files(root):
        with open(path, "r", encoding="utf-8") as handle:
            source = handle.read()
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type not in (tokenize.STRING, tokenize.COMMENT):
                continue
            value = None
            if token.type == tokenize.STRING:
                try:
                    parsed = ast.literal_eval(token.string)
                except (ValueError, SyntaxError):
                    parsed = None
                value = parsed if isinstance(parsed, str) else None
            fragments.append((os.path.relpath(path, root), token.start[0], token.string, value))
    return fragments


def _python_files(root):
    for entry in SCANNED:
        path = os.path.join(root, entry)
        if os.path.isfile(path):
            yield path
            continue
        for directory, _, names in os.walk(path):
            for name in sorted(names):
                if name.endswith(".py"):
                    yield os.path.join(directory, name)


def sentences(text):
    for sentence in re.split(r"(?<=[.;:])\s+", text or ""):
        sentence = sentence.strip()
        if len(sentence.split()) >= MINIMUM_SENTENCE_WORDS:
            yield sentence


def harvest(client):
    """Collect everything the server owns that the CLI must not repeat."""
    forbidden = {}

    initialize = client.initialize_result
    for sentence in sentences(initialize.get("instructions", "")):
        forbidden[sentence] = ("a sentence of the initialize instructions", ANYWHERE)

    tools = client.call("tools/list")["result"]["tools"]
    for tool in tools:
        forbidden[tool["name"]] = ("a fixed tool name", ANYWHERE)
        for field in ("title", "description"):
            for sentence in sentences(tool.get(field)):
                forbidden[sentence] = ("a sentence of the %s tool %s" % (tool["name"], field), ANYWHERE)

    catalog = _call(client, {"mode": "catalog", "page": {"budgetBytes": 262144}})
    tags = []
    for group in (catalog.get("catalog") or {}).values():
        for entry in group:
            tag = entry.get("tag")
            if not tag:
                continue
            tags.append(tag)
            forbidden.setdefault(tag, ("a canonical tag", AS_A_VALUE))

    for tag in tags:
        results = _call(client, {"mode": "search", "tags": [tag], "limit": 100,
                                 "page": {"budgetBytes": 262144}})
        for hit in results.get("results") or []:
            if hit.get("id"):
                forbidden[hit["id"]] = ("a capability id", ANYWHERE)

    return forbidden, tags


def _call(client, arguments):
    """One capability search. This file is a tool, so it may name the tool it drives."""
    response = client.call(
        "tools/call", {"name": "jutsu_capabilities_search", "arguments": arguments}
    )["result"]
    return response.get("structuredContent") or {}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--root", default=None, help="CLI directory to scan; defaults to this one.")
    arguments = parser.parse_args(argv)
    root = arguments.root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    try:
        client = Client(resolve_port(arguments.port))
        client.connect({"name": "check-cli-forwarding", "version": "1"})
    except TransportError as failure:
        print("check_cli_forwarding: %s" % failure, file=sys.stderr)
        return 2

    try:
        forbidden, tags = harvest(client)
    finally:
        client.close()

    fragments = cli_text(root)
    hits = []
    for term, (kind, how) in forbidden.items():
        for path, line, text, value in fragments:
            if term in text if how == ANYWHERE else value == term:
                hits.append((path, line, kind, term))

    print("%d term(s) harvested from the live server across %d tag(s); "
          "%d CLI text fragment(s) searched." % (len(forbidden), len(tags), len(fragments)))
    if hits:
        for path, line, kind, term in sorted(hits):
            print("%s:%d: carries %s: %r" % (path, line, kind, term))
        print("\n%d forbidden reference(s)." % len(hits))
        return 1
    print("The CLI carries none of the server's vocabulary.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
