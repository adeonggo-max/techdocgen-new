# TechDocGen by IBMC

A comprehensive tool for generating technical documentation from source code in Java, .NET (C#, VB.NET, F#), and PHP. Supports reading from single files, folders, or Git repositories, and uses LLMs (OpenAI, Anthropic, Ollama, or MCP) to generate high-quality documentation.

**TechDocGen by IBMC** - Empowering developers with AI-driven documentation generation.

## Features

- **Multiple Source Types**: Read from single files, folders, or Git repositories
- **Language Support**: Java, .NET (C#, VB.NET, F#), and PHP
- **LLM Integration**: Support for multiple LLM providers:
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic (Claude)
  - Ollama (Local LLMs)
  - MCP (Model Context Protocol)
- **Intelligent Parsing**: Extracts classes, methods, interfaces, imports, and more
- **Markdown Output**: Generates well-formatted markdown documentation

## Installation

1. Clone or download this repository

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

**For Linux/Mac:**
```bash
pip install -r requirements.txt
```

**For Windows (recommended if you encounter gobject-2-0-0 errors):**
```bash
pip install -r requirements-windows.txt
```

**Note:** The main `requirements.txt` includes `weasyprint` which requires GTK/GObject libraries that can be problematic on Windows. If you encounter errors like "OSEerror gobeject-2-0-0 error" on Windows, use `requirements-windows.txt` instead, which uses `xhtml2pdf` (a Windows-compatible PDF generator).

4. (Optional) Set up environment variables:
```bash
cp .env.example .env  # On Windows: copy .env.example .env
# Edit .env with your API keys
```

## Configuration

Edit `config.yaml` to customize:
- Supported languages and file extensions
- LLM provider settings
- Documentation preferences
- Output settings

## Usage

### Web UI (Recommended)

Launch the modern web interface:

```bash
# Using the convenience script
./run_ui.sh

# Or directly with Streamlit
streamlit run app.py
```

The web UI provides:
- 🎨 Modern, intuitive interface
- 📁 Easy source selection (file upload, folder, or Git repo)
- 🤖 LLM provider selection and configuration
- ⚡ Real-time generation progress
- 📄 Live preview of generated documentation
- 📥 One-click download

The interface will open in your default browser at `http://localhost:8501`

### CLI Usage

### Basic Usage

Generate documentation from a single file:
```bash
python main.py --source path/to/file.java --type file
```

Generate documentation from a folder:
```bash
python main.py --source path/to/project --type folder
```

Generate documentation from a Git repository:
```bash
python main.py --source https://github.com/user/repo.git --type git
```

### Advanced Usage

Specify LLM provider:
```bash
python main.py --source ./src --type folder --provider ollama
```

Specify output file:
```bash
python main.py --source ./src --type folder --output ./my_docs.md
```

Use specific Git branch:
```bash
python main.py --source https://github.com/user/repo.git --type git --branch develop
```

Custom config file:
```bash
python main.py --source ./src --type folder --config custom_config.yaml
```

Verbose output:
```bash
python main.py --source ./src --type folder --verbose
```

## LLM Provider Setup

### Ollama (Local LLM - Recommended for Privacy)

1. Install Ollama from https://ollama.ai
2. Pull a model:
```bash
ollama pull llama3.2
```
3. Use with the generator:
```bash
python main.py --source ./src --provider ollama
```

### OpenAI

1. Get API key from https://platform.openai.com
2. Set environment variable:
```bash
export OPENAI_API_KEY=your_key_here
```
3. Or add to `.env` file
4. Use:
```bash
python main.py --source ./src --provider openai
```

### Anthropic (Claude)

1. Get API key from https://console.anthropic.com
2. Set environment variable:
```bash
export ANTHROPIC_API_KEY=your_key_here
```
3. Use:
```bash
python main.py --source ./src --provider anthropic
```

### MCP (Model Context Protocol)

1. Set up MCP server
2. Configure in `config.yaml`:
```yaml
llm_providers:
  mcp:
    enabled: true
    server_url: http://localhost:8000
    model: your_model
```
3. Use:
```bash
python main.py --source ./src --provider mcp
```

## Project Structure

```
TechDocGen by IBMC/
├── src/
│   ├── config.py              # Configuration management
│   ├── generator.py            # Main documentation generator
│   ├── readers/                # Source code readers
│   │   ├── base_reader.py
│   │   ├── file_reader.py
│   │   ├── folder_reader.py
│   │   └── git_reader.py
│   ├── parsers/                # Language parsers
│   │   ├── base_parser.py
│   │   ├── java_parser.py
│   │   ├── csharp_parser.py
│   │   ├── vbnet_parser.py
│   │   ├── fsharp_parser.py
│   │   └── php_parser.py
│   └── llm/                    # LLM integrations
│       ├── base_llm.py
│       ├── openai_llm.py
│       ├── anthropic_llm.py
│       ├── ollama_llm.py
│       ├── mcp_llm.py
│       └── llm_factory.py
├── main.py                     # CLI entry point
├── config.yaml                 # Configuration file
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Examples

### Example 1: Document a Java Project
```bash
python main.py --source ./my-java-project/src --type folder --provider ollama --output java_docs.md
```

### Example 2: Document a .NET Solution
```bash
python main.py --source ./MySolution --type folder --provider openai
```

### Example 3: Document a PHP Application from Git
```bash
python main.py --source https://github.com/user/php-app.git --type git --branch main --provider ollama
```

## Configuration Options

### Exclude Patterns

Add patterns to exclude files/directories in `config.yaml`:
```yaml
documentation:
  exclude_patterns:
    - "**/node_modules/**"
    - "**/vendor/**"
    - "**/bin/**"
```

### File Size Limits

Set maximum file size:
```yaml
documentation:
  max_file_size_mb: 10
```

### LLM Settings

Customize LLM behavior:
```yaml
llm_providers:
  ollama:
    model: llama3.2
    temperature: 0.3
    base_url: http://localhost:11434
```

## Troubleshooting

### Windows Installation Issues

**Error: "OSEerror gobeject-2-0-0 error" or similar GTK/GObject errors**

This occurs because `weasyprint` requires GTK/GObject libraries that are difficult to install on Windows. Solution:

1. Use the Windows-specific requirements file:
   ```bash
   pip install -r requirements-windows.txt
   ```

2. The application will automatically use `xhtml2pdf` instead of `weasyprint` on Windows, which doesn't require GTK dependencies.

3. If you still encounter issues, you can manually install:
   ```bash
   pip uninstall weasyprint
   pip install xhtml2pdf
   ```

### Ollama Connection Error
- Ensure Ollama is running: `ollama serve`
- Check the base URL in config matches your Ollama setup

### Git Repository Issues
- For private repos, ensure you have proper authentication
- Use SSH URLs for private repositories

### Large Projects
- Increase `max_file_size_mb` in config if needed
- Consider processing specific folders instead of entire projects

### PDF Generation Issues

**Error: "usedforsecurity is not a valid keyword argument for OpenSSL"**

This error occurs when using older versions of `xhtml2pdf` or `reportlab` with newer Python/OpenSSL versions. Solution:

1. Upgrade xhtml2pdf and reportlab:
   ```bash
   pip install --upgrade xhtml2pdf>=0.2.17 reportlab>=4.0.0
   ```

2. The code includes an automatic workaround, but if issues persist, reinstall:
   ```bash
   pip uninstall xhtml2pdf reportlab
   pip install xhtml2pdf>=0.2.17 reportlab>=4.0.0
   ```

**General PDF Generation Issues:**
- On Windows, the app automatically falls back to `xhtml2pdf` if `weasyprint` is unavailable
- If PDF generation fails, check that either `weasyprint` (Linux/Mac) or `xhtml2pdf` (Windows) is installed
- Ensure you're using xhtml2pdf version 0.2.17+ for OpenSSL compatibility

## License

This project is provided as-is for generating technical documentation.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for improvements.

