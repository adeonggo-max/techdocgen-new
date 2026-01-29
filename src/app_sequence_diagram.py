"""Generate a high-level app interaction sequence diagram."""

from typing import Dict, Any, List, Optional
import re


def build_app_sequence_diagram(
    service_catalog: Dict[str, Any],
    messaging_flows: List[Dict[str, Any]],
    message_types: Optional[List[Dict[str, str]]] = None,
) -> Optional[str]:
    """Build a Mermaid sequence diagram for app interaction flow."""
    controllers = [c.get("name") for c in service_catalog.get("controllers", []) if c.get("name")]
    services = service_catalog.get("services", []) or []
    interfaces = service_catalog.get("interfaces", []) or []

    controller = controllers[0] if controllers else None
    other_controllers = [c for c in controllers[1:] if c]
    service = services[0] if services else (interfaces[0] if interfaces else None)
    endpoints = service_catalog.get("endpoints", []) or []
    endpoint_flows = service_catalog.get("endpoint_flows", []) or []
    controller_deps = service_catalog.get("controller_dependencies", {}) or {}
    flow_lookup = {
        f"{flow.get('controller')}.{flow.get('method')}": flow for flow in endpoint_flows
    }

    queue = None
    consumer = None
    for flow in messaging_flows or []:
        if flow.get("queue"):
            queue = flow.get("queue")
            if flow.get("consumers"):
                consumer = flow.get("consumers")[0]
            break

    flow_consumers = _collect_flow_consumers(endpoint_flows)
    if not queue and flow_consumers:
        queue = "RabbitMQ"

    if not controller and not service and not queue:
        return None

    lines = ["```mermaid", "sequenceDiagram"]
    lines.append("  participant Client")
    if controller:
        lines.append(f"  participant { _safe_id(controller) }")
    if queue:
        lines.append(f"  participant { _safe_id(queue) }")
    for cons in flow_consumers:
        lines.append(f"  participant { _safe_id(cons) }")
    for ctrl in other_controllers:
        lines.append(f"  participant { _safe_id(ctrl) }")
    if service and not controller:
        lines.append(f"  participant { _safe_id(service) }")

    if endpoints:
        # Show up to 5 endpoints to keep diagram readable
        for endpoint in endpoints[:5]:
            verb = ", ".join(endpoint.get("http_verbs", []) or [])
            route = endpoint.get("route") or ""
            label = f"{verb} {route}".strip()
            target = endpoint.get("controller") or controller or service
            if target:
                lines.append(
                    f"  Client->>{_safe_id(target)}: {_safe_message(label or 'Request')}"
                )
                dep_list = controller_deps.get(target, [])
                service_dep = _pick_dep(dep_list, ("Service", "Handler"))
                repo_dep = _pick_dep(dep_list, ("Repository", "DbContext"))
                if service_dep:
                    lines.append(
                        f"  {_safe_id(target)}->>{_safe_id(service_dep)}: {_safe_message('Handle')}"
                    )
                    if repo_dep:
                        lines.append(
                            f"  {_safe_id(service_dep)}->>{_safe_id(repo_dep)}: {_safe_message('Query/Save')}"
                        )
                        lines.append(
                            f"  {_safe_id(repo_dep)}-->>{_safe_id(service_dep)}: {_safe_message('Result')}"
                        )
                    lines.append(
                        f"  {_safe_id(service_dep)}-->>{_safe_id(target)}: {_safe_message('Result')}"
                    )
                elif service and target != service:
                    lines.append(
                        f"  {_safe_id(target)}->>{_safe_id(service)}: {_safe_message('Handle')}"
                    )
                    lines.append(
                        f"  {_safe_id(service)}-->>{_safe_id(target)}: {_safe_message('Result')}"
                    )
                flow = flow_lookup.get(f"{endpoint.get('controller')}.{endpoint.get('method')}", {})
                messages, consumers = _extract_flow_messages_and_consumers(flow.get("steps", []))
                if queue:
                    for msg in messages:
                        lines.append(
                            f"  {_safe_id(target)}->>{_safe_id(queue)}: {_safe_message(f'Publish Send {msg}')}"
                        )
                        for cons in consumers:
                            lines.append(
                                f"  {_safe_id(queue)}-->>{_safe_id(cons)}: {_safe_message(f'Consume {msg}')}"
                            )
                else:
                    for msg in messages:
                        for cons in consumers:
                            lines.append(
                                f"  {_safe_id(target)}->>{_safe_id(cons)}: {_safe_message(f'Publish Send {msg}')}"
                            )
                lines.append(f"  {_safe_id(target)}-->>Client: {_safe_message('Response')}")
    elif controller:
        lines.append(f"  Client->>{_safe_id(controller)}: {_safe_message('Request')}")
        if service:
            lines.append(
                f"  {_safe_id(controller)}->>{_safe_id(service)}: {_safe_message('Handle')}"
            )
            lines.append(
                f"  {_safe_id(service)}-->>{_safe_id(controller)}: {_safe_message('Result')}"
            )
        lines.append(f"  {_safe_id(controller)}-->>Client: {_safe_message('Response')}")
    elif service:
        lines.append(f"  Client->>{_safe_id(service)}: {_safe_message('Request')}")
        lines.append(f"  {_safe_id(service)}-->>Client: {_safe_message('Response')}")

    if queue and not flow_consumers:
        sender = _safe_id(service) if service else _safe_id(controller)
        message_name = None
        for msg in message_types or []:
            if msg.get("message"):
                message_name = msg["message"]
                break
        label = f"Publish/Send {message_name}" if message_name else "Publish/Send"
        lines.append(f"  {sender}->>{_safe_id(queue)}: {_safe_message(label)}")
        if consumer:
            lines.append(f"  {_safe_id(queue)}-->>{_safe_id(consumer)}: {_safe_message('Consume')}")
            lines.append(f"  {_safe_id(consumer)}-->>{_safe_id(queue)}: {_safe_message('Ack')}")

    lines.append("```")
    return "\n".join(lines)


def _safe_id(value: str) -> str:
    return re.sub(r"[^\w]", "_", value)[:50] or "node"


def _pick_dep(deps: List[str], suffixes: tuple) -> Optional[str]:
    for dep in deps:
        if dep.endswith(suffixes):
            return dep
    return None


def _safe_message(label: str) -> str:
    cleaned = (label or "").replace("\n", " ").strip()
    cleaned = re.sub(r"[\"<>`]", "", cleaned)
    cleaned = cleaned.replace("/", " ").replace("\\", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        cleaned = "Message"
    return cleaned


def _collect_flow_consumers(endpoint_flows: List[Dict[str, Any]]) -> List[str]:
    consumers = set()
    for flow in endpoint_flows:
        _, flow_consumers = _extract_flow_messages_and_consumers(flow.get("steps", []))
        for cons in flow_consumers:
            consumers.add(cons)
    return sorted(consumers)


def _extract_flow_messages_and_consumers(steps: List[str]) -> tuple[List[str], List[str]]:
    messages = []
    consumers = []
    for step in steps or []:
        if not step:
            continue
        msg_match = re.search(r"Publish/Send\s+([^\s]+)", step)
        if msg_match:
            messages.append(msg_match.group(1))
        cons_match = re.search(r"Consumer\s+([^\s]+)\s+reads queue", step)
        if cons_match:
            consumers.append(cons_match.group(1))
    return messages, consumers
