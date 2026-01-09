# TechDocGen by IBMC - Architecture Document

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Design Patterns](#design-patterns)
7. [Key Components](#key-components)
8. [Configuration Management](#configuration-management)
9. [User Interfaces](#user-interfaces)
10. [Deployment & Execution](#deployment--execution)

---

## Overview

**TechDocGen by IBMC** is a comprehensive technical documentation generator that automatically creates high-quality documentation from source code using Large Language Models (LLMs). The system supports multiple programming languages (Java, C#, VB.NET, F#, PHP), multiple LLM providers (OpenAI, Anthropic, Ollama, MCP), and can process source code from files, folders, or Git repositories.

### Key Capabilities
- **Multi-Language Support**: Java, .NET (C#, VB.NET, F#), PHP
- **Multiple Source Types**: Single files, folders, Git repositories
- **LLM Integration**: OpenAI, Anthropic, Ollama, MCP
- **Intelligent Parsing**: Tree-sitter based parsing with language-specific parsers
- **Dependency Analysis**: Automatic dependency mapping and circular dependency detection
- **Multiple Output Formats**: Markdown, PDF (Confluence-style)
- **Web UI & CLI**: Dual interface support

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interfaces                          │
├─────────────────────────────┬───────────────────────────────────┤
│      Web UI (Streamlit)     │        CLI (Click/Python)          │
└──────────────┬──────────────┴──────────────┬────────────────────┘
               │                              │
               └──────────────┬───────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Main Entry      │
                    │   Points          │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Documentation     │
                    │ Generator         │
                    │ (Orchestrator)    │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐  ┌────────▼────────┐
│   Readers      │   │    Parsers      │  │  LLM Providers  │
│  (File/Folder/ │   │ (Java/C#/VB/   │  │ (OpenAI/Anthropic│
│     Git)       │   │   F#/PHP)      │  │  Ollama/MCP)    │
└────────────────┘   └─────────────────┘  └─────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Output Writers   │
                    │ (Markdown/PDF)    │
                    └───────────────────┘
```

### Component Layers

1. **Presentation Layer**
   - Streamlit Web UI (`app.py`)
   - CLI Interface (`main.py`)

2. **Business Logic Layer**
   - Documentation Generator (`src/generator.py`)
   - Dependency Analyzer (`src/dependency_analyzer.py`)
   - Sequence Diagram Generator (`src/sequence_diagram.py`)

3. **Data Access Layer**
   - File Reader (`src/readers/file_reader.py`)
   - Folder Reader (`src/readers/folder_reader.py`)
   - Git Reader (`src/readers/git_reader.py`)

4. **Processing Layer**
   - Language Parsers (`src/parsers/`)
   - LLM Integrations (`src/llm/`)

5. **Output Layer**
   - Markdown Writer (built-in)
   - PDF Generator (`src/pdf_generator.py`)

---

## Component Architecture

### Core Components

#### 1. DocumentationGenerator (`src/generator.py`)
**Purpose**: Main orchestration component that coordinates the documentation generation process.

**Responsibilities**:
- Initialize readers, parsers, and LLM providers
- Coordinate file reading, parsing, and documentation generation
- Manage progress tracking and error handling
- Generate final documentation output

**Key Methods**:
- `generate_from_file()` - Process single file
- `generate_from_folder()` - Process folder
- `generate_from_git()` - Process Git repository
- `_generate_docs()` - Core generation logic
- `save_documentation()` - Save output to file

**Dependencies**: Config, Readers, Parsers, LLM Factory, Dependency Analyzer

#### 2. Configuration Manager (`src/config.py`)
**Purpose**: Centralized configuration management from YAML files and environment variables.

**Responsibilities**:
- Load configuration from `config.yaml`
- Override with environment variables
- Provide configuration access methods
- Manage LLM provider settings

**Key Features**:
- Dot-notation access (e.g., `config.get("documentation.include_comments")`)
- Environment variable override support
- Default configuration fallback

#### 3. Readers Module (`src/readers/`)
**Purpose**: Abstract and implement different source code reading strategies.

**Components**:
- `BaseReader` - Abstract base class
- `FileReader` - Reads single files
- `FolderReader` - Recursively reads folders
- `GitReader` - Clones and reads Git repositories

**Design Pattern**: Strategy Pattern

**Common Features**:
- File exclusion patterns
- File size limits
- Language detection
- Path filtering

#### 4. Parsers Module (`src/parsers/`)
**Purpose**: Parse source code and extract structured information.

**Components**:
- `BaseParser` - Abstract base class
- `JavaParser` - Java source code parsing
- `CSharpParser` - C# source code parsing
- `VBNetParser` - VB.NET source code parsing
- `FSharpParser` - F# source code parsing
- `PHPParser` - PHP source code parsing

**Parsing Technology**: Tree-sitter (for AST parsing)

**Extracted Information**:
- Classes and their methods
- Functions/procedures
- Imports/dependencies
- Comments and documentation
- Interfaces and abstract classes
- Properties and fields

**Design Pattern**: Strategy Pattern, Template Method Pattern

#### 5. LLM Module (`src/llm/`)
**Purpose**: Abstract and implement multiple LLM provider integrations.

**Components**:
- `BaseLLM` - Abstract base class defining LLM interface
- `OpenAILLM` - OpenAI API integration
- `AnthropicLLM` - Anthropic Claude API integration
- `OllamaLLM` - Local Ollama integration
- `MCPLLM` - Model Context Protocol integration
- `LLMFactory` - Factory for creating LLM instances

**Design Pattern**: Factory Pattern, Strategy Pattern

**LLM Responsibilities**:
- Accept parsed code structure
- Generate natural language documentation
- Handle provider-specific API calls
- Error handling and retries

#### 6. Dependency Analyzer (`src/dependency_analyzer.py`)
**Purpose**: Analyze code dependencies and generate dependency maps.

**Features**:
- Build file dependency graphs
- Detect circular dependencies
- Identify orphaned files
- Find highly coupled components
- Export in multiple formats (JSON, DOT, Mermaid, Markdown)

**Output Formats**:
- JSON - Machine-readable dependency data
- DOT - Graphviz format for visualization
- Mermaid - Diagram format for documentation
- Markdown - Human-readable report

#### 7. Sequence Diagram Generator (`src/sequence_diagram.py`)
**Purpose**: Generate sequence diagrams from code structure.

**Features**:
- Extract method call sequences
- Generate Mermaid sequence diagrams
- LLM-assisted diagram generation
- Support for multiple classes

#### 8. PDF Generator (`src/pdf_generator.py`)
**Purpose**: Convert Markdown documentation to PDF with Confluence-style formatting.

**Features**:
- Confluence-inspired styling
- Syntax highlighting for code blocks
- Table of contents
- Page numbering
- Professional formatting

**Technology**: WeasyPrint for PDF generation, Pygments for syntax highlighting

---

## Data Flow

### Documentation Generation Flow

```
1. User Input
   ├─ Source Type: File/Folder/Git
   ├─ LLM Provider Selection
   └─ Configuration Options

2. Source Reading Phase
   ├─ Reader Selection (FileReader/FolderReader/GitReader)
   ├─ File Discovery & Filtering
   ├─ Language Detection
   └─ Content Reading
       └─ Output: List[FileInfo{path, content, language}]

3. Parsing Phase (Per File)
   ├─ Select Parser by Language
   ├─ Parse AST using Tree-sitter
   ├─ Extract Structure (classes, methods, imports)
   └─ Output: ParsedInfo{classes, methods, imports, comments}

4. Dependency Analysis Phase (Optional)
   ├─ Analyze file dependencies
   ├─ Build dependency graph
   ├─ Detect circular dependencies
   └─ Output: DependencyMap{graph, analysis}

5. Documentation Generation Phase (Per File)
   ├─ Prepare prompt from ParsedInfo
   ├─ Call LLM Provider
   ├─ Generate natural language documentation
   └─ Output: Documentation text

6. Aggregation Phase
   ├─ Combine all file documentation
   ├─ Add dependency maps
   ├─ Add sequence diagrams
   └─ Generate final Markdown

7. Output Phase
   ├─ Save Markdown file
   ├─ Generate PDF (optional)
   └─ Return file paths
```

### Data Structures

**FileInfo**:
```python
{
    "path": str,           # Absolute file path
    "relative_path": str,  # Relative path from source
    "content": str,        # File content
    "language": str,       # Detected language (java, csharp, etc.)
    "name": str           # File name
}
```

**ParsedInfo**:
```python
{
    "classes": [
        {
            "name": str,
            "methods": [{"name": str, "parameters": [...]}],
            "properties": [...],
            "inherits": str
        }
    ],
    "functions": [...],
    "imports": [...],
    "comments": [...]
}
```

**DependencyAnalysis**:
```python
{
    "file_count": int,
    "class_count": int,
    "dependency_count": int,
    "circular_dependencies": [[str]],
    "orphaned_files": [str],
    "highly_coupled_files": [...]
}
```

---

## Technology Stack

### Core Technologies

**Programming Language**: Python 3.8+

**Key Libraries**:
- **Streamlit** - Web UI framework
- **Click** - CLI framework
- **Tree-sitter** - Code parsing (tree-sitter-java, tree-sitter-c-sharp, tree-sitter-php)
- **PyYAML** - Configuration management
- **python-dotenv** - Environment variable management
- **GitPython** - Git repository operations
- **WeasyPrint** - PDF generation
- **Pygments** - Syntax highlighting
- **Markdown** - Markdown processing
- **Requests** - HTTP client for LLM APIs

### LLM Integration Libraries

- **openai** - OpenAI API client
- **anthropic** - Anthropic API client
- **ollama** - Ollama client for local LLMs

### Development Tools

- **Rich** - Terminal formatting and progress bars
- **pathspec** - Path pattern matching

---

## Design Patterns

### 1. Factory Pattern
**Usage**: LLM Provider Creation
- `LLMFactory.create()` creates appropriate LLM instance based on provider name
- Simplifies adding new LLM providers

### 2. Strategy Pattern
**Usage**: 
- **Readers**: FileReader, FolderReader, GitReader implement BaseReader
- **Parsers**: Language-specific parsers implement BaseParser
- **LLM Providers**: Each provider implements BaseLLM

### 3. Template Method Pattern
**Usage**: BaseReader and BaseParser provide common functionality with abstract methods for specific implementations

### 4. Facade Pattern
**Usage**: DocumentationGenerator acts as facade, hiding complexity of readers, parsers, and LLM providers

### 5. Singleton Pattern
**Usage**: Configuration instance (created once and reused)

---

## Key Components

### Web UI (`app.py`)

**Framework**: Streamlit

**Features**:
- Modern gradient-based UI
- Tab-based interface:
  - Source Selection
  - Generate
  - Preview
  - Dependency Map
- Real-time progress tracking
- Live documentation preview
- Download options (Markdown, PDF)
- LLM provider selection and configuration
- Ollama model discovery

**State Management**: Streamlit session state

**Key Functions**:
- `main()` - Main UI loop
- `load_config()` - Load configuration
- `get_ollama_models()` - Discover available Ollama models
- `render_markdown_with_mermaid()` - Render documentation with diagrams
- `generate_summary()` - Extract documentation summary

### CLI (`main.py`)

**Framework**: Click

**Features**:
- Rich terminal output
- Progress bars
- Verbose mode
- Multiple output options
- Dependency map generation

**Commands**:
```bash
python main.py --source <path> --type <file|folder|git> [options]
```

**Options**:
- `--source`, `-s` - Source path
- `--type`, `-t` - Source type
- `--output`, `-o` - Output file
- `--provider`, `-p` - LLM provider
- `--config`, `-c` - Config file
- `--branch`, `-b` - Git branch
- `--verbose`, `-v` - Verbose output
- `--dep-map` - Generate dependency map
- `--dep-map-format` - Dependency map format

### Configuration System

**Configuration File**: `config.yaml`

**Structure**:
```yaml
languages: [java, csharp, vbnet, fsharp, php]
extensions: {...}
llm_providers:
  openai: {...}
  anthropic: {...}
  ollama: {...}
  mcp: {...}
documentation:
  include_comments: bool
  include_imports: bool
  max_file_size_mb: int
  exclude_patterns: [...]
output:
  format: markdown
  directory: ./docs
```

**Environment Variable Override**:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `DEFAULT_LLM_PROVIDER`

---

## User Interfaces

### Web UI Architecture

```
Streamlit App (app.py)
├── Sidebar
│   ├── LLM Provider Selection
│   ├── Provider-specific Settings
│   └── Advanced Settings
│
└── Main Area (Tabs)
    ├── Tab 1: Source Selection
    │   ├── Source Type Radio
    │   ├── File Upload / Path Input / Git URL
    │   └── Branch Selection (for Git)
    │
    ├── Tab 2: Generate
    │   ├── Source Info Display
    │   ├── Generate Button
    │   └── Progress Tracking
    │
    ├── Tab 3: Preview
    │   ├── Summary Section
    │   ├── Source Files List
    │   ├── Metrics
    │   ├── Download Buttons
    │   └── Documentation Preview
    │
    └── Tab 4: Dependency Map
        ├── Analysis Button
        ├── Metrics Display
        ├── Visual Dependency Graph
        ├── Circular Dependencies
        └── Export Options
```

### CLI Architecture

```
CLI Entry Point (main.py)
├── Argument Parsing (Click)
├── Source Type Auto-detection
├── Generator Initialization
├── Progress Tracking (Rich)
└── Output Generation
```

---

## Deployment & Execution

### Execution Modes

**1. Web UI Mode**
```bash
streamlit run app.py
# or
./run_ui.sh
```
- Runs on `http://localhost:8501`
- Interactive browser-based interface
- Real-time updates

**2. CLI Mode**
```bash
python main.py --source <path> --type <type> [options]
```
- Command-line interface
- Suitable for automation and CI/CD
- Non-interactive

### Requirements

**System Requirements**:
- Python 3.8+
- 4GB+ RAM (for Ollama models)
- Internet connection (for cloud LLM providers)

**Installation**:
```bash
pip install -r requirements.txt
```

**Ollama Setup** (for local LLMs):
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.2
# or
ollama pull deepseek-coder:6.7b
```

### Output Structure

```
docs/
├── {project_name}_technical_docs.md  # Main documentation
├── dependency_map.json                # Dependency data (if generated)
├── dependency_map.dot                 # Graphviz format (optional)
├── dependency_map.mmd                 # Mermaid format (optional)
└── dependency_map.md                  # Markdown report (optional)
```

### Error Handling

**Error Handling Strategy**:
- Graceful degradation for optional features (diagrams, dependency analysis)
- Detailed error messages with tracebacks (in verbose mode)
- Progress tracking continues even if individual files fail
- User-friendly error display in UI

**Common Error Scenarios**:
- LLM API failures → Retry with exponential backoff
- Parsing errors → Skip file with warning
- Large files → Skip with size limit message
- Network errors → Clear error message

---

## Extensibility

### Adding a New Language Parser

1. Create new parser in `src/parsers/`
2. Extend `BaseParser`
3. Implement `parse()` method
4. Register in `config.yaml` extensions
5. Add parser instance in `DocumentationGenerator.__init__()`

### Adding a New LLM Provider

1. Create new LLM class in `src/llm/`
2. Extend `BaseLLM`
3. Implement `generate_documentation()` method
4. Register in `LLMFactory._providers`
5. Add configuration in `config.yaml`

### Adding a New Reader Type

1. Create new reader in `src/readers/`
2. Extend `BaseReader`
3. Implement `read()` method
4. Add method in `DocumentationGenerator`

---

## Performance Considerations

### Optimization Strategies

1. **Sequential Processing**: Files processed one at a time to manage memory
2. **File Size Limits**: Configurable max file size to prevent memory issues
3. **Caching**: Parsed ASTs could be cached (future enhancement)
4. **Parallel Processing**: Potential for parallel file processing (future enhancement)

### Resource Usage

- **Memory**: Scales with file sizes and number of files
- **Network**: LLM API calls require internet (except Ollama)
- **CPU**: Tree-sitter parsing is CPU-intensive for large files
- **Disk**: Temporary Git repositories for Git sources

### Scalability

**Current Limitations**:
- Single-threaded file processing
- No distributed processing
- Limited to local machine resources

**Future Enhancements**:
- Parallel file processing
- Distributed LLM processing
- Incremental documentation updates
- Caching layer for parsed code

---

## Security Considerations

1. **API Keys**: Stored in environment variables, never committed
2. **File System Access**: Respects file permissions and exclude patterns
3. **Git Operations**: Uses GitPython, respects SSH keys
4. **Input Validation**: File size limits, path sanitization
5. **LLM Content**: User-generated content sent to LLM providers

---

## Future Enhancements

1. **Additional Languages**: TypeScript, Python, Go, Rust
2. **Advanced Diagrams**: Architecture diagrams, class diagrams
3. **Documentation Templates**: Customizable output templates
4. **Batch Processing**: Process multiple projects
5. **API Server**: REST API for programmatic access
6. **Incremental Updates**: Update documentation for changed files only
7. **Version Control Integration**: Track documentation changes
8. **Multi-language Projects**: Better handling of mixed-language projects

---

## Conclusion

**TechDocGen by IBMC** is built with a modular, extensible architecture that separates concerns between reading, parsing, documentation generation, and output formatting. The use of design patterns like Factory, Strategy, and Template Method makes the system easy to extend with new languages, LLM providers, and features.

The dual interface (Web UI and CLI) makes it accessible to both technical and non-technical users, while the comprehensive dependency analysis and diagram generation features provide deep insights into codebases.

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Product**: TechDocGen by IBMC  
**Author**: IBMC Development Team
