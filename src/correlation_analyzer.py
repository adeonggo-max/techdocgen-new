"""Build correlation signals and diagrams across stacks."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import re


def _normalize_lookup_path(path_str: str) -> str:
    if not path_str:
        return ""
    try:
        return Path(path_str).as_posix()
    except Exception:
        return str(path_str).replace("\\", "/")


def _extract_js_ts_imports(code: str) -> List[str]:
    imports = re.findall(r'import\s+(?:[\w*\s{},]+)\s+from\s+[\'"]([^\'"]+)[\'"]', code)
    requires = re.findall(r'require\(\s*[\'"]([^\'"]+)[\'"]\s*\)', code)
    return imports + requires


def _extract_csharp_usings(code: str) -> List[str]:
    return re.findall(r'using\s+([\w\.]+)\s*;', code)


def _find_keyword_matches(values: List[str], keywords: List[str]) -> List[str]:
    matches = set()
    for value in values:
        value_lower = value.lower()
        for keyword in keywords:
            if keyword in value_lower:
                matches.add(keyword)
    return sorted(matches)


def build_correlation_signals(
    source_files: List[Dict[str, Any]],
    dep_map: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build cross-stack correlation signals for .NET, RabbitMQ, Node.js, and Angular."""
    csharp_keywords = [
        "masstransit",
        "rabbitmq",
        "rabbitmq.client",
        "masstransit.rabbitmq",
    ]
    node_keywords = [
        "amqplib",
        "amqp-connection-manager",
        "rascal",
        "@golevelup/nestjs-rabbitmq",
        "@nestjs/microservices",
        "rabbitmq",
    ]

    external_deps = dep_map.get("external_dependencies", {}) if dep_map else {}

    csharp_messaging = []
    node_messaging = []
    angular_files = []

    for file_info in source_files or []:
        raw_path = file_info.get("relative_path") or file_info.get("path", "")
        lookup_path = _normalize_lookup_path(raw_path)
        language = (file_info.get("language") or "").lower()
        content = file_info.get("content", "") or ""

        values: List[str] = []
        values.extend(external_deps.get(lookup_path, []))

        if language in ["javascript", "typescript"]:
            values.extend(_extract_js_ts_imports(content))
        if language in ["csharp", "vbnet", "fsharp"]:
            values.extend(_extract_csharp_usings(content))

        if language in ["csharp", "vbnet", "fsharp"]:
            matches = _find_keyword_matches(values, csharp_keywords)
            if matches:
                csharp_messaging.append({"file": raw_path, "matches": matches})

        if language in ["javascript", "typescript"]:
            matches = _find_keyword_matches(values, node_keywords)
            if matches:
                node_messaging.append({"file": raw_path, "matches": matches})

        if language in ["typescript", "javascript", "markup"]:
            if any("@angular/" in value.lower() for value in values) or "/src/app/" in lookup_path.lower():
                angular_files.append({"file": raw_path})

    return {
        "csharp_messaging": csharp_messaging,
        "node_messaging": node_messaging,
        "angular_files": angular_files,
    }


def build_correlation_mermaid(correlation: Dict[str, Any]) -> Optional[str]:
    """Build a Mermaid correlation graph for cross-stack signals."""
    if not correlation:
        return None
    csharp = correlation.get("csharp_messaging", [])
    node = correlation.get("node_messaging", [])
    angular = correlation.get("angular_files", [])

    if not (csharp or node or angular):
        return None

    lines = ["```mermaid", "graph LR"]
    if csharp:
        lines.append(f'  DOTNET[".NET Services ({len(csharp)})"]')
    if node:
        lines.append(f'  NODE["Node.js Services ({len(node)})"]')
    if angular:
        lines.append(f'  ANGULAR["Angular UI ({len(angular)})"]')

    if csharp or node:
        lines.append('  MQ["RabbitMQ / Messaging"]')

    if csharp:
        lines.append("  DOTNET --> MQ")
    if node:
        lines.append("  NODE --> MQ")
    if angular and node:
        lines.append("  ANGULAR --> NODE")
    elif angular and not node:
        lines.append("  ANGULAR --> MQ")

    lines.append("```")
    return "\n".join(lines)
