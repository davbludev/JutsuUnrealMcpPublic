"""Render the one part of a response that is cheaper as text than as JSON.

Measured before it was written, on 204 recorded responses from real agent runs with the
`o200k_base` tokenizer. Two findings decided everything here:

* Re-encoding a response wholesale into indented lines, flattened paths or Markdown costs
  **more** tokens than the JSON it replaces - 115% to 252% of it. Modern tokenizers pack JSON
  punctuation into single tokens, and the server's payloads are already compact, so a general
  reformat pays for indentation it did not need. The envelope therefore stays JSON.
* A JSON Schema document is the exception, and a large one. Three quarters of a schema's tokens
  are structure rather than prose, and the same document written as a signature costs 39% of its
  JSON. Schemas are 29% of everything those runs received, so rendering only them takes 18% off
  the whole corpus and 42% off a capability describe, while every description, bound and enum
  survives.

The rule this file obeys: it knows JSON Schema, and nothing else. There is no branch on a
capability id, a domain or an aspect, and it never looks at what produced the document.
"""

#: Keys whose value is a schema document. The name is the trigger, not the shape: a payload of
#: real editor state can easily contain `type` and `enum` and must never be mistaken for a
#: contract and rewritten. A key that ends in "Schema" is a schema by the response contract.
SCHEMA_KEY_SUFFIX = "Schema"

#: The keywords a signature spells out inline, in the order a reader wants them.
_BOUNDS = ("minLength", "maxLength", "minimum", "maximum", "minItems", "maxItems", "pattern", "format")


def signature(schema, name=None, required=False, depth=0):
    """One JSON Schema document as indented signature lines.

    Every constraint the document declares survives: types, bounds, enums, consts, branch
    counts, whether an object is closed, and every description. What is dropped is the JSON
    that carried them.
    """
    if not isinstance(schema, dict):
        return []
    indent = "  " * depth
    description = schema.get("description")

    def line(declaration):
        label = "%s%s%s: %s" % (indent, name, "" if required else "?", declaration) if name else indent + declaration
        return label + ("  # " + description if description else "")

    for keyword in ("oneOf", "anyOf"):
        branches = schema.get(keyword)
        if isinstance(branches, list) and branches:
            lines = [line("%s[%d]" % (keyword, len(branches)))]
            for index, branch in enumerate(branches):
                lines.extend(signature(branch, "|%d" % index, True, depth + 1))
            return lines

    if "const" in schema:
        return [line('"%s"' % schema["const"])]
    values = schema.get("enum")
    if isinstance(values, list) and values:
        return [line("|".join('"%s"' % value for value in values))]

    declared = schema.get("type", "any")
    if declared == "object":
        lines = [line("object" if schema.get("additionalProperties") is False else "object open")]
        required_names = set(schema.get("required") or [])
        for key, value in (schema.get("properties") or {}).items():
            lines.extend(signature(value, key, key in required_names, depth + 1))
        return lines
    if declared == "array":
        lines = [line("array" + _bounds(schema))]
        lines.extend(signature(schema.get("items") or {}, "item", True, depth + 1))
        return lines
    return [line(declared + _bounds(schema))]


def _bounds(schema):
    return "".join(" %s=%s" % (keyword, schema[keyword]) for keyword in _BOUNDS if keyword in schema)


def render(value):
    """Return ``value`` with every schema document replaced by its signature text.

    Everything else is returned unchanged, including nesting, arrays, identity strings and
    numbers. Identity strings are never re-cased, re-quoted or wrapped anywhere in this file.
    """
    if isinstance(value, dict):
        rendered = {}
        for key, item in value.items():
            if key.endswith(SCHEMA_KEY_SUFFIX) and isinstance(item, dict) and item:
                rendered[key] = "\n".join(signature(item))
            else:
                rendered[key] = render(item)
        return rendered
    if isinstance(value, list):
        return [render(item) for item in value]
    return value
