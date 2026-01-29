"""Build service catalog and endpoint flows."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import re


ATTR_PATTERN = r"\[(?:[^\]\"']+|\"[^\"]*\"|'[^']*')+\]"
HTTP_VERB_PATTERN = re.compile(
    r"\[(HttpGet|HttpPost|HttpPut|HttpDelete|HttpPatch|HttpHead|HttpOptions)\b",
    re.IGNORECASE,
)
ROUTE_PATTERN = re.compile(r'\[Route\(\s*"([^"]+)"\s*\)\]', re.IGNORECASE)
HTTP_ROUTE_PATTERN = re.compile(
    r"\[Http(?:Get|Post|Put|Delete|Patch|Head|Options)\(\s*\"([^\"]*)\"\s*\)\]",
    re.IGNORECASE,
)


def build_service_catalog(
    files: List[Dict[str, Any]],
    dependency_analyzer: Optional[Any] = None,
) -> Dict[str, Any]:
    controllers = []
    services = []
    interfaces = []
    endpoints = []
    class_map: Dict[str, List[str]] = {}
    endpoint_bodies: Dict[str, str] = {}
    consumer_map = _build_consumer_message_map(files)

    for file_info in files:
        language = (file_info.get("language") or "").lower()
        if language != "csharp":
            continue
        path = file_info.get("relative_path") or file_info.get("path", "")
        content = file_info.get("content", "") or ""
        parsed = _parse_csharp_classes_and_endpoints(content)
        class_map[path] = parsed["classes"]
        controllers.extend(parsed["controllers"])
        endpoints.extend(parsed["endpoints"])
        endpoint_bodies.update(parsed.get("endpoint_bodies", {}))
        services.extend([c for c in parsed["classes"] if c.endswith("Service") or c.endswith("Repository")])
        interfaces.extend([c for c in parsed["classes"] if c.startswith("I") and len(c) > 1])

    flow_graph, controller_dependencies = _build_controller_flow_graph(
        controllers, class_map, dependency_analyzer
    )
    endpoint_flows = _build_endpoint_flows(endpoints, endpoint_bodies, consumer_map)
    api_spec = _build_api_spec(endpoints, controller_dependencies, endpoint_flows)
    endpoint_sequence_diagrams = _build_endpoint_sequence_diagrams(
        endpoints, controller_dependencies, endpoint_flows
    )

    return {
        "controllers": controllers,
        "services": sorted(set(services)),
        "interfaces": sorted(set(interfaces)),
        "endpoints": endpoints,
        "flow_graph": flow_graph,
        "controller_dependencies": controller_dependencies,
        "endpoint_flows": endpoint_flows,
        "api_spec": api_spec,
        "endpoint_sequence_diagrams": endpoint_sequence_diagrams,
    }


def _parse_csharp_classes_and_endpoints(code: str) -> Dict[str, Any]:
    controllers = []
    endpoints = []
    classes = []
    endpoint_bodies: Dict[str, str] = {}

    class_pattern = re.compile(
        r"(?P<attrs>(?:" + ATTR_PATTERN + r"\s*)*)"
        r"(?:public|private|internal|protected|abstract|sealed|static|partial)?\s*"
        r"class\s+(?P<name>\w+)(?:\s*:\s*[\w,\s<>]+)?\s*\{",
        re.MULTILINE,
    )

    for match in class_pattern.finditer(code):
        class_name = match.group("name")
        classes.append(class_name)
        attrs = match.group("attrs") or ""
        body = _extract_balanced_braces(code, match.end() - 1)
        if not body:
            continue

        class_route = _extract_route(attrs)
        class_route = _resolve_controller_token(class_route, class_name)
        is_controller = class_name.endswith("Controller") or "ApiController" in attrs

        if is_controller:
            controllers.append(
                {
                    "name": class_name,
                    "route": class_route,
                }
            )

        for method in _extract_csharp_methods_with_attributes(body):
            verbs = _extract_http_verbs(method["attrs"])
            if not verbs:
                continue
            method_route = _extract_route(method["attrs"])
            full_route = _join_routes(class_route, method_route)
            endpoint_key = f"{class_name}.{method['name']}"
            endpoint_bodies[endpoint_key] = method.get("body", "")
            endpoints.append(
                {
                    "controller": class_name,
                    "method": method["name"],
                    "http_verbs": verbs,
                    "route": full_route or "",
                }
            )

    return {
        "controllers": controllers,
        "endpoints": endpoints,
        "classes": classes,
        "endpoint_bodies": endpoint_bodies,
    }


def _extract_csharp_methods_with_attributes(class_body: str) -> List[Dict[str, str]]:
    methods = []
    pattern = re.compile(
        r"(?P<attrs>(?:" + ATTR_PATTERN + r"\s*)*)"
        r"(?P<signature>(?:public|private|internal|protected)[^{;]*\{)",
        re.MULTILINE,
    )
    for match in pattern.finditer(class_body):
        signature = match.group("signature")
        name_match = re.search(r"(\w+)\s*\(", signature)
        if not name_match:
            continue
        name = name_match.group(1)
        body = _extract_balanced_braces(class_body, match.end() - 1)
        methods.append(
            {
                "name": name,
                "attrs": match.group("attrs") or "",
                "body": body,
            }
        )
    return methods


def _build_endpoint_flows(
    endpoints: List[Dict[str, Any]],
    endpoint_bodies: Dict[str, str],
    consumer_map: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    flows = []
    for endpoint in endpoints:
        key = f"{endpoint.get('controller')}.{endpoint.get('method')}"
        body = endpoint_bodies.get(key, "")
        steps, messages = _infer_endpoint_steps(body)
        consumers = []
        for message in messages:
            consumers.extend(consumer_map.get(message, []))
        for cons in consumers:
            steps.append(f"Consumer {cons['consumer']} reads queue")
            if cons.get("reads_db"):
                steps.append(f"Consumer {cons['consumer']} reads DB")
        flows.append(
            {
                "controller": endpoint.get("controller"),
                "method": endpoint.get("method"),
                "http_verbs": endpoint.get("http_verbs", []),
                "route": endpoint.get("route", ""),
                "steps": steps,
            }
        )
    return flows


def _build_api_spec(
    endpoints: List[Dict[str, Any]],
    controller_dependencies: Dict[str, List[str]],
    endpoint_flows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    spec_rows = []
    flow_lookup = {
        f"{flow.get('controller')}.{flow.get('method')}": flow for flow in endpoint_flows
    }
    for endpoint in endpoints:
        controller = endpoint.get("controller")
        method = endpoint.get("method")
        key = f"{controller}.{method}"
        deps = controller_dependencies.get(controller, []) if controller else []
        flow = flow_lookup.get(key, {})
        steps = flow.get("steps", [])
        components = [controller] if controller else []
        components.extend([dep for dep in deps if dep])
        spec_rows.append(
            {
                "controller": controller,
                "method": method,
                "http_verbs": endpoint.get("http_verbs", []),
                "route": endpoint.get("route", ""),
                "components": components,
                "steps": steps,
            }
        )
    return spec_rows


def _build_endpoint_sequence_diagrams(
    endpoints: List[Dict[str, Any]],
    controller_dependencies: Dict[str, List[str]],
    endpoint_flows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    diagrams = []
    flow_lookup = {
        f"{flow.get('controller')}.{flow.get('method')}": flow for flow in endpoint_flows
    }
    for endpoint in endpoints:
        controller = endpoint.get("controller")
        method = endpoint.get("method")
        key = f"{controller}.{method}"
        deps = controller_dependencies.get(controller, []) if controller else []
        flow = flow_lookup.get(key, {})
        verb = ", ".join(endpoint.get("http_verbs", []) or [])
        route = endpoint.get("route") or ""
        label = f"{verb} {route}".strip()
        mermaid = _render_endpoint_sequence(
            controller, deps, label or "Request", flow.get("steps", [])
        )
        diagrams.append(
            {
                "controller": controller,
                "method": method,
                "http_verbs": endpoint.get("http_verbs", []),
                "route": route,
                "components": [controller] + deps if controller else deps,
                "mermaid": mermaid,
            }
        )
    return diagrams


def _render_endpoint_sequence(
    controller: Optional[str],
    dependencies: List[str],
    request_label: str,
    steps: List[str],
) -> str:
    lines = ["```mermaid", "sequenceDiagram", "  participant Client"]
    if controller:
        lines.append(f"  participant {_safe_id(controller)}")
    for dep in dependencies:
        lines.append(f"  participant {_safe_id(dep)}")
    if controller:
        lines.append(f"  Client->>{_safe_id(controller)}: {request_label}")
        for dep in dependencies:
            lines.append(f"  {_safe_id(controller)}->>{_safe_id(dep)}: Call")
            lines.append(f"  {_safe_id(dep)}-->>{_safe_id(controller)}: Result")
        if steps:
            note = " | ".join(step for step in steps if step)
            if note:
                lines.append(f"  Note over {_safe_id(controller)}: {note}")
        lines.append(f"  {_safe_id(controller)}-->>Client: Response")
    else:
        lines.append("  Client->>Service: Request")
        lines.append("  Service-->>Client: Response")
    lines.append("```")
    return "\n".join(lines)


def _infer_endpoint_steps(body: str) -> tuple[List[str], List[str]]:
    steps: List[str] = []
    messages: List[str] = []
    if not body:
        return steps, messages
    var_types: Dict[str, str] = {}
    for match in re.finditer(r"\bvar\s+(\w+)\s*=\s*new\s+([\w\.]+)\s*\(", body):
        var_types[match.group(1)] = match.group(2)
    for match in re.finditer(r"\b([\w\.]+)\s+(\w+)\s*=\s*new\s+([\w\.]+)\s*\(", body):
        declared_type = match.group(1)
        constructed_type = match.group(3)
        resolved_type = constructed_type if declared_type.lower() == "var" else declared_type
        var_types[match.group(2)] = resolved_type
    if re.search(r"Guid\.NewGuid\(|new\s+Guid\(", body):
        steps.append("Generate OrderId")
    if re.search(r"\bSaveChanges(?:Async)?\(", body) or re.search(r"\b(Add|AddAsync|Insert|Update)\b", body):
        steps.append("Insert/Update DB")
    publish_matches = re.findall(r"\.Publish<\s*([\w\.]+)\s*>|\bPublish\(\s*new\s+([\w\.]+)", body)
    send_matches = re.findall(r"\.Send<\s*([\w\.]+)\s*>|\bSend\(\s*new\s+([\w\.]+)", body)
    for match in publish_matches + send_matches:
        msg = match[0] or match[1]
        if msg:
            messages.append(msg)
            steps.append(f"Publish/Send {msg} to queue")
    for match in re.finditer(r"\bPublish\(\s*(\w+)\s*\)|\bSend\(\s*(\w+)\s*\)", body):
        var_name = match.group(1) or match.group(2)
        msg = var_types.get(var_name)
        if msg and msg not in messages:
            messages.append(msg)
            steps.append(f"Publish/Send {msg} to queue")
    if re.search(r"GetSendEndpoint\(", body):
        steps.append("Send to queue endpoint")
    return steps, messages


def _build_consumer_message_map(files: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    consumer_pattern = re.compile(r"class\s+(\w+)\s*:\s*[^{\n]*IConsumer<\s*([\w\.]+)\s*>")
    consumer_map: Dict[str, List[Dict[str, Any]]] = {}
    for file_info in files:
        language = (file_info.get("language") or "").lower()
        if language != "csharp":
            continue
        content = file_info.get("content", "") or ""
        reads_db = "DbContext" in content or "DbSet" in content or "SaveChanges" in content
        for match in consumer_pattern.finditer(content):
            consumer = match.group(1)
            message = match.group(2)
            consumer_map.setdefault(message, [])
            consumer_map[message].append(
                {"consumer": consumer, "reads_db": reads_db}
            )
    return consumer_map


def _extract_http_verbs(attrs: str) -> List[str]:
    verbs = set()
    for match in HTTP_VERB_PATTERN.finditer(attrs or ""):
        name = match.group(1) or ""
        verb = re.sub(r"^Http", "", name, flags=re.IGNORECASE).upper()
        if verb:
            verbs.add(verb)
    return sorted(verbs)


def _extract_route(attrs: str) -> str:
    match = ROUTE_PATTERN.search(attrs or "")
    if match:
        return match.group(1)
    http_match = HTTP_ROUTE_PATTERN.search(attrs or "")
    return http_match.group(1) if http_match else ""


def _join_routes(base: str, sub: str) -> str:
    if not base:
        return sub or ""
    if not sub:
        return base or ""
    return f"{base.rstrip('/')}/{sub.lstrip('/')}"


def _resolve_controller_token(route: str, class_name: str) -> str:
    if not route or "[controller]" not in route.lower():
        return route or ""
    name = class_name
    if class_name.lower().endswith("controller"):
        name = class_name[: -len("Controller")]
    token = name.lower() if name else class_name.lower()
    return re.sub(r"\[controller\]", token, route, flags=re.IGNORECASE)


def _build_controller_flow_graph(
    controllers: List[Dict[str, Any]],
    class_map: Dict[str, List[str]],
    dependency_analyzer: Optional[Any],
) -> tuple[Optional[str], Dict[str, List[str]]]:
    if not dependency_analyzer or not controllers:
        return None, {}

    lines = ["```mermaid", "graph LR"]
    edges_added = set()
    controller_dependencies: Dict[str, List[str]] = {}

    # Build a lookup from controller name to file path
    controller_files = {}
    for file_path, classes in class_map.items():
        for cls in classes:
            if cls.endswith("Controller"):
                controller_files[cls] = file_path

    for controller in controllers:
        name = controller["name"]
        file_path = controller_files.get(name)
        if not file_path:
            continue
        deps = dependency_analyzer.dependencies.get(file_path, set())
        for dep_path in deps:
            dep_classes = class_map.get(dep_path, [])
            for dep_class in dep_classes:
                if dep_class.endswith(("Service", "Repository", "Consumer", "Handler")) or dep_class.startswith("I"):
                    controller_dependencies.setdefault(name, [])
                    if dep_class not in controller_dependencies[name]:
                        controller_dependencies[name].append(dep_class)
                    src_id = _safe_id(name)
                    dst_id = _safe_id(dep_class)
                    edge_key = f"{src_id}->{dst_id}"
                    if edge_key in edges_added:
                        continue
                    lines.append(f'  {src_id}["{name}"] --> {dst_id}["{dep_class}"]')
                    edges_added.add(edge_key)

    lines.append("```")
    return ("\n".join(lines) if edges_added else None), controller_dependencies


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
