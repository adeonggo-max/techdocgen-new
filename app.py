"""
Modern Web UI for Technical Documentation Generator
Built with Streamlit
"""

import streamlit as st
import os
import sys
import re
from pathlib import Path
from typing import Optional, List
import tempfile
import shutil
import requests
from datetime import datetime

try:
    import streamlit_mermaid as stmd
    MERMAID_AVAILABLE = True
except ImportError:
    MERMAID_AVAILABLE = False

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.generator import DocumentationGenerator
    from src.config import Config
    from src.pdf_generator import PDFGenerator
except ImportError as e:
    st.error(f"Import error: {e}. Make sure all dependencies are installed.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="TechDocGen by IBMC - Technical Documentation Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .logo-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .logo-img {
        height: 50px;
        width: auto;
    }
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #0066CC 0%, #004499 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .brand-tagline {
        color: #0066CC;
        font-size: 0.9rem;
        font-weight: 500;
        margin-top: -0.5rem;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #6b7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #0066CC 0%, #004499 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0, 102, 204, 0.3);
    }
    .info-box {
        background: linear-gradient(135deg, #0066CC15 0%, #00449915 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #0066CC;
        margin: 1rem 0;
    }
    .success-box {
        background: linear-gradient(135deg, #10b98115 0%, #05966915 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #10b981;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'generated_docs' not in st.session_state:
    st.session_state.generated_docs = None
if 'generation_status' not in st.session_state:
    st.session_state.generation_status = None
if 'dependency_analysis' not in st.session_state:
    st.session_state.dependency_analysis = None
if 'dependency_map_data' not in st.session_state:
    st.session_state.dependency_map_data = None
if 'source_files' not in st.session_state:
    st.session_state.source_files = None

def load_config():
    """Load configuration"""
    config_path = st.session_state.get('config_path', 'config.yaml')
    try:
        return Config(config_path)
    except:
        return Config()

def get_ollama_models(base_url: str = "http://localhost:11434") -> List[str]:
    """Fetch available Ollama models from the API"""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [model.get("name", "") for model in data.get("models", [])]
            return sorted(models) if models else []
    except (requests.exceptions.RequestException, KeyError):
        pass
    return []

def extract_project_title(source_path: Optional[str], source_type: Optional[str]) -> str:
    """Extract project title from source path"""
    if not source_path:
        return "Technical_Documentation"
    
    try:
        title = ""
        if source_type == "Single File":
            # Use filename without extension
            title = Path(source_path).stem
        elif source_type == "Folder":
            # Use folder name
            title = Path(source_path).name
        elif source_type == "Git Repository":
            # Extract repo name from URL or path
            if source_path.startswith(('http://', 'https://')):
                # Extract from URL like https://github.com/user/repo.git
                repo_name = source_path.rstrip('/').rstrip('.git').split('/')[-1]
                title = repo_name
            else:
                # Local git path
                title = Path(source_path).name
        else:
            title = Path(source_path).stem if source_path else "Technical_Documentation"
        
        # Sanitize filename: remove invalid characters
        title = re.sub(r'[<>:"/\\|?*]', '_', title)
        title = title.replace(' ', '_')
        return title if title else "Technical_Documentation"
    except:
        return "Technical_Documentation"

def generate_summary(docs: str) -> str:
    """Extract or generate a summary from the documentation"""
    if not docs:
        return "No summary available."
    
    # Try to extract the first meaningful paragraph after the title
    lines = docs.split('\n')
    summary_lines = []
    found_content = False
    
    for i, line in enumerate(lines):
        # Skip title and metadata lines
        if line.strip().startswith('#') and 'Technical Documentation' in line:
            continue
        if 'Generated using' in line:
            continue
        if line.strip() == '---':
            continue
        if not line.strip():
            if found_content:
                break
            continue
        
        # Start collecting summary after skipping header
        if not found_content and line.strip():
            found_content = True
        
        if found_content:
            # Stop at first heading or after 3-4 sentences
            if line.strip().startswith('##'):
                break
            summary_lines.append(line.strip())
            if len(summary_lines) >= 4 and any(line.strip().endswith('.') for line in summary_lines[-3:]):
                break
    
    summary = ' '.join(summary_lines).strip()
    
    # If no good summary found, create a basic one
    if not summary or len(summary) < 50:
        # Count files and languages
        file_count = docs.count('### ')  # Count file sections
        languages = set()
        for lang in ['java', 'csharp', 'vbnet', 'fsharp', 'php']:
            if f'{lang.upper()} Files' in docs:
                languages.add(lang)
        
        summary = f"This documentation covers {file_count} source file(s) "
        if languages:
            summary += f"written in {', '.join(languages)}. "
        summary += "The documentation includes detailed explanations of classes, methods, and code structure."
    
    return summary

def render_markdown_with_mermaid(content: str):
    """Render markdown content, extracting and rendering Mermaid diagrams separately"""
    # Split content by Mermaid code blocks
    pattern = r'(```mermaid.*?```)'
    parts = re.split(pattern, content, flags=re.DOTALL)
    
    for part in parts:
        if part.strip().startswith('```mermaid'):
            # Extract Mermaid diagram code
            diagram_code = re.sub(r'```mermaid\s*', '', part)
            diagram_code = re.sub(r'```\s*$', '', diagram_code, flags=re.MULTILINE)
            # Clean up: remove leading/trailing whitespace and normalize line endings
            diagram_code = diagram_code.strip()
            # Remove any empty lines at start/end
            lines = [line for line in diagram_code.split('\n') if line.strip() or len([l for l in diagram_code.split('\n') if l.strip()]) > 0]
            diagram_code = '\n'.join(lines).strip()
            
            # Render Mermaid diagram as SVG
            if MERMAID_AVAILABLE:
                try:
                    # Validate basic syntax before rendering
                    if 'sequenceDiagram' in diagram_code and 'participant' in diagram_code:
                        stmd.st_mermaid(diagram_code)
                    else:
                        # If syntax looks invalid, show as code
                        st.warning("⚠️ Diagram syntax validation failed, showing as code:")
                        st.code(diagram_code, language="mermaid")
                except Exception as e:
                    # Show error and fallback to code block
                    st.warning(f"⚠️ Could not render diagram: {str(e)}")
                    with st.expander("View diagram code"):
                        st.code(diagram_code, language="mermaid")
            else:
                # Fallback: show as code block with note
                st.info("💡 Install streamlit-mermaid to view diagrams: `pip install streamlit-mermaid`")
                st.code(diagram_code, language="mermaid")
        else:
            # Regular markdown content
            if part.strip():
                st.markdown(part)

def main():
    # Header with IBMC branding
    logo_path = Path(__file__).parent / "assets" / "ibmc-logo.svg"
    
    # Create header with logo and branding
    header_col1, header_col2 = st.columns([1, 5])
    with header_col1:
        if logo_path.exists():
            with open(logo_path, 'r') as f:
                logo_svg = f.read()
            # Adjust logo size for header
            logo_svg = logo_svg.replace('width="120" height="40"', 'width="80" height="30"')
            st.markdown(logo_svg, unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size: 2rem; font-weight: bold; color: #0066CC;">IBMC</div>', unsafe_allow_html=True)
    
    with header_col2:
        st.markdown('<h1 class="main-header">TechDocGen</h1>', unsafe_allow_html=True)
        st.markdown('<p class="brand-tagline">by IBMC</p>', unsafe_allow_html=True)
    
    st.markdown('<p class="sub-header">Generate comprehensive technical documentation from your source code using AI</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        # LLM Provider Selection
        config = load_config()
        available_providers = ['ollama', 'anthropic', 'openai', 'mcp']
        default_provider = config.get_default_provider()
        
        selected_provider = st.selectbox(
            "🤖 LLM Provider",
            available_providers,
            index=available_providers.index(default_provider) if default_provider in available_providers else 0,
            help="Choose the LLM provider to generate documentation"
        )
        
        # Provider-specific settings
        if selected_provider == 'ollama':
            st.markdown("#### Ollama Settings")
            ollama_url = st.text_input(
                "Base URL",
                value=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                help="Ollama server URL"
            )
            
            # Get available models from Ollama
            available_models = get_ollama_models(ollama_url)
            
            # Get default model from config or env
            config_ollama = config.config.get("llm_providers", {}).get("ollama", {})
            default_model = os.getenv("OLLAMA_MODEL", config_ollama.get("model", "llama3.2"))
            
            if available_models:
                # Show dropdown with available models
                if default_model in available_models:
                    default_index = available_models.index(default_model)
                else:
                    default_index = 0
                
                ollama_model = st.selectbox(
                    "Model",
                    options=available_models,
                    index=default_index,
                    help="Select an Ollama model. Make sure Ollama is running and the model is pulled."
                )
                
                # Show refresh button to reload models
                if st.button("🔄 Refresh Models", use_container_width=True, help="Reload available models from Ollama"):
                    st.rerun()
            else:
                # Fallback to text input if models can't be fetched
                st.warning("⚠️ Could not fetch models from Ollama. Make sure Ollama is running.")
                ollama_model = st.text_input(
                    "Model",
                    value=default_model,
                    help="Enter Ollama model name manually (e.g., deepseek-coder:6.7b). Make sure the model is pulled: ollama pull <model-name>"
                )
                if st.button("🔄 Refresh Models", use_container_width=True, help="Try to reload available models"):
                    st.rerun()
            
            # Store in session state for use during generation
            st.session_state.ollama_url = ollama_url
            st.session_state.ollama_model = ollama_model
        
        elif selected_provider == 'anthropic':
            st.markdown("#### Anthropic Settings")
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            if api_key:
                st.success("✅ API Key configured")
            else:
                st.warning("⚠️ Set ANTHROPIC_API_KEY in .env")
        
        elif selected_provider == 'openai':
            st.markdown("#### OpenAI Settings")
            api_key = os.getenv("OPENAI_API_KEY", "")
            if api_key:
                st.success("✅ API Key configured")
            else:
                st.warning("⚠️ Set OPENAI_API_KEY in .env")
        
        st.markdown("---")
        
        # Advanced Settings
        with st.expander("🔧 Advanced Settings"):
            max_file_size = st.number_input(
                "Max File Size (MB)",
                min_value=1,
                max_value=100,
                value=10,
                help="Maximum file size to process"
            )
            
            include_comments = st.checkbox("Include Comments", value=True)
            include_imports = st.checkbox("Include Imports", value=True)
    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["📁 Source Selection", "⚡ Generate", "📄 Preview", "🔗 Dependency Map"])
    
    with tab1:
        st.markdown("### Select Source Code")
        
        source_type = st.radio(
            "Source Type",
            ["Single File", "Folder", "Git Repository"],
            horizontal=True,
            help="Choose the type of source to document"
        )
        
        source_path = None
        
        if source_type == "Single File":
            uploaded_file = st.file_uploader(
                "Upload a source file",
                type=['java', 'cs', 'vb', 'fs', 'fsx', 'cshtml', 'vbhtml', 'php'],
                help="Upload a Java, .NET (C#, VB.NET, F#), or PHP file"
            )
            if uploaded_file:
                # Save uploaded file temporarily
                temp_dir = Path(tempfile.mkdtemp())
                source_path = str(temp_dir / uploaded_file.name)
                with open(source_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                st.session_state.temp_source_path = source_path
                st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        elif source_type == "Folder":
            folder_path = st.text_input(
                "Folder Path",
                placeholder="/path/to/your/project",
                help="Enter the path to your project folder"
            )
            if folder_path and Path(folder_path).exists():
                source_path = folder_path
                st.success(f"✅ Folder found: {folder_path}")
            elif folder_path:
                st.error(f"❌ Folder not found: {folder_path}")
        
        elif source_type == "Git Repository":
            git_url = st.text_input(
                "Git Repository URL",
                placeholder="https://github.com/user/repo.git",
                help="Enter Git repository URL or local path"
            )
            branch = st.text_input(
                "Branch (optional)",
                placeholder="main",
                help="Specify branch to use"
            )
            if git_url:
                source_path = git_url
                st.session_state.git_branch = branch if branch else None
                st.info(f"📦 Repository: {git_url}")
    
    with tab2:
        st.markdown("### Generate Documentation")
        
        if source_path:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.info(f"📂 Source: {source_path}")
                if source_type == "Git Repository" and st.session_state.get('git_branch'):
                    st.info(f"🌿 Branch: {st.session_state.git_branch}")
            
            with col2:
                generate_btn = st.button("🚀 Generate Documentation", type="primary", use_container_width=True)
            
            if generate_btn:
                # Store source info in session state
                st.session_state.source_path = source_path
                st.session_state.source_type = source_type
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Store original environment variables for restoration
                original_ollama_model = None
                original_ollama_url = None
                
                try:
                    status_text.text("🔄 Initializing generator...")
                    progress_bar.progress(10)
                    
                    # Update config with UI-selected Ollama settings if applicable
                    if selected_provider == 'ollama' and st.session_state.get('ollama_model'):
                        # Temporarily set environment variables to override config
                        original_ollama_model = os.getenv("OLLAMA_MODEL")
                        original_ollama_url = os.getenv("OLLAMA_BASE_URL")
                        os.environ["OLLAMA_MODEL"] = st.session_state.ollama_model
                        if st.session_state.get('ollama_url'):
                            os.environ["OLLAMA_BASE_URL"] = st.session_state.ollama_url
                    
                    # Initialize generator
                    generator = DocumentationGenerator(llm_provider=selected_provider)
                    
                    status_text.text("📖 Reading source code...")
                    progress_bar.progress(10)
                    
                    # Read source files first
                    if source_type == "Single File":
                        from src.readers import FileReader
                        reader = FileReader(source_path, generator.config.config)
                        files = reader.read()
                    elif source_type == "Folder":
                        from src.readers import FolderReader
                        reader = FolderReader(source_path, generator.config.config)
                        files = reader.read()
                    elif source_type == "Git Repository":
                        from src.readers import GitReader
                        branch = st.session_state.get('git_branch')
                        reader = GitReader(source_path, branch, generator.config.config)
                        files = reader.read()
                    
                    # Store files in session state for dependency analysis
                    st.session_state.source_files = files
                    
                    total_files = len(files)
                    progress_bar.progress(20)
                    status_text.text(f"✅ Found {total_files} file(s). Starting AI documentation generation...")
                    
                    # Progress callback for file processing
                    file_status = st.empty()
                    
                    def update_progress(current, total, filename):
                        progress_pct = 20 + int((current / total) * 70)  # 20-90% range
                        progress_bar.progress(progress_pct)
                        file_status.text(f"🤖 Processing file {current}/{total}: {filename}")
                    
                    # Generate documentation with progress tracking
                    if source_type == "Single File":
                        docs = generator.generate_from_file(source_path, update_progress)
                    elif source_type == "Folder":
                        docs = generator.generate_from_folder(source_path, update_progress)
                    elif source_type == "Git Repository":
                        branch = st.session_state.get('git_branch')
                        docs = generator.generate_from_git(source_path, branch, update_progress)
                    
                    file_status.empty()
                    status_text.text("✅ Documentation generation complete!")
                    progress_bar.progress(90)
                    
                    # Save to session state
                    st.session_state.generated_docs = docs
                    st.session_state.generation_status = "success"
                    
                    status_text.text("💾 Saving documentation...")
                    progress_bar.progress(90)
                    
                    # Save to file
                    output_file = generator.save_documentation(docs)
                    st.session_state.output_file = str(output_file)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Complete!")
                    
                    st.success("✅ Documentation generated successfully!")
                    st.balloons()
                    
                    # Cleanup temp files if any
                    if source_type == "Single File" and st.session_state.get('temp_source_path'):
                        temp_path = Path(st.session_state.temp_source_path)
                        if temp_path.exists():
                            try:
                                shutil.rmtree(temp_path.parent)
                            except:
                                pass
                    
                except Exception as e:
                    progress_bar.progress(0)
                    status_text.text("❌ Error occurred")
                    st.error(f"❌ Error: {str(e)}")
                    st.session_state.generation_status = "error"
                    st.session_state.error_message = str(e)
                    
                    # Show detailed error in expander
                    with st.expander("🔍 Error Details"):
                        import traceback
                        st.code(traceback.format_exc())
                finally:
                    # Restore original environment variables
                    if selected_provider == 'ollama':
                        if original_ollama_model is None:
                            os.environ.pop("OLLAMA_MODEL", None)
                        else:
                            os.environ["OLLAMA_MODEL"] = original_ollama_model
                        if original_ollama_url is None:
                            os.environ.pop("OLLAMA_BASE_URL", None)
                        else:
                            os.environ["OLLAMA_BASE_URL"] = original_ollama_url
        else:
            st.warning("⚠️ Please select a source in the 'Source Selection' tab first.")
    
    with tab3:
        st.markdown("### Preview & Download")
        
        if st.session_state.generated_docs:
            # Get project title and date for PDF filename
            source_path = st.session_state.get('source_path')
            source_type = st.session_state.get('source_type')
            project_title = extract_project_title(source_path, source_type)
            current_date = datetime.now().strftime("%d-%m-%Y")
            pdf_filename = f"{project_title}_{current_date}.pdf"
            
            # Summary Section
            st.markdown("#### 📋 Summary")
            summary = generate_summary(st.session_state.generated_docs)
            st.info(summary)
            
            # Source Files List
            if st.session_state.get('source_files'):
                st.markdown("#### 📁 Source Files")
                files = st.session_state.source_files
                
                # Group files by language
                files_by_lang = {}
                for file_info in files:
                    lang = file_info.get('language', 'unknown')
                    if lang not in files_by_lang:
                        files_by_lang[lang] = []
                    files_by_lang[lang].append(file_info)
                
                # Display files in expandable sections by language
                for lang, lang_files in sorted(files_by_lang.items()):
                    if lang == 'unknown':
                        continue
                    with st.expander(f"{lang.upper()} Files ({len(lang_files)})", expanded=False):
                        for file_info in lang_files:
                            file_path = file_info.get('relative_path') or file_info.get('path', 'Unknown')
                            file_name = file_info.get('name', Path(file_path).name)
                            st.text(f"• {file_name}")
                            st.caption(f"  {file_path}")
            
            st.markdown("---")
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Status", "✅ Ready")
            with col2:
                doc_length = len(st.session_state.generated_docs)
                st.metric("Documentation Size", f"{doc_length:,} chars")
            with col3:
                lines = st.session_state.generated_docs.count('\n')
                st.metric("Lines", f"{lines:,}")
            with col4:
                if st.session_state.get('output_file'):
                    st.metric("Saved To", "✅ Yes")
            
            # Download buttons
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📥 Download Markdown",
                    data=st.session_state.generated_docs,
                    file_name="technical_documentation.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            with col2:
                # Generate PDF on demand
                if 'pdf_generator' not in st.session_state:
                    st.session_state.pdf_generator = PDFGenerator()
                
                try:
                    pdf_bytes = st.session_state.pdf_generator.generate_pdf_from_markdown(
                        st.session_state.generated_docs
                    )
                    st.download_button(
                        label="📄 Download PDF (Confluence Style)",
                        data=pdf_bytes.getvalue(),
                        file_name=pdf_filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"❌ PDF generation failed: {str(e)}")
                    st.info("💡 Make sure all dependencies are installed: `pip install -r requirements.txt`")
                    with st.expander("🔍 Error Details"):
                        import traceback
                        st.code(traceback.format_exc())
            
            st.markdown("---")
            
            # Preview
            st.markdown("### Preview")
            with st.expander("📖 View Full Documentation", expanded=True):
                # Render markdown with Mermaid diagrams
                render_markdown_with_mermaid(st.session_state.generated_docs)
        else:
            st.info("👆 Generate documentation first to see preview here.")
    
    with tab4:
        st.markdown("### 🔗 Dependency Map Analysis")
        
        if st.session_state.source_files and len(st.session_state.source_files) > 0:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.info(f"📂 {len(st.session_state.source_files)} file(s) available for analysis")
            
            with col2:
                analyze_btn = st.button("🔍 Analyze Dependencies", type="primary", use_container_width=True, key="analyze_deps")
            
            if analyze_btn:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Store original environment variables for restoration
                original_ollama_model = None
                original_ollama_url = None
                
                try:
                    status_text.text("🔄 Initializing dependency analyzer...")
                    progress_bar.progress(10)
                    
                    # Update config with UI-selected Ollama settings if applicable
                    if selected_provider == 'ollama' and st.session_state.get('ollama_model'):
                        # Temporarily set environment variables to override config
                        original_ollama_model = os.getenv("OLLAMA_MODEL")
                        original_ollama_url = os.getenv("OLLAMA_BASE_URL")
                        os.environ["OLLAMA_MODEL"] = st.session_state.ollama_model
                        if st.session_state.get('ollama_url'):
                            os.environ["OLLAMA_BASE_URL"] = st.session_state.ollama_url
                    
                    # Initialize generator
                    generator = DocumentationGenerator(llm_provider=selected_provider)
                    
                    status_text.text("📊 Analyzing dependencies...")
                    progress_bar.progress(30)
                    
                    # Analyze dependencies
                    analysis = generator.dependency_analyzer.analyze_files(
                        st.session_state.source_files, 
                        generator.parsers
                    )
                    
                    progress_bar.progress(80)
                    status_text.text("✅ Analysis complete!")
                    
                    # Store in session state
                    st.session_state.dependency_analysis = analysis
                    st.session_state.dependency_map_data = generator.dependency_analyzer._build_dependency_map()
                    st.session_state.dependency_analyzer = generator.dependency_analyzer
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Ready!")
                    
                    st.success("✅ Dependency analysis complete!")
                    st.rerun()
                    
                except Exception as e:
                    progress_bar.progress(0)
                    status_text.text("❌ Error occurred")
                    st.error(f"❌ Error: {str(e)}")
                    with st.expander("🔍 Error Details"):
                        import traceback
                        st.code(traceback.format_exc())
                finally:
                    # Restore original environment variables
                    if selected_provider == 'ollama':
                        if original_ollama_model is None:
                            os.environ.pop("OLLAMA_MODEL", None)
                        else:
                            os.environ["OLLAMA_MODEL"] = original_ollama_model
                        if original_ollama_url is None:
                            os.environ.pop("OLLAMA_BASE_URL", None)
                        else:
                            os.environ["OLLAMA_BASE_URL"] = original_ollama_url
            
            # Display analysis results
            if st.session_state.dependency_analysis:
                analysis = st.session_state.dependency_analysis
                dep_map = st.session_state.dependency_map_data
                
                # Metrics
                st.markdown("#### 📊 Analysis Metrics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Files", analysis['file_count'])
                with col2:
                    st.metric("Total Classes", analysis['class_count'])
                with col3:
                    st.metric("Dependencies", analysis['dependency_count'])
                with col4:
                    st.metric("External Deps", analysis['external_dependency_count'])
                
                st.markdown("---")
                
                # Visual Dependency Graph
                st.markdown("#### 🗺️ Dependency Graph")
                
                # Generate Mermaid diagram
                if dep_map and len(dep_map.get('edges', [])) > 0:
                    mermaid_code = "graph TD\n"
                    
                    # Limit nodes for readability (show top 50 nodes)
                    nodes_to_show = dep_map['nodes'][:50]
                    node_ids = {}
                    for node in nodes_to_show:
                        node_id = node['path'].replace('/', '_').replace('\\', '_').replace('.', '_').replace(' ', '_')[:30]
                        node_ids[node['id']] = node_id
                    
                    # Add edges (limit to 100 for performance)
                    edges_added = set()
                    for edge in dep_map['edges'][:100]:
                        source_id = edge['source']
                        target_id = edge['target']
                        
                        if source_id in node_ids and target_id in node_ids:
                            source_label = node_ids[source_id]
                            target_label = node_ids[target_id]
                            edge_key = f"{source_label}->{target_label}"
                            
                            if edge_key not in edges_added:
                                source_name = Path(edge['source']).stem[:20]
                                target_name = Path(edge['target']).stem[:20]
                                mermaid_code += f'  {source_label}["{source_name}"] --> {target_label}["{target_name}"]\n'
                                edges_added.add(edge_key)
                    
                    if MERMAID_AVAILABLE:
                        try:
                            stmd.st_mermaid(mermaid_code)
                        except Exception as e:
                            st.warning(f"⚠️ Could not render diagram: {str(e)}")
                            with st.expander("View diagram code"):
                                st.code(mermaid_code, language="mermaid")
                    else:
                        st.info("💡 Install streamlit-mermaid to view diagrams: `pip install streamlit-mermaid`")
                        with st.expander("View diagram code"):
                            st.code(mermaid_code, language="mermaid")
                else:
                    st.info("No dependencies found to visualize.")
                
                st.markdown("---")
                
                # Circular Dependencies
                if analysis.get('circular_dependencies'):
                    st.markdown("#### ⚠️ Circular Dependencies")
                    st.warning(f"Found {len(analysis['circular_dependencies'])} circular dependency cycle(s)")
                    for idx, cycle in enumerate(analysis['circular_dependencies'][:10], 1):
                        cycle_path = " → ".join([Path(f).name for f in cycle])
                        st.code(f"Cycle {idx}: {cycle_path}")
                
                # Orphaned Files
                if analysis.get('orphaned_files'):
                    st.markdown("#### 📦 Orphaned Files")
                    st.info(f"Found {len(analysis['orphaned_files'])} file(s) with no dependencies")
                    with st.expander("View orphaned files"):
                        for file_path in analysis['orphaned_files'][:20]:
                            st.text(f"• {file_path}")
                
                # Highly Coupled Files
                if analysis.get('highly_coupled_files'):
                    st.markdown("#### 🔗 Highly Coupled Files")
                    st.info("Files with high coupling (many dependencies or dependents)")
                    
                    # Create a table
                    try:
                        import pandas as pd
                        coupled_data = []
                        for item in analysis['highly_coupled_files'][:15]:
                            coupled_data.append({
                                'File': Path(item['file']).name,
                                'Dependencies': item['dependencies'],
                                'Dependents': item['dependents'],
                                'Total Coupling': item['total_coupling']
                            })
                        
                        if coupled_data:
                            df = pd.DataFrame(coupled_data)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                    except ImportError:
                        st.info("Install pandas for table view: `pip install pandas`")
                        for item in analysis['highly_coupled_files'][:15]:
                            st.text(f"• {Path(item['file']).name}: {item['total_coupling']} total coupling")
                
                st.markdown("---")
                
                # Export Options
                st.markdown("#### 💾 Export Dependency Map")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("📄 Export JSON", use_container_width=True, key="export_json"):
                        if 'dependency_analyzer' in st.session_state:
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                                output_file = st.session_state.dependency_analyzer.export_json(tmp.name)
                                with open(output_file, 'r') as f:
                                    json_data = f.read()
                                st.download_button(
                                    label="📥 Download JSON",
                                    data=json_data,
                                    file_name="dependency_map.json",
                                    mime="application/json",
                                    use_container_width=True,
                                    key="dl_json"
                                )
                
                with col2:
                    if st.button("🔄 Export DOT", use_container_width=True, key="export_dot"):
                        if 'dependency_analyzer' in st.session_state:
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as tmp:
                                output_file = st.session_state.dependency_analyzer.export_dot(tmp.name)
                                with open(output_file, 'r') as f:
                                    dot_data = f.read()
                                st.download_button(
                                    label="📥 Download DOT",
                                    data=dot_data,
                                    file_name="dependency_map.dot",
                                    mime="text/plain",
                                    use_container_width=True,
                                    key="dl_dot"
                                )
                
                with col3:
                    if st.button("🌊 Export Mermaid", use_container_width=True, key="export_mermaid"):
                        if 'dependency_analyzer' in st.session_state:
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as tmp:
                                output_file = st.session_state.dependency_analyzer.export_mermaid(tmp.name)
                                with open(output_file, 'r') as f:
                                    mermaid_data = f.read()
                                st.download_button(
                                    label="📥 Download Mermaid",
                                    data=mermaid_data,
                                    file_name="dependency_map.mmd",
                                    mime="text/plain",
                                    use_container_width=True,
                                    key="dl_mermaid"
                                )
                
                with col4:
                    if st.button("📝 Export Markdown", use_container_width=True, key="export_md"):
                        if 'dependency_analyzer' in st.session_state:
                            markdown_report = st.session_state.dependency_analyzer.generate_markdown_report()
                            st.download_button(
                                label="📥 Download Markdown",
                                data=markdown_report,
                                file_name="dependency_map.md",
                                mime="text/markdown",
                                use_container_width=True,
                                key="dl_md"
                            )
        else:
            st.info("👆 Please select and process source code first in the 'Source Selection' and 'Generate' tabs.")
            st.markdown("""
            **How to use Dependency Map:**
            1. Go to **Source Selection** tab and select your source code
            2. Go to **Generate** tab and click "Generate Documentation" (this will read your files)
            3. Come back to this tab and click "Analyze Dependencies"
            4. View the interactive dependency graph and analysis results
            """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #6b7280; padding: 2rem;'>"
        "<strong>TechDocGen by IBMC</strong> - Powered by AI | Support: Java, .NET (C#, VB.NET, F#), PHP"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()

