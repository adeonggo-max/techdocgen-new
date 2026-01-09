"""Technical documentation generator"""

from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
from .config import Config
from .readers import FileReader, FolderReader, GitReader
from .parsers import JavaParser, CSharpParser, VBNetParser, FSharpParser, PHPParser
from .llm.llm_factory import LLMFactory
from .sequence_diagram import SequenceDiagramGenerator
from .dependency_analyzer import DependencyAnalyzer
from .template_engine import TemplateEngine


class DocumentationGenerator:
    """Main class for generating technical documentation"""
    
    def __init__(self, config_path: Optional[str] = None, llm_provider: Optional[str] = None):
        self.config = Config(config_path)
        self.llm_provider = llm_provider or self.config.get_default_provider()
        self.llm = LLMFactory.create(self.llm_provider, self.config.config)
        
        # Initialize parsers
        self.parsers = {
            "java": JavaParser(self.config.config),
            "csharp": CSharpParser(self.config.config),
            "vbnet": VBNetParser(self.config.config),
            "fsharp": FSharpParser(self.config.config),
            "php": PHPParser(self.config.config)
        }
        
        # Initialize sequence diagram generator
        self.sequence_diagram_gen = SequenceDiagramGenerator(self.config.config)
        
        # Initialize dependency analyzer
        self.dependency_analyzer = DependencyAnalyzer(self.config.config)
        
        # Initialize template engine
        template_dir = self.config.config.get("documentation", {}).get("template_dir")
        template_name = self.config.config.get("documentation", {}).get("template", "confluence.md")
        self.template_engine = TemplateEngine(template_dir, self.config.config)
        self.template_name = template_name
        
        # Ensure default template exists
        self.template_engine.create_default_template()
    
    def generate_from_file(self, file_path: str, progress_callback=None) -> str:
        """Generate documentation from a single file"""
        reader = FileReader(file_path, self.config.config)
        files = reader.read()
        return self._generate_docs(files, progress_callback)
    
    def generate_from_folder(self, folder_path: str, progress_callback=None) -> str:
        """Generate documentation from a folder"""
        reader = FolderReader(folder_path, self.config.config)
        files = reader.read()
        return self._generate_docs(files, progress_callback)
    
    def generate_from_git(self, repo_path: str, branch: Optional[str] = None, progress_callback=None) -> str:
        """Generate documentation from a Git repository"""
        reader = GitReader(repo_path, branch, self.config.config)
        files = reader.read()
        return self._generate_docs(files, progress_callback)
    
    def _get_reader(self, source_type: str, source: str, branch: Optional[str] = None):
        """Get appropriate reader for source type"""
        if source_type == 'file':
            return FileReader(source, self.config.config)
        elif source_type == 'folder':
            return FolderReader(source, self.config.config)
        elif source_type == 'git':
            return GitReader(source, branch, self.config.config)
        else:
            raise ValueError(f"Unknown source type: {source_type}")
    
    def generate_docs_from_files(self, files: List[Dict[str, Any]], progress_callback=None) -> str:
        """Generate documentation from already-read files"""
        return self._generate_docs(files, progress_callback)
    
    def _generate_docs(self, files: List[Dict[str, Any]], progress_callback=None) -> str:
        """Generate documentation from parsed files using templates"""
        if not files:
            return "# Technical Documentation\n\n**TechDocGen by IBMC**\n\nNo source files found."
        
        # Analyze dependencies if enabled
        dependency_analysis = None
        dependency_map_markdown = None
        include_dep_map = self.config.config.get("documentation", {}).get("include_dependency_map", False)
        if include_dep_map and len(files) > 1:
            try:
                dependency_analysis = self.dependency_analyzer.analyze_files(files, self.parsers)
                dependency_map_markdown = self.dependency_analyzer.generate_markdown_report()
            except Exception as e:
                # Silently fail dependency analysis - don't break documentation
                pass
        
        # Group files by language
        files_by_language = {}
        for file_info in files:
            lang = file_info["language"]
            if lang not in files_by_language:
                files_by_language[lang] = []
            files_by_language[lang].append(file_info)
        
        # Count total files for progress tracking
        total_files = sum(len(lang_files) for lang_files in files_by_language.values() if lang_files)
        processed_files = 0
        
        # Process each file to generate documentation and parse structure
        processed_files_by_language = {}
        
        for language, lang_files in files_by_language.items():
            if language == "unknown":
                continue
            
            processed_files_by_language[language] = []
            
            # Get parser for this language
            parser = self.parsers.get(language)
            if not parser:
                continue
            
            # Process each file sequentially
            for file_info in lang_files:
                file_name = file_info.get('name', 'Unknown')
                processed_files += 1
                
                # Report progress
                if progress_callback:
                    progress_callback(processed_files, total_files, file_name)
                
                try:
                    # Parse the code
                    parsed_info = parser.parse(file_info["content"])
                    
                    # Generate documentation using LLM
                    llm_doc = self.llm.generate_documentation(parsed_info, language)
                    
                    # Generate sequence diagram if enabled
                    sequence_diagram = None
                    try:
                        classes = parsed_info.get("classes", [])
                        include_diagram = self.config.config.get("documentation", {}).get("include_sequence_diagrams", True)
                        
                        if include_diagram and len(classes) > 0:
                            # Try simple diagram first (more reliable)
                            sequence_diagram = self.sequence_diagram_gen.generate_sequence_diagram(
                                parsed_info, file_info["content"], language
                            )
                            
                            # Only try LLM if simple diagram not available and we have multiple classes
                            if not sequence_diagram and len(classes) > 1:
                                sequence_diagram = self.sequence_diagram_gen.generate_from_llm_analysis(
                                    parsed_info, file_info["content"], self.llm
                                )
                    except Exception:
                        # Silently fail diagram generation
                        pass
                    
                    # Prepare file data for template
                    processed_file_info = {
                        "name": file_name,
                        "path": file_info.get("path", ""),
                        "relative_path": file_info.get("relative_path", file_info.get("path", "")),
                        "documentation": llm_doc,
                        "parsed_info": parsed_info,
                        "sequence_diagram": sequence_diagram
                    }
                    
                    processed_files_by_language[language].append(processed_file_info)
                    
                except Exception as e:
                    import traceback
                    error_msg = str(e) if str(e) else type(e).__name__
                    # Create error file info for template
                    processed_file_info = {
                        "name": file_name,
                        "path": file_info.get("path", ""),
                        "relative_path": file_info.get("relative_path", file_info.get("path", "")),
                        "documentation": f"*Error processing file: {error_msg}*\n\n<details><summary>Error Details</summary>\n\n```\n{traceback.format_exc()}\n```\n\n</details>",
                        "parsed_info": {"classes": [], "functions": [], "imports": []},
                        "sequence_diagram": None
                    }
                    processed_files_by_language[language].append(processed_file_info)
        
        # Prepare template context
        template_context = {
            "llm_provider": self.llm_provider,
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_files": total_files,
            "files_by_language": processed_files_by_language,
            "dependency_map": dependency_map_markdown,
            "languages": [lang for lang in processed_files_by_language.keys() if lang != "unknown"]
        }
        
        # Render template
        try:
            # Try to use specified template, fallback to default if not found
            documentation = self.template_engine.render(self.template_name, template_context)
        except Exception as e:
            # If template rendering fails, fallback to default template
            try:
                documentation = self.template_engine.render("default.md", template_context)
            except Exception:
                # Last resort: return basic documentation
                return f"# Technical Documentation\n\n**TechDocGen by IBMC**\n\nGenerated using {self.llm_provider.upper()} LLM\n\nError rendering template: {str(e)}"
        
        return documentation
    
    def save_documentation(self, documentation: str, output_path: Optional[str] = None) -> Path:
        """Save documentation to file"""
        if output_path:
            output_file = Path(output_path)
        else:
            output_dir = Path(self.config.get("output.directory", "./docs"))
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = self.config.get("output.filename_template", "technical_docs.md")
            output_file = output_dir / filename
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        return output_file
    
    def generate_dependency_map(self, files: List[Dict[str, Any]], format: str = "json", output_path: Optional[str] = None) -> Path:
        """
        Generate dependency map from files
        
        Args:
            files: List of file dictionaries
            format: Output format ('json', 'dot', 'mermaid', 'markdown')
            output_path: Optional output file path
            
        Returns:
            Path to generated dependency map file
        """
        # Analyze dependencies
        analysis = self.dependency_analyzer.analyze_files(files, self.parsers)
        
        # Determine output path
        if not output_path:
            output_dir = Path(self.config.get("output.directory", "./docs"))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            ext_map = {
                "json": ".json",
                "dot": ".dot",
                "mermaid": ".mmd",
                "markdown": ".md"
            }
            ext = ext_map.get(format, ".json")
            output_path = str(output_dir / f"dependency_map{ext}")
        
        # Export based on format
        if format == "json":
            return self.dependency_analyzer.export_json(output_path)
        elif format == "dot":
            return self.dependency_analyzer.export_dot(output_path)
        elif format == "mermaid":
            return self.dependency_analyzer.export_mermaid(output_path)
        elif format == "markdown":
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(self.dependency_analyzer.generate_markdown_report())
            return output_file
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json', 'dot', 'mermaid', or 'markdown'")

