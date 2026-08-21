"""Refuse CLI source that owns any of the server's vocabulary. Runs without an editor.

The CLI's whole contract is that it forwards rather than declares: tool names, schemas,
descriptions, capability ids and the ``instructions`` string all come from the live server at run
time. A copy of any of them in this package would be a second contract that goes stale silently.

This is the cheap half of the rule, meant for every commit and for machines with no engine
installed. ``check_cli_forwarding.py`` is the real one: it derives the forbidden vocabulary from a
running server rather than from the patterns below.

    python cli/tools/check_cli_vocabulary.py
"""

import ast
import io
import os
import re
import sys
import tokenize

#: Only the package an agent actually talks through is scanned. Tests and tools are allowed to
#: name capabilities, because naming them is how they check that the package does not.
SCANNED = ("jutsu_mcp", "jutsu_mcp_stdio.py")

#: Any fixed tool name. ``jutsu_mcp`` is this package's own name and is not a tool.
TOOL_NAME = re.compile(r"\bjutsu_(?!mcp)[a-z][a-z_]*")

#: A capability id: three or more dotted lowercase segments, hunted in text rather than in code.
CAPABILITY_ID = re.compile(r"\b[a-z][a-z0-9]*(?:\.[a-z][a-z0-9_]*){2,}\b")

#: Unreal object and class paths.
UNREAL_PATH = re.compile(r"/(?:Script|Game|Engine)/")

#: No transport diagnostic needs this much room. The pinned ``instructions`` string is roughly
#: 1,400 characters, so this catches the specific regression the rule exists for.
MAX_LITERAL_CHARACTERS = 400


def python_files(root):
    for entry in SCANNED:
        path = os.path.join(root, entry)
        if os.path.isfile(path):
            yield path
            continue
        for directory, _, names in os.walk(path):
            for name in sorted(names):
                if name.endswith(".py"):
                    yield os.path.join(directory, name)


def docstring_lines(tree):
    """Line numbers of module, class and function docstrings.

    Prose about how the CLI works is the CLI's own, and it is long on purpose. What the rule is
    hunting is server text pasted into a value the CLI hands to an agent.
    """
    lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                lines.add(body[0].value.lineno)
    return lines


def check_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        source = handle.read()
    tree = ast.parse(source, path)
    problems = []

    # Capability ids and object paths are hunted in text only. An attribute chain such as
    # ``response.headers.get`` is code, not vocabulary, and reading it as an id would make the
    # check noise rather than a gate. A tool name is refused anywhere, identifiers included.
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        line_number = token.start[0]
        if token.type == tokenize.NAME:
            for match in TOOL_NAME.finditer(token.string):
                problems.append((line_number, "fixed tool name %r" % match.group(0)))
            continue
        if token.type not in (tokenize.STRING, tokenize.COMMENT):
            continue
        for match in TOOL_NAME.finditer(token.string):
            problems.append((line_number, "fixed tool name %r" % match.group(0)))
        for match in CAPABILITY_ID.finditer(token.string):
            problems.append((line_number, "capability id %r" % match.group(0)))
        if UNREAL_PATH.search(token.string):
            problems.append((line_number, "an Unreal object path"))

    docstrings = docstring_lines(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and node.lineno not in docstrings and len(node.value) > MAX_LITERAL_CHARACTERS:
            problems.append(
                (node.lineno, "a %d-character string literal, which is server prose rather "
                              "than a transport diagnostic" % len(node.value))
            )
    return sorted(problems)


def main(argv=None):
    root = (argv or [None])[0] or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    failures = 0
    scanned = 0
    for path in python_files(root):
        scanned += 1
        for line_number, problem in check_file(path):
            failures += 1
            print("%s:%d: %s" % (os.path.relpath(path, root), line_number, problem))
    if failures:
        print("\n%d forbidden reference(s) in %d file(s)." % (failures, scanned))
        return 1
    print("%d file(s) scanned, no server vocabulary found." % scanned)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
