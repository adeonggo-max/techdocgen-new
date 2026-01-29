"""Dependency analyzer for identifying and mapping code dependencies"""

from typing import Dict, List, Any, Set, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import json


class DependencyAnalyzer:
    """Analyzes dependencies between code files and creates dependency maps"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.file_index: Dict[str, Dict[str, Any]] = {}  # Maps file paths to file info
        self.class_index: Dict[str, str] = {}  # Maps class names to file paths
        self.package_index: Dict[str, List[str]] = defaultdict(list)  # Maps packages to file paths
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)  # Maps file paths to dependent file paths
        self.external_dependencies: Dict[str, Set[str]] = defaultdict(set)  # External imports
    
    def analyze_files(self, files: List[Dict[str, Any]], parsers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze all files and build dependency map
        
        Args:
            files: List of file dictionaries with 'path', 'content', 'language' keys
            parsers: Dictionary of language parsers
            
        Returns:
            Dictionary containing dependency map and analysis results
        """
        # First pass: Index all files, classes, and packages
        self._build_index(files, parsers)
        
        # Second pass: Resolve dependencies
        self._resolve_dependencies(files, parsers)
        
        # Build dependency graph
        dependency_map = self._build_dependency_map()
        
        return {
            "dependency_map": dependency_map,
            "file_count": len(self.file_index),
            "class_count": len(self.class_index),
            "dependency_count": sum(len(deps) for deps in self.dependencies.values()),
            "external_dependency_count": sum(len(deps) for deps in self.external_dependencies.values()),
            "circular_dependencies": self._detect_circular_dependencies(),
            "orphaned_files": self._find_orphaned_files(),
            "highly_coupled_files": self._find_highly_coupled_files()
        }
    
    def _normalize_path(self, path_str: str) -> str:
        """Normalize path to use forward slashes consistently"""
        if not path_str:
            return ""
        # Convert to Path and use as_posix() to normalize separators
        try:
            return Path(path_str).as_posix()
        except:
            # Fallback: just replace backslashes with forward slashes
            return str(path_str).replace('\\', '/')
    
    def _build_index(self, files: List[Dict[str, Any]], parsers: Dict[str, Any]):
        """Build indexes for files, classes, and packages"""
        for file_info in files:
            file_path = file_info.get('path', '')
            relative_path = file_info.get('relative_path', file_path)
            # Normalize paths to use forward slashes consistently (important for cross-platform compatibility)
            relative_path = self._normalize_path(relative_path)
            language = file_info.get('language', 'unknown')
            
            if language == 'unknown' or language not in parsers:
                continue
            
            parser = parsers[language]
            try:
                parsed = parser.parse(file_info['content'])
                
                # Index file
                self.file_index[relative_path] = {
                    'path': file_path,
                    'relative_path': relative_path,
                    'language': language,
                    'parsed': parsed,
                    'classes': [],
                    'package': None,
                    'namespace': None
                }
                
                # Extract package/namespace
                if language == 'java':
                    package = parsed.get('package', '')
                    if package:
                        self.file_index[relative_path]['package'] = package
                        self.package_index[package].append(relative_path)
                elif language in ['csharp', 'vbnet', 'fsharp']:
                    namespace = parsed.get('namespace', '')
                    if namespace:
                        self.file_index[relative_path]['namespace'] = namespace
                        self.package_index[namespace].append(relative_path)
                elif language == 'php':
                    namespace = parsed.get('namespace', '')
                    if namespace:
                        self.file_index[relative_path]['namespace'] = namespace
                        self.package_index[namespace].append(relative_path)
                
                # Index classes
                classes = parsed.get('classes', [])
                for cls in classes:
                    class_name = cls.get('name', '')
                    if class_name:
                        full_class_name = self._get_full_class_name(
                            class_name, 
                            package or namespace or '', 
                            language
                        )
                        self.class_index[full_class_name] = relative_path
                        self.class_index[class_name] = relative_path  # Also index short name
                        self.file_index[relative_path]['classes'].append({
                            'name': class_name,
                            'full_name': full_class_name
                        })
                
                # Index interfaces (for C#, Java, etc.)
                interfaces = parsed.get('interfaces', [])
                for iface in interfaces:
                    interface_name = iface.get('name', '')
                    if interface_name:
                        full_interface_name = self._get_full_class_name(
                            interface_name,
                            package or namespace or '',
                            language
                        )
                        self.class_index[full_interface_name] = relative_path
                        self.class_index[interface_name] = relative_path  # Also index short name
                        self.file_index[relative_path]['classes'].append({
                            'name': interface_name,
                            'full_name': full_interface_name
                        })
                
            except Exception:
                # Skip files that can't be parsed
                continue
    
    def _get_full_class_name(self, class_name: str, package_or_namespace: str, language: str) -> str:
        """Get fully qualified class name"""
        if not package_or_namespace:
            return class_name
        
        if language == 'java':
            return f"{package_or_namespace}.{class_name}"
        elif language in ['csharp', 'vbnet', 'fsharp']:
            return f"{package_or_namespace}.{class_name}"
        elif language == 'php':
            return f"\\{package_or_namespace}\\{class_name}"
        
        return class_name
    
    def _resolve_dependencies(self, files: List[Dict[str, Any]], parsers: Dict[str, Any]):
        """Resolve dependencies between files based on imports"""
        for file_info in files:
            file_path = file_info.get('relative_path', file_info.get('path', ''))
            # Normalize path to ensure consistency
            file_path = self._normalize_path(file_path)
            language = file_info.get('language', 'unknown')
            
            if file_path not in self.file_index or language not in parsers:
                continue
            
            parser = parsers[language]
            try:
                parsed = self.file_index[file_path]['parsed']
                
                # Get imports based on language
                imports = []
                if language == 'java':
                    imports = parsed.get('imports', [])
                elif language == 'csharp':
                    imports = parsed.get('using', [])
                elif language == 'vbnet':
                    imports = parsed.get('imports', [])
                elif language == 'fsharp':
                    imports = parsed.get('open', [])
                elif language == 'php':
                    imports = parsed.get('use', [])
                
                # Resolve each import
                for imp in imports:
                    resolved_files = self._resolve_import(imp, file_path, language)
                    if resolved_files:
                        # resolved_files can be a single file path or a list
                        if isinstance(resolved_files, list):
                            for resolved in resolved_files:
                                # Normalize resolved path
                                normalized_resolved = self._normalize_path(resolved)
                                if normalized_resolved in self.file_index:
                                    self.dependencies[file_path].add(normalized_resolved)
                                else:
                                    self.external_dependencies[file_path].add(imp)
                        else:
                            # Normalize resolved path
                            normalized_resolved = self._normalize_path(resolved_files)
                            if normalized_resolved in self.file_index:
                                self.dependencies[file_path].add(normalized_resolved)
                            else:
                                self.external_dependencies[file_path].add(imp)
            
            except Exception:
                continue
    
    def _resolve_import(self, import_stmt: str, source_file: str, language: str) -> Optional[Any]:
        """
        Resolve an import statement to a file path or list of file paths
        
        Args:
            import_stmt: Import statement (e.g., "java.util.List", "System.Collections", "MyApp.Models")
            source_file: Path of the file containing the import
            language: Programming language
            
        Returns:
            Resolved file path (str), list of file paths (List[str]), or None if not found
            Returns a list when multiple files match (e.g., all files in a namespace)
        """
        # Clean import statement
        import_stmt = import_stmt.strip()
        
        # Remove wildcards
        if import_stmt.endswith('.*'):
            import_stmt = import_stmt[:-2]
        
        # Try to find by full class name
        if import_stmt in self.class_index:
            resolved = self.class_index[import_stmt]
            return self._normalize_path(resolved) if resolved else None
        
        # Try to find by class name (last segment)
        if '.' in import_stmt:
            class_name = import_stmt.split('.')[-1]
            if class_name in self.class_index:
                resolved = self.class_index[class_name]
                return self._normalize_path(resolved) if resolved else None
        
        # Try to find by package/namespace
        if language == 'java':
            # Check if it's a package
            if import_stmt in self.package_index:
                # Return all files in package
                files = self.package_index[import_stmt]
                if files:
                    normalized_files = [self._normalize_path(f) for f in files]
                    return normalized_files if len(normalized_files) > 1 else normalized_files[0]
        elif language in ['csharp', 'vbnet', 'fsharp']:
            # Check if it's a namespace
            if import_stmt in self.package_index:
                # Return all files in namespace
                files = self.package_index[import_stmt]
                if files:
                    normalized_files = [self._normalize_path(f) for f in files]
                    return normalized_files if len(normalized_files) > 1 else normalized_files[0]
            # Avoid prefix matching to reduce false dependencies
        
        # Try partial matching
        for full_name, file_path in self.class_index.items():
            if full_name.endswith(import_stmt) or import_stmt in full_name:
                return self._normalize_path(file_path) if file_path else None
        
        return None
    
    def _build_dependency_map(self) -> Dict[str, Any]:
        """Build a structured dependency map"""
        nodes = []
        edges = []
        
        # Create nodes
        for file_path, file_info in self.file_index.items():
            node = {
                'id': file_path,
                'path': file_path,
                'language': file_info['language'],
                'package': file_info.get('package') or file_info.get('namespace', ''),
                'classes': [cls['name'] for cls in file_info.get('classes', [])],
                'dependency_count': len(self.dependencies.get(file_path, set())),
                'dependent_count': self._count_dependents(file_path)
            }
            nodes.append(node)
        
        # Create edges
        for source, targets in self.dependencies.items():
            for target in targets:
                edge = {
                    'source': source,
                    'target': target,
                    'type': 'internal'
                }
                edges.append(edge)
        
        return {
            'nodes': nodes,
            'edges': edges,
            'external_dependencies': {
                file_path: list(deps) 
                for file_path, deps in self.external_dependencies.items()
            }
        }
    
    def _count_dependents(self, file_path: str) -> int:
        """Count how many files depend on this file"""
        count = 0
        for deps in self.dependencies.values():
            if file_path in deps:
                count += 1
        return count
    
    def _detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependencies.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
            
            rec_stack.remove(node)
            path.pop()
        
        for node in self.file_index.keys():
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _find_orphaned_files(self) -> List[str]:
        """Find files that have no dependencies and are not depended upon"""
        orphaned = []
        for file_path in self.file_index.keys():
            has_dependencies = len(self.dependencies.get(file_path, set())) > 0
            has_dependents = self._count_dependents(file_path) > 0
            if not has_dependencies and not has_dependents:
                orphaned.append(file_path)
        return orphaned
    
    def _find_highly_coupled_files(self, threshold: int = 5) -> List[Dict[str, Any]]:
        """Find files with high coupling (many dependencies or dependents)"""
        highly_coupled = []
        for file_path in self.file_index.keys():
            dep_count = len(self.dependencies.get(file_path, set()))
            dependent_count = self._count_dependents(file_path)
            total_coupling = dep_count + dependent_count
            
            if total_coupling >= threshold:
                highly_coupled.append({
                    'file': file_path,
                    'dependencies': dep_count,
                    'dependents': dependent_count,
                    'total_coupling': total_coupling
                })
        
        return sorted(highly_coupled, key=lambda x: x['total_coupling'], reverse=True)
    
    def export_json(self, output_path: str) -> Path:
        """Export dependency map to JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        result = self._build_dependency_map()
        result['analysis'] = {
            'file_count': len(self.file_index),
            'class_count': len(self.class_index),
            'dependency_count': sum(len(deps) for deps in self.dependencies.values()),
            'external_dependency_count': sum(len(deps) for deps in self.external_dependencies.values()),
            'circular_dependencies': self._detect_circular_dependencies(),
            'orphaned_files': self._find_orphaned_files(),
            'highly_coupled_files': self._find_highly_coupled_files()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def export_dot(self, output_path: str) -> Path:
        """Export dependency map to Graphviz DOT format"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        lines = ['digraph Dependencies {']
        lines.append('  rankdir=LR;')
        lines.append('  node [shape=box, style=rounded];')
        lines.append('')
        
        # Add nodes
        for file_path, file_info in self.file_index.items():
            label = Path(file_path).name
            package = file_info.get('package') or file_info.get('namespace', '')
            if package:
                label = f"{label}\\n({package})"
            
            node_id = file_path.replace('/', '_').replace('\\', '_').replace('.', '_')
            lines.append(f'  "{node_id}" [label="{label}"];')
        
        lines.append('')
        
        # Add edges
        for source, targets in self.dependencies.items():
            source_id = source.replace('/', '_').replace('\\', '_').replace('.', '_')
            for target in targets:
                target_id = target.replace('/', '_').replace('\\', '_').replace('.', '_')
                lines.append(f'  "{source_id}" -> "{target_id}";')
        
        lines.append('}')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return output_file
    
    def export_mermaid(self, output_path: str) -> Path:
        """Export dependency map to Mermaid format"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        def sanitize_node_id(path: str) -> str:
            """Sanitize path to valid Mermaid node ID"""
            import re
            # Replace all non-word characters with underscores
            node_id = re.sub(r'[^\w]', '_', str(path))
            # Remove consecutive underscores
            node_id = re.sub(r'_+', '_', node_id)
            # Remove leading/trailing underscores
            node_id = node_id.strip('_')
            # Ensure it starts with a letter or underscore
            if node_id and not node_id[0].isalpha() and node_id[0] != '_':
                node_id = '_' + node_id
            return node_id[:50] if node_id else 'node'
        
        def sanitize_label(text: str) -> str:
            """Sanitize text for Mermaid node labels"""
            label = text.replace('\\', '\\\\').replace('"', '\\"')
            label = label.replace('\n', ' ').replace('\r', ' ')
            return label[:40] if label else 'file'
        
        lines = ['graph LR']
        
        # Add edges with node labels (nodes are auto-created with labels in Mermaid)
        edges_added = set()
        for source, targets in self.dependencies.items():
            source_id = sanitize_node_id(source)
            source_label = sanitize_label(Path(source).name)
            
            for target in targets:
                target_id = sanitize_node_id(target)
                target_label = sanitize_label(Path(target).name)
                
                # Avoid duplicate edges
                edge_key = f"{source_id}->{target_id}"
                if edge_key not in edges_added:
                    lines.append(f'  {source_id}["{source_label}"] --> {target_id}["{target_label}"]')
                    edges_added.add(edge_key)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return output_file

    def generate_mermaid_block(self, max_edges: int = 80) -> str:
        """Generate a Mermaid code block for dependency visualization"""
        lines = ["```mermaid", "graph LR"]
        edges_added = set()
        edge_count = 0

        for source, targets in self.dependencies.items():
            source_id = self._sanitize_node_id(source)
            source_label = self._sanitize_label(Path(source).name)

            for target in targets:
                if edge_count >= max_edges:
                    break
                target_id = self._sanitize_node_id(target)
                target_label = self._sanitize_label(Path(target).name)
                edge_key = f"{source_id}->{target_id}"
                if edge_key in edges_added:
                    continue
                lines.append(f'  {source_id}["{source_label}"] --> {target_id}["{target_label}"]')
                edges_added.add(edge_key)
                edge_count += 1
            if edge_count >= max_edges:
                break

        lines.append("```")
        return "\n".join(lines) if edge_count else ""

    def _sanitize_node_id(self, path: str) -> str:
        """Sanitize path to valid Mermaid node ID"""
        import re
        node_id = re.sub(r"[^\w]", "_", str(path))
        node_id = re.sub(r"_+", "_", node_id)
        node_id = node_id.strip("_")
        if node_id and not node_id[0].isalpha() and node_id[0] != "_":
            node_id = "_" + node_id
        return node_id[:50] if node_id else "node"

    def _sanitize_label(self, text: str) -> str:
        """Sanitize text for Mermaid node labels"""
        label = text.replace("\\", "\\\\").replace('"', '\\"')
        label = label.replace("\n", " ").replace("\r", " ")
        return label[:40] if label else "file"
    
    def generate_markdown_report(self) -> str:
        """Generate a markdown report of the dependency analysis"""
        # Use existing analysis data
        circular_deps = self._detect_circular_dependencies()
        orphaned = self._find_orphaned_files()
        highly_coupled = self._find_highly_coupled_files()
        
        lines = ['# Dependency Map Analysis\n']
        lines.append(f"**Total Files:** {len(self.file_index)}\n")
        lines.append(f"**Total Classes:** {len(self.class_index)}\n")
        lines.append(f"**Internal Dependencies:** {sum(len(deps) for deps in self.dependencies.values())}\n")
        lines.append(f"**External Dependencies:** {sum(len(deps) for deps in self.external_dependencies.values())}\n\n")
        
        # Circular dependencies
        if circular_deps:
            lines.append('## ⚠️ Circular Dependencies\n\n')
            for cycle in circular_deps:
                lines.append(f"- {' → '.join(cycle)}\n")
            lines.append('\n')
        
        # Orphaned files
        if orphaned:
            lines.append('## 📦 Orphaned Files\n\n')
            lines.append('Files with no dependencies:\n\n')
            for file_path in orphaned:
                lines.append(f"- `{file_path}`\n")
            lines.append('\n')
        
        # Highly coupled files
        if highly_coupled:
            lines.append('## 🔗 Highly Coupled Files\n\n')
            lines.append('| File | Dependencies | Dependents | Total Coupling |\n')
            lines.append('|------|--------------|------------|----------------|\n')
            for item in highly_coupled[:10]:  # Top 10
                lines.append(f"| `{item['file']}` | {item['dependencies']} | {item['dependents']} | {item['total_coupling']} |\n")
            lines.append('\n')
        
        # Dependency graph (simplified)
        lines.append('## Dependency Graph\n\n')
        lines.append('```mermaid\n')
        lines.append('graph TD\n')
        
        def sanitize_node_id(path: str) -> str:
            """Sanitize path to valid Mermaid node ID"""
            import re
            node_id = re.sub(r'[^\w]', '_', str(path))
            node_id = re.sub(r'_+', '_', node_id)
            node_id = node_id.strip('_')
            if node_id and not node_id[0].isalpha() and node_id[0] != '_':
                node_id = '_' + node_id
            return node_id[:50] if node_id else 'node'
        
        def sanitize_label(text: str) -> str:
            """Sanitize text for Mermaid node labels"""
            label = text.replace('\\', '\\\\').replace('"', '\\"')
            label = label.replace('\n', ' ').replace('\r', ' ')
            return label[:40] if label else 'file'
        
        # Add simplified graph with proper sanitization
        edges_added = set()
        for source, targets in list(self.dependencies.items())[:20]:  # Limit for readability
            source_id = sanitize_node_id(source)
            source_label = sanitize_label(Path(source).name)
            for target in list(targets)[:5]:  # Limit targets per source
                target_id = sanitize_node_id(target)
                target_label = sanitize_label(Path(target).name)
                edge_key = f"{source_id}->{target_id}"
                if edge_key not in edges_added:
                    lines.append(f'  {source_id}["{source_label}"] --> {target_id}["{target_label}"]\n')
                    edges_added.add(edge_key)
        
        lines.append('```\n')
        
        return ''.join(lines)

