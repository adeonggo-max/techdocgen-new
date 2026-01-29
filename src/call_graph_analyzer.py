"""Extract intra-class call graphs from source code."""

from typing import Dict, List, Any
import re


KEYWORDS = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "using",
    "return",
    "new",
    "throw",
    "lock",
    "foreach",
    "await",
}


def build_csharp_class_call_graphs(code: str) -> List[Dict[str, Any]]:
    """Build call graphs for methods within each C# class."""
    graphs: List[Dict[str, Any]] = []
    class_pattern = re.compile(
        r"(?:public|private|internal|protected|abstract|sealed|static|partial)?\s*"
        r"class\s+(\w+)(?:\s*:\s*[\w,\s<>]+)?\s*\{",
        re.MULTILINE,
    )

    for match in class_pattern.finditer(code):
        class_name = match.group(1)
        class_body = _extract_balanced_braces(code, match.end() - 1)
        if not class_body:
            continue

        methods = _extract_csharp_methods_with_bodies(class_body, class_name)
        if not methods:
            continue

        method_names = {m["name"] for m in methods}
        edges = []
        for method in methods:
            called = _extract_method_calls(method["body"], method_names)
            for callee in sorted(called):
                edges.append((method["name"], callee))

        if not edges:
            continue

        mermaid = _build_mermaid_for_class(class_name, edges)
        graphs.append(
            {
                "class": class_name,
                "edges": edges,
                "mermaid": mermaid,
            }
        )

    return graphs


def _extract_csharp_methods_with_bodies(code: str, class_name: str) -> List[Dict[str, str]]:
    methods: List[Dict[str, str]] = []
    pattern = re.compile(
        r"(?:public|private|internal|protected|static|virtual|override|abstract|async)?\s*"
        r"(?:[\w<>,\s\[\]]+\s+)?(\w+)\s*\([^)]*\)\s*\{",
        re.MULTILINE,
    )
    for match in pattern.finditer(code):
        method_name = match.group(1)
        if method_name in KEYWORDS or method_name == class_name:
            continue
        body = _extract_balanced_braces(code, match.end() - 1)
        if not body:
            continue
        methods.append({"name": method_name, "body": body})
    return methods


def _extract_method_calls(body: str, method_names: set) -> set:
    calls = set()
    for match in re.finditer(r"\b(\w+)\s*\(", body):
        name = match.group(1)
        if name in method_names and name not in KEYWORDS:
            calls.add(name)
    return calls


def _build_mermaid_for_class(class_name: str, edges: List[tuple]) -> str:
    lines = ["```mermaid", "graph TD"]
    for src, dst in edges:
        src_id = _safe_id(f"{class_name}.{src}")
        dst_id = _safe_id(f"{class_name}.{dst}")
        lines.append(f'  {src_id}["{class_name}.{src}"] --> {dst_id}["{class_name}.{dst}"]')
    lines.append("```")
    return "\n".join(lines)


def _safe_id(value: str) -> str:
    return re.sub(r"[^\w]", "_", value)[:50] or "node"


def _extract_balanced_braces(code: str, start_pos: int) -> str:
    if start_pos >= len(code) or code[start_pos] != "{":
        return ""
    depth = 0
    end_pos = start_pos
    for i in range(start_pos, len(code)):
        if code[i] == "{":
            depth += 1
        elif code[i] == "}":
            depth -= 1
            if depth == 0:
                end_pos = i + 1
                break
    return code[start_pos:end_pos]
