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
10. [Deployment Architecture](#deployment-architecture)
11. [Infrastructure Setup](#infrastructure-setup)
12. [Technical Architecture Details](#technical-architecture-details)
13. [Deployment & Execution](#deployment--execution)

---

## Overview

**TechDocGen by IBMC** is a comprehensive technical documentation generator that automatically creates high-quality documentation from source code using Large Language Models (LLMs). The system supports multiple programming languages (Java, C#, VB.NET, F#, PHP), multiple LLM providers (Ollama, MCP), and can process source code from files, folders, or Git repositories.

### Key Capabilities
- **Multi-Language Support**: Java, .NET (C#, VB.NET, F#), PHP
- **Multiple Source Types**: Single files, folders, Git repositories
- **LLM Integration**: Ollama, MCP
- **Intelligent Parsing**: Tree-sitter based parsing with language-specific parsers
- **Dependency Analysis**: Automatic dependency mapping and circular dependency detection
- **Correlation & Integration**: Cross-stack correlation signals and messaging integration graphs
- **Service Catalog**: Controllers, endpoints, services, and interface inventory
- **Call Graphs**: Intra-class method call visualization
- **Multiple Output Formats**: Markdown, PDF (Confluence-style)
- **Diagram Rendering**: Mermaid diagrams rendered in UI and PDF
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
│  (File/Folder/ │   │ (Java/C#/VB/   │  │   (Ollama/MCP)  │
│     Git)       │   │   F#/PHP)      │  │                │
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
   - Correlation Analyzer (`src/correlation_analyzer.py`)
   - Service Catalog (`src/service_catalog.py`)
   - Call Graph Analyzer (`src/call_graph_analyzer.py`)
   - App Interaction Sequence (`src/app_sequence_diagram.py`)
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
- Generate Mermaid blocks for visualizations

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
- Mermaid diagrams rendered as images (Kroki)

**Technology**: WeasyPrint for PDF generation, Pygments for syntax highlighting, Kroki for Mermaid rendering

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
   ├─ Add correlation/integration graphs
   ├─ Add service catalog and call graphs
   ├─ Add app interaction sequence
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
    └── Tab 4: Correlation & Dependencies
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

## Deployment Architecture

### Deployment Models

TechDocGen by IBMC supports multiple deployment models to accommodate different use cases, from local development to enterprise-scale production environments.

#### 1. Local Development Deployment

**Use Case**: Individual developers, small teams, local testing

**Architecture**:
```
┌─────────────────────────────────────────┐
│         Developer Machine                │
│  ┌───────────────────────────────────┐  │
│  │   TechDocGen Application          │  │
│  │   ├── Streamlit UI (Port 8501)   │  │
│  │   ├── CLI Interface               │  │
│  │   └── Core Engine                 │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   Local LLM (Ollama)              │  │
│  │   └── Port 11434                  │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   File System / Git Repos          │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Characteristics**:
- Single-machine deployment
- All components run locally
- No network dependencies (when using Ollama)
- Minimal infrastructure requirements
- Suitable for privacy-sensitive projects

**Requirements**:
- Python 3.8+ installed
- 4GB+ RAM (8GB+ recommended for Ollama)
- Local storage for source code and outputs
- Optional: Ollama for local LLM processing

#### 2. Containerized Deployment (Docker)

**Use Case**: Consistent environments, CI/CD pipelines, isolated deployments

**Architecture**:
```
┌─────────────────────────────────────────────┐
│         Docker Host / Container Runtime     │
│  ┌───────────────────────────────────────┐  │
│  │   Container: techdocgen-app          │  │
│  │   ├── Python Runtime                  │  │
│  │   ├── Streamlit UI                    │  │
│  │   ├── CLI Tools                       │  │
│  │   └── Application Code                │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │   Container: ollama (Optional)        │  │
│  │   └── Local LLM Service               │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │   Volume: /data                        │  │
│  │   ├── Source Code                      │  │
│  │   └── Generated Docs                   │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

**Docker Compose Example**:
```yaml
version: '3.8'
services:
  techdocgen:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./docs:/app/docs
      - ./config.yaml:/app/config.yaml
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - ollama
    networks:
      - techdocgen-network

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    networks:
      - techdocgen-network

volumes:
  ollama-data:

networks:
  techdocgen-network:
    driver: bridge
```

**Benefits**:
- Consistent runtime environment
- Easy deployment and scaling
- Isolation from host system
- Version control for dependencies
- Simplified dependency management

#### 3. Cloud Deployment (SaaS Model)

**Use Case**: Multi-tenant SaaS, enterprise customers, scalable infrastructure

**Architecture**:
```
┌─────────────────────────────────────────────────────────┐
│                    Cloud Infrastructure                   │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │           Load Balancer / API Gateway              │  │
│  └───────────────────────┬────────────────────────────┘  │
│                          │                                │
│        ┌─────────────────┼─────────────────┐            │
│        │                 │                 │              │
│  ┌─────▼─────┐   ┌───────▼──────┐  ┌──────▼──────┐      │
│  │  App      │   │  App         │  │  App        │      │
│  │  Instance │   │  Instance    │  │  Instance   │      │
│  │  (Pod 1)  │   │  (Pod 2)     │  │  (Pod N)    │      │
│  └─────┬─────┘   └───────┬──────┘  └──────┬──────┘      │
│        │                 │                 │              │
│        └─────────────────┼─────────────────┘            │
│                          │                                │
│  ┌───────────────────────▼────────────────────────────┐  │
│  │         Message Queue (Task Queue)                  │  │
│  │         - Redis / RabbitMQ / SQS                  │  │
│  └───────────────────────┬────────────────────────────┘  │
│                          │                                │
│        ┌─────────────────┼─────────────────┐            │
│        │                 │                 │              │
│  ┌─────▼─────┐   ┌───────▼──────┐  ┌──────▼──────┐      │
│  │  Worker    │   │  Worker     │  │  Worker     │      │
│  │  Pool 1    │   │  Pool 2     │  │  Pool N     │      │
│  │  (LLM)     │   │  (LLM)      │  │  (LLM)      │      │
│  └────────────┘   └─────────────┘  └─────────────┘      │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │         Object Storage (S3 / GCS / Azure)          │  │
│  │         - Source Code Cache                        │  │
│  │         - Generated Documentation                   │  │
│  │         - Dependency Maps                          │  │
│  └────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │         Database (PostgreSQL / MongoDB)            │  │
│  │         - User Management                          │  │
│  │         - Job Status                              │  │
│  │         - Configuration                           │  │
│  └────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │         External Services                          │  │
│  │         - LLM APIs (MCP providers)                 │  │
│  │         - Git Providers (GitHub, GitLab, etc.)      │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Key Components**:
- **Load Balancer**: Distributes incoming requests across multiple app instances
- **Application Instances**: Stateless application servers (Kubernetes pods, ECS tasks, etc.)
- **Task Queue**: Manages asynchronous documentation generation jobs
- **Worker Pools**: Dedicated workers for LLM processing
- **Object Storage**: Stores generated documentation and cached data
- **Database**: Manages user data, job status, and configuration

**Scaling Strategy**:
- **Horizontal Scaling**: Add more app instances based on load
- **Worker Scaling**: Scale worker pools independently based on queue depth
- **Auto-scaling**: Based on CPU, memory, or queue metrics

#### 4. Kubernetes Deployment

**Use Case**: Enterprise deployments, microservices architecture, high availability

**Architecture**:
```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
│                                                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │              Ingress Controller                    │ │
│  │              (NGINX / Traefik)                    │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐ │
│  │         Service: techdocgen-web                    │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│        ┌─────────────────┼─────────────────┐             │
│        │                 │                 │               │
│  ┌─────▼─────┐   ┌───────▼──────┐  ┌──────▼──────┐       │
│  │ Deployment│   │ Deployment   │  │ Deployment  │       │
│  │ techdocgen│   │ techdocgen    │  │ techdocgen  │       │
│  │ -web-1    │   │ -web-2        │  │ -web-3      │       │
│  └───────────┘   └───────────────┘  └─────────────┘       │
│                                                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │         Service: techdocgen-workers              │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│        ┌─────────────────┼─────────────────┐             │
│        │                 │                 │               │
│  ┌─────▼─────┐   ┌───────▼──────┐  ┌──────▼──────┐       │
│  │ Deployment│   │ Deployment   │  │ Deployment  │       │
│  │ worker-1  │   │ worker-2     │  │ worker-N    │       │
│  └───────────┘   └───────────────┘  └─────────────┘       │
│                                                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │         StatefulSet: ollama (Optional)            │ │
│  │         - Persistent Volume for Models            │ │
│  └───────────────────────────────────────────────────┘ │
│                                                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │         ConfigMap: app-config                    │ │
│  │         Secret: api-keys                         │ │
│  │         PersistentVolumeClaim: docs-storage      │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Kubernetes Manifests**:
- **Deployment**: Application and worker deployments
- **Service**: Internal service discovery
- **Ingress**: External access routing
- **ConfigMap**: Configuration management
- **Secret**: API keys and sensitive data
- **PersistentVolumeClaim**: Storage for documentation and models

#### 5. Serverless Deployment (AWS Lambda / Azure Functions)

**Use Case**: Event-driven processing, cost optimization, sporadic usage

**Architecture**:
```
┌─────────────────────────────────────────────────────────┐
│              Serverless Architecture                     │
│                                                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │         API Gateway / Function Trigger            │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐ │
│  │         Lambda / Azure Function                     │ │
│  │         - Documentation Generation Handler          │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐ │
│  │         External LLM APIs                           │ │
│  │         - MCP providers                             │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │         S3 / Blob Storage                          │ │
│  │         - Source Code Input                        │ │
│  │         - Generated Documentation Output           │ │
│  └───────────────────────────────────────────────────┘ │
│                                                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │         DynamoDB / Cosmos DB                      │ │
│  │         - Job Status                               │ │
│  │         - Metadata                                 │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Considerations**:
- Function timeout limits (15 minutes for Lambda)
- Cold start latency
- Memory and CPU constraints
- Stateless execution requirements
- External LLM API dependencies (Ollama not suitable)

### Deployment Comparison

| Deployment Model | Scalability | Complexity | Cost | Use Case |
|-----------------|-------------|------------|------|----------|
| Local Development | Low | Low | Low | Development, Testing |
| Docker | Medium | Medium | Low-Medium | CI/CD, Small Teams |
| Cloud (SaaS) | High | High | Medium-High | Production, Enterprise |
| Kubernetes | Very High | Very High | High | Enterprise, Multi-tenant |
| Serverless | Auto | Medium | Pay-per-use | Event-driven, Sporadic |

---

## Infrastructure Setup

### Infrastructure Requirements

#### Minimum Requirements (Local Development)

**Hardware**:
- CPU: 2+ cores
- RAM: 4GB (8GB recommended with Ollama)
- Storage: 5GB free space
- Network: Internet connection (for cloud LLM providers)

**Software**:
- Operating System: Linux, macOS, or Windows
- Python: 3.8 or higher
- Git: For Git repository support
- (Optional) Docker: For containerized deployment

#### Recommended Requirements (Production)

**Hardware**:
- CPU: 4+ cores (8+ for high concurrency)
- RAM: 16GB+ (32GB+ for local LLM processing)
- Storage: 50GB+ SSD (for models and documentation cache)
- Network: High-bandwidth connection for LLM API calls

**Software**:
- Operating System: Linux (Ubuntu 20.04+ or RHEL 8+)
- Python: 3.10 or higher
- Container Runtime: Docker 20.10+ or containerd
- Orchestration: Kubernetes 1.24+ (for production)
- Reverse Proxy: NGINX or Traefik
- Database: PostgreSQL 13+ or MongoDB 5+

### Network Architecture

#### Network Topology

```
┌─────────────────────────────────────────────────────────┐
│                    Internet / WAN                        │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ HTTPS (443)
                        │
        ┌───────────────▼───────────────┐
        │     Firewall / Security       │
        │     - DDoS Protection         │
        │     - WAF Rules               │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │     Load Balancer              │
        │     - SSL Termination          │
        │     - Health Checks            │
        │     - Request Routing         │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │     Application Tier            │
        │     ┌─────────────────────┐    │
        │     │  Web UI (Streamlit) │    │
        │     │  Port: 8501         │    │
        │     └─────────────────────┘    │
        │     ┌─────────────────────┐    │
        │     │  API Gateway        │    │
        │     │  Port: 8000         │    │
        │     └─────────────────────┘    │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │     Processing Tier            │
        │     ┌─────────────────────┐    │
        │     │  Worker Pool        │    │
        │     │  - LLM Processing   │    │
        │     │  - Code Parsing     │    │
        │     └─────────────────────┘    │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │     Data Tier                  │
        │     ┌─────────────────────┐    │
        │     │  Object Storage     │    │
        │     │  - Documentation    │    │
        │     │  - Source Cache     │    │
        │     └─────────────────────┘    │
        │     ┌─────────────────────┐    │
        │     │  Database           │    │
        │     │  - Job Status       │    │
        │     │  - User Data        │    │
        │     └─────────────────────┘    │
        └───────────────────────────────┘
```

#### Network Ports and Protocols

| Service | Port | Protocol | Purpose | Access |
|---------|------|----------|---------|--------|
| Streamlit UI | 8501 | HTTP/HTTPS | Web interface | Public/Internal |
| API Gateway | 8000 | HTTP/HTTPS | REST API | Public/Internal |
| Ollama | 11434 | HTTP | Local LLM service | Internal |
| PostgreSQL | 5432 | TCP | Database | Internal |
| Redis | 6379 | TCP | Cache/Queue | Internal |
| NGINX | 80, 443 | HTTP/HTTPS | Reverse proxy | Public |

#### Security Considerations

**Network Security**:
- **Firewall Rules**: Restrict access to internal services
- **SSL/TLS**: Encrypt all external communications
- **VPN Access**: For internal service access
- **Network Segmentation**: Separate public, application, and data tiers

**Application Security**:
- **API Authentication**: JWT tokens or OAuth2
- **Rate Limiting**: Prevent abuse
- **Input Validation**: Sanitize all user inputs
- **Secret Management**: Use secret management services (AWS Secrets Manager, HashiCorp Vault)

### Storage Architecture

#### Storage Requirements

**Documentation Storage**:
- **Type**: Object Storage (S3, GCS, Azure Blob) or File System
- **Capacity**: 10GB+ (scales with usage)
- **Access Pattern**: Write-heavy, read-moderate
- **Retention**: Configurable (default: 90 days)

**Source Code Cache**:
- **Type**: Object Storage or File System
- **Capacity**: 50GB+ (depends on repository sizes)
- **Access Pattern**: Write-once, read-many
- **Retention**: 30 days (configurable)

**Model Storage (Ollama)**:
- **Type**: Local File System or Persistent Volume
- **Capacity**: 10-50GB per model
- **Access Pattern**: Read-heavy
- **Location**: Co-located with Ollama service

**Database Storage**:
- **Type**: Block Storage (SSD)
- **Capacity**: 20GB+ (scales with users/jobs)
- **Access Pattern**: Read/write balanced
- **Backup**: Daily automated backups

#### Storage Layout

```
Storage Structure:
├── documentation/
│   ├── {project_id}/
│   │   ├── {timestamp}_technical_docs.md
│   │   ├── {timestamp}_technical_docs.pdf
│   │   └── dependency_map.json
│   └── archive/
│       └── {year}/{month}/
│
├── cache/
│   ├── git_repos/
│   │   └── {repo_hash}/
│   ├── parsed_code/
│   │   └── {file_hash}.json
│   └── dependency_graphs/
│       └── {project_hash}.json
│
├── models/ (Ollama)
│   └── {model_name}/
│
└── database/
    ├── postgres_data/
    └── backups/
```

### Compute Infrastructure

#### CPU Requirements

**Per Instance**:
- **Minimum**: 2 vCPUs
- **Recommended**: 4-8 vCPUs
- **High Load**: 8-16 vCPUs

**CPU-Intensive Operations**:
- Tree-sitter parsing (single-threaded per file)
- PDF generation (multi-threaded)
- Dependency graph analysis

#### Memory Requirements

**Per Instance**:
- **Minimum**: 4GB RAM
- **Recommended**: 8-16GB RAM
- **With Ollama**: 16-32GB RAM

**Memory Usage Breakdown**:
- Application: 500MB-1GB
- Tree-sitter parsers: 200-500MB
- LLM context (per request): 100-500MB
- Ollama model (in-memory): 4-24GB (model-dependent)
- Buffer/cache: 1-2GB

#### Scaling Strategy

**Vertical Scaling**:
- Increase CPU/RAM for single instance
- Suitable for: Small to medium workloads
- Limit: Hardware constraints

**Horizontal Scaling**:
- Add more instances
- Suitable for: High concurrency, distributed processing
- Requires: Load balancer, shared state (database/cache)

**Auto-Scaling Triggers**:
- CPU utilization > 70%
- Memory utilization > 80%
- Queue depth > 100 jobs
- Request rate > 100 req/min

### Monitoring and Observability

#### Metrics to Monitor

**Application Metrics**:
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Active jobs/queue depth
- LLM API call latency
- Documentation generation time

**Infrastructure Metrics**:
- CPU utilization
- Memory usage
- Disk I/O
- Network throughput
- Database connection pool

**Business Metrics**:
- Documents generated per day
- Average processing time
- User activity
- API usage by provider

#### Monitoring Tools

**Recommended Stack**:
- **Metrics**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana) or Loki
- **Tracing**: Jaeger or Zipkin
- **APM**: New Relic, Datadog, or Application Insights

#### Alerting

**Critical Alerts**:
- Service downtime
- Error rate > 5%
- Response time > 30s (p95)
- Disk space < 20%
- Database connection failures

**Warning Alerts**:
- CPU > 80%
- Memory > 85%
- Queue depth > 500
- LLM API rate limit approaching

---

## Technical Architecture Details

### System Integration Architecture

#### LLM Provider Integration

```
┌─────────────────────────────────────────────────────────┐
│              LLM Integration Layer                       │
│                                                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │         BaseLLM (Abstract Interface)              │ │
│  │         - generate_documentation()                 │ │
│  │         - validate_config()                       │ │
│  │         - handle_errors()                         │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│        ┌─────────────────┼─────────────────┐             │
│        │                 │                 │               │
│  ┌─────▼─────┐   ┌───────▼──────┐  ┌──────▼──────┐       │
│  │ Ollama    │   │ MCP          │  │ Providers   │       │
│  │ LLM       │   │ LLM          │  │ (Extensible)│       │
│  │ - Local   │   │ - MCP Server │  │            │       │
│  │ - Models  │   │ - Remote     │  │            │       │
│  └─────┬─────┘   └──────┬────────┘  └─────┬──────┘       │
│        │               │                  │               │
│        └───────────────┼──────────────────┘             │
│                        │                                 │
│  ┌─────────────────────▼─────────────────────────────┐ │
│  │         LLM Factory                               │ │
│  │         - Provider Selection                      │ │
│  │         - Configuration Management                │ │
│  │         - Instance Creation                       │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Integration Patterns**:
- **Retry Logic**: Exponential backoff for transient failures
- **Rate Limiting**: Respect provider rate limits
- **Timeout Handling**: Configurable timeouts per provider
- **Error Handling**: Provider-specific error translation
- **Cost Tracking**: Track token usage per provider

#### Code Parsing Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Code Parsing Pipeline                       │
│                                                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │         Source Code Input                         │ │
│  │         - File Content                            │ │
│  │         - Language Detection                      │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐ │
│  │         Parser Selection                            │ │
│  │         - Language-based routing                    │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐ │
│  │         Tree-sitter AST Parsing                     │ │
│  │         - Build Abstract Syntax Tree                │ │
│  │         - Extract Code Structure                    │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐ │
│  │         Structure Extraction                         │ │
│  │         - Classes & Methods                         │ │
│  │         - Functions & Procedures                    │ │
│  │         - Imports & Dependencies                   │ │
│  │         - Comments & Documentation                   │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐ │
│  │         ParsedInfo Output                           │ │
│  │         - Structured JSON                           │ │
│  │         - Ready for LLM Processing                  │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Parser Capabilities**:
- **Java**: Full class hierarchy, annotations, generics
- **C#**: Classes, interfaces, properties, async/await
- **VB.NET**: Modules, classes, properties, events
- **F#**: Modules, types, discriminated unions
- **PHP**: Classes, traits, namespaces, closures

#### Dependency Analysis Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Dependency Analysis Engine                        │
│                                                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │         Dependency Graph Builder                  │ │
│  │         - Parse import statements                 │ │
│  │         - Build dependency edges                 │ │
│  │         - Create graph structure                 │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐ │
│  │         Analysis Algorithms                        │ │
│  │         - Circular Dependency Detection           │ │
│  │         - Orphaned File Detection                 │ │
│  │         - Coupling Analysis                       │ │
│  │         - Dependency Depth Calculation            │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐ │
│  │         Output Generators                          │ │
│  │         - JSON Export                              │ │
│  │         - DOT (Graphviz) Format                   │ │
│  │         - Mermaid Diagrams                         │ │
│  │         - Markdown Reports                        │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Data Processing Pipeline

#### Sequential Processing Flow

```
Input → Reader → Parser → Dependency Analysis → LLM Generation → Aggregation → Output
  │        │         │              │                  │              │           │
  │        │         │              │                  │              │           │
  │        │         │              │                  │              │           │
  └────────┴─────────┴──────────────┴──────────────────┴──────────────┴───────────┘
```

**Processing Stages**:

1. **Input Stage**
   - File upload / Git clone / Folder scan
   - Language detection
   - File filtering (exclude patterns)

2. **Reading Stage**
   - Content extraction
   - Metadata collection
   - File size validation

3. **Parsing Stage**
   - AST construction
   - Structure extraction
   - Comment extraction

4. **Analysis Stage** (Optional)
   - Dependency graph construction
   - Circular dependency detection
   - Coupling analysis

5. **Generation Stage**
   - Prompt construction
   - LLM API calls
   - Documentation generation

6. **Aggregation Stage**
   - Combine file documentation
   - Add diagrams
   - Format final output

7. **Output Stage**
   - Markdown generation
   - PDF conversion (optional)
   - File saving

#### Parallel Processing Opportunities

**Current**: Sequential file processing
**Future Enhancements**:
- Parallel file parsing (I/O bound)
- Batch LLM API calls (with rate limit respect)
- Parallel dependency analysis
- Concurrent PDF generation

### Security Architecture

#### Authentication & Authorization

```
┌─────────────────────────────────────────────────────────┐
│         Security Layer                                   │
│                                                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │         Authentication                             │ │
│  │         - API Keys                                 │ │
│  │         - OAuth2 / JWT                             │ │
│  │         - Session Management                       │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐ │
│  │         Authorization                               │ │
│  │         - Role-Based Access Control (RBAC)         │ │
│  │         - Resource Permissions                     │ │
│  │         - Rate Limiting                           │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐ │
│  │         Application                                 │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### Data Security

**At Rest**:
- Encrypted storage volumes
- Encrypted database backups
- Secure secret storage (Vault, Secrets Manager)

**In Transit**:
- TLS 1.2+ for all external communications
- VPN for internal service communication
- Certificate pinning for LLM API calls

**In Processing**:
- Memory encryption for sensitive data
- Secure code isolation
- No persistent storage of source code (configurable)

### Performance Architecture

#### Caching Strategy

**Multi-Level Caching**:

1. **Application Cache** (In-Memory)
   - Parsed ASTs (per file hash)
   - Configuration data
   - LLM responses (optional, with TTL)

2. **Distributed Cache** (Redis)
   - Shared parsed results
   - Dependency graphs
   - Job status

3. **Object Storage Cache**
   - Git repository clones
   - Generated documentation
   - Dependency maps

**Cache Invalidation**:
- File-based: Invalidate on file change (hash-based)
- Time-based: TTL for LLM responses
- Manual: Clear cache API endpoint

#### Optimization Techniques

**Code Parsing**:
- Lazy loading of parsers
- AST caching
- Incremental parsing (future)

**LLM Processing**:
- Request batching
- Streaming responses
- Token optimization
- Provider failover

**Documentation Generation**:
- Template caching
- Incremental updates
- Parallel PDF generation

### Error Handling Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Error Handling Strategy                          │
│                                                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │         Error Classification                     │ │
│  │         - Transient (Retry)                      │ │
│  │         - Permanent (Skip)                       │ │
│  │         - Critical (Fail)                        │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐ │
│  │         Error Handling                             │ │
│  │         - Retry with Backoff                       │ │
│  │         - Graceful Degradation                     │ │
│  │         - Error Logging                            │ │
│  │         - User Notification                        │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Error Categories**:
- **Network Errors**: Retry with exponential backoff
- **LLM API Errors**: Provider-specific handling
- **Parsing Errors**: Skip file, log warning
- **File System Errors**: Clear error message
- **Configuration Errors**: Validation and helpful messages

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

**Document Version**: 1.1  
**Last Updated**: January 2026  
**Product**: TechDocGen by IBMC  
**Author**: IBMC Development Team
