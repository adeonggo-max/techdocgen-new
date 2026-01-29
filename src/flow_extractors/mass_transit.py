"""MassTransit flow extractor for RabbitMQ"""

import re
from typing import Dict, List, Any


class MassTransitFlowExtractor:
    """Extract queues, consumers, and producers from MassTransit configuration"""
    
    RECEIVE_ENDPOINT_PATTERN = re.compile(r'ReceiveEndpoint\s*\(\s*[\'"]([^\'"]+)[\'"]')
    CONSUMER_PATTERN = re.compile(r'Consumer<\s*([\w\.]+)\s*>')
    SAGA_PATTERN = re.compile(r'(?:Saga|StateMachineSaga)<\s*([\w\.]+)\s*>')
    PUBLISH_PATTERN = re.compile(r'\.Publish<\s*([\w\.]+)\s*>|\bPublish\(\s*new\s+([\w\.]+)')
    SEND_PATTERN = re.compile(r'\.Send<\s*([\w\.]+)\s*>|\bSend\(\s*new\s+([\w\.]+)')
    SEND_ENDPOINT_PATTERN = re.compile(r'GetSendEndpoint\(\s*new\s+Uri\(\s*[\'"]([^\'"]+)[\'"]')
    CONSUMER_CLASS_PATTERN = re.compile(r'class\s+(\w+)\s*:\s*[^{\n]*IConsumer<\s*([\w\.]+)\s*>')
    CONFIGURE_CONSUMER_PATTERN = re.compile(r'ConfigureConsumer<\s*([\w\.]+)\s*>')
    
    def extract(self, code: str) -> Dict[str, Any]:
        """Extract MassTransit flows from C# code"""
        queues = self._extract_receive_endpoints(code)
        publishes = self._extract_messages(code, self.PUBLISH_PATTERN)
        sends = self._extract_messages(code, self.SEND_PATTERN)
        send_endpoints = self._extract_send_endpoints(code)
        consumer_messages = self._extract_consumer_messages(code)
        
        flows = []
        for queue in queues:
            flows.append({
                "queue": queue["queue"],
                "consumers": queue["consumers"],
                "sagas": queue["sagas"]
            })
        
        return {
            "queues": queues,
            "flows": flows,
            "publishes": publishes,
            "sends": sends,
            "send_endpoints": send_endpoints,
            "consumer_messages": consumer_messages
        }
    
    def _extract_receive_endpoints(self, code: str) -> List[Dict[str, Any]]:
        """Extract ReceiveEndpoint blocks"""
        endpoints = []
        for match in self.RECEIVE_ENDPOINT_PATTERN.finditer(code):
            queue_name = match.group(1)
            block = self._extract_block_after(match.end(), code)
            consumers = self.CONSUMER_PATTERN.findall(block)
            consumers += self.CONFIGURE_CONSUMER_PATTERN.findall(block)
            sagas = self.SAGA_PATTERN.findall(block)
            endpoints.append({
                "queue": queue_name,
                "consumers": sorted(set(consumers)),
                "sagas": sorted(set(sagas))
            })
        return endpoints
    
    def _extract_messages(self, code: str, pattern: re.Pattern) -> List[str]:
        """Extract message types from Publish/Send calls"""
        messages = []
        for match in pattern.finditer(code):
            msg_type = match.group(1) or match.group(2)
            if msg_type:
                messages.append(msg_type)
        return sorted(set(messages))
    
    def _extract_send_endpoints(self, code: str) -> List[str]:
        """Extract SendEndpoint URIs (queue/topic names)"""
        endpoints = []
        for match in self.SEND_ENDPOINT_PATTERN.finditer(code):
            uri = match.group(1)
            normalized = self._normalize_queue_uri(uri)
            endpoints.append(normalized)
        return sorted(set(endpoints))

    def _extract_consumer_messages(self, code: str) -> List[Dict[str, str]]:
        """Extract message types consumed by IConsumer<T> implementations"""
        consumers = []
        for match in self.CONSUMER_CLASS_PATTERN.finditer(code):
            consumers.append({
                "consumer": match.group(1),
                "message": match.group(2)
            })
        return consumers

    def _normalize_queue_uri(self, uri: str) -> str:
        if uri.startswith("queue:"):
            return uri
        if "queue:" in uri:
            return "queue:" + uri.split("queue:", 1)[1]
        if "rabbitmq://" in uri:
            # Use last path segment as queue
            parts = uri.split("/")
            if parts:
                queue_name = parts[-1]
                return f"queue:{queue_name}"
        return uri
    
    def _extract_block_after(self, start_pos: int, code: str) -> str:
        """Extract block after ReceiveEndpoint call (best-effort)"""
        brace_pos = code.find("{", start_pos)
        if brace_pos == -1:
            return ""
        depth = 0
        end_pos = brace_pos
        for i in range(brace_pos, len(code)):
            if code[i] == "{":
                depth += 1
            elif code[i] == "}":
                depth -= 1
                if depth == 0:
                    end_pos = i + 1
                    break
        return code[brace_pos:end_pos]
