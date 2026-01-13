"""PDF generator with Confluence-style formatting"""

import re
import sys
import hashlib
from io import BytesIO
from pathlib import Path
from typing import Optional
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter

# Fix for usedforsecurity parameter issue with xhtml2pdf/reportlab on newer Python/OpenSSL
# This patches hashlib functions to handle usedforsecurity parameter compatibility
def _patch_hashlib_for_xhtml2pdf():
    """Patch hashlib to handle usedforsecurity parameter compatibility issues"""
    # Store original functions
    original_md5 = hashlib.md5
    original_sha1 = hashlib.sha1
    original_sha256 = hashlib.sha256
    original_sha512 = getattr(hashlib, 'sha512', None)
    
    def safe_hash_wrapper(original_func):
        """Wrapper that strips usedforsecurity if it causes errors"""
        def wrapper(*args, **kwargs):
            # Try with usedforsecurity if provided
            if 'usedforsecurity' in kwargs:
                try:
                    return original_func(*args, **kwargs)
                except (TypeError, ValueError) as e:
                    # If usedforsecurity causes an error, remove it and retry
                    if 'usedforsecurity' in str(e).lower() or 'openssl' in str(e).lower():
                        kwargs = kwargs.copy()
                        kwargs.pop('usedforsecurity', None)
                        return original_func(*args, **kwargs)
                    raise
            else:
                return original_func(*args, **kwargs)
        return wrapper
    
    # Apply patches
    hashlib.md5 = safe_hash_wrapper(original_md5)
    hashlib.sha1 = safe_hash_wrapper(original_sha1)
    hashlib.sha256 = safe_hash_wrapper(original_sha256)
    if original_sha512:
        hashlib.sha512 = safe_hash_wrapper(original_sha512)

# Apply the patch before importing xhtml2pdf to prevent errors during import
_patch_hashlib_for_xhtml2pdf()

# Try to import WeasyPrint (may fail on Windows)
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    WEASYPRINT_ERROR = str(e)

# Try to import xhtml2pdf as fallback (Windows-compatible)
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except (ImportError, TypeError) as e:
    XHTML2PDF_AVAILABLE = False
    XHTML2PDF_ERROR = str(e) if 'ImportError' not in str(type(e)) else None


class PDFGenerator:
    """Generate PDF from markdown with Confluence-style formatting"""
    
    CONFLUENCE_CSS = """
    @page {
        size: A4;
        margin: 2cm 2cm 2.5cm 2cm;
        @top-center {
            content: "TechDocGen by IBMC - Technical Documentation";
            font-size: 10pt;
            color: #707070;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        @bottom-center {
            content: "Page " counter(page) " of " counter(pages);
            font-size: 10pt;
            color: #707070;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
    }
    
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: 14px;
        line-height: 1.6;
        color: #172B4D;
        background-color: #FFFFFF;
        margin: 0;
        padding: 0;
    }
    
    h1 {
        font-size: 32px;
        font-weight: 600;
        color: #172B4D;
        margin-top: 0;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid #DFE1E6;
    }
    
    h2 {
        font-size: 24px;
        font-weight: 600;
        color: #172B4D;
        margin-top: 32px;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid #DFE1E6;
    }
    
    h3 {
        font-size: 20px;
        font-weight: 600;
        color: #172B4D;
        margin-top: 24px;
        margin-bottom: 12px;
    }
    
    h4 {
        font-size: 16px;
        font-weight: 600;
        color: #172B4D;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    
    h5 {
        font-size: 14px;
        font-weight: 600;
        color: #172B4D;
        margin-top: 16px;
        margin-bottom: 8px;
    }
    
    h6 {
        font-size: 12px;
        font-weight: 600;
        color: #172B4D;
        margin-top: 12px;
        margin-bottom: 6px;
    }
    
    p {
        margin: 0 0 12px 0;
        line-height: 1.6;
    }
    
    ul, ol {
        margin: 12px 0;
        padding-left: 24px;
    }
    
    li {
        margin: 6px 0;
        line-height: 1.6;
    }
    
    code {
        background-color: #F4F5F7;
        border: 1px solid #DFE1E6;
        border-radius: 3px;
        padding: 2px 6px;
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
        font-size: 13px;
        color: #E53E3E;
    }
    
    pre {
        background-color: #F4F5F7;
        border: 1px solid #DFE1E6;
        border-radius: 3px;
        padding: 12px;
        margin: 16px 0;
        overflow-x: auto;
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
        font-size: 13px;
        line-height: 1.5;
    }
    
    pre code {
        background-color: transparent;
        border: none;
        padding: 0;
        color: #172B4D;
    }
    
    pre code span {
        color: inherit;
    }
    
    blockquote {
        border-left: 4px solid #0052CC;
        padding-left: 16px;
        margin: 16px 0;
        color: #505F79;
        font-style: italic;
    }
    
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 16px 0;
        border: 1px solid #DFE1E6;
    }
    
    th {
        background-color: #F4F5F7;
        border: 1px solid #DFE1E6;
        padding: 8px 12px;
        text-align: left;
        font-weight: 600;
        color: #172B4D;
    }
    
    td {
        border: 1px solid #DFE1E6;
        padding: 8px 12px;
    }
    
    tr:nth-child(even) {
        background-color: #FAFBFC;
    }
    
    hr {
        border: none;
        border-top: 1px solid #DFE1E6;
        margin: 24px 0;
    }
    
    a {
        color: #0052CC;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    .info-panel {
        background-color: #E3FCEF;
        border-left: 4px solid #36B37E;
        padding: 12px 16px;
        margin: 16px 0;
        border-radius: 3px;
    }
    
    .warning-panel {
        background-color: #FFF4E5;
        border-left: 4px solid #FFAB00;
        padding: 12px 16px;
        margin: 16px 0;
        border-radius: 3px;
    }
    
    .error-panel {
        background-color: #FFEBEE;
        border-left: 4px solid #DE350B;
        padding: 12px 16px;
        margin: 16px 0;
        border-radius: 3px;
    }
    
    .note-panel {
        background-color: #E3FCEF;
        border-left: 4px solid #0052CC;
        padding: 12px 16px;
        margin: 16px 0;
        border-radius: 3px;
    }
    
    strong {
        font-weight: 600;
        color: #172B4D;
    }
    
    em {
        font-style: italic;
    }
    """
    
    def __init__(self):
        """Initialize PDF generator"""
        self.html_formatter = HtmlFormatter(style='default', noclasses=True, nowrap=True)
        
        # Check available PDF backends
        if not WEASYPRINT_AVAILABLE and not XHTML2PDF_AVAILABLE:
            raise RuntimeError(
                "No PDF generation library available. Please install either:\n"
                "  - weasyprint (Linux/Mac): pip install weasyprint\n"
                "  - xhtml2pdf (Windows-compatible): pip install xhtml2pdf\n"
                f"WeasyPrint error: {WEASYPRINT_ERROR if not WEASYPRINT_AVAILABLE else 'N/A'}"
            )
    
    def _process_code_blocks(self, html: str) -> str:
        """Process code blocks with syntax highlighting"""
        # Pattern to match code blocks with language class
        # Handles both <pre><code class="language-xxx"> and <pre><code class="highlight">
        pattern = r'<pre><code class="(?:language-)?(\w+)?">(.*?)</code></pre>'
        
        def replace_code_block(match):
            lang_class = match.group(1) or ""
            code = match.group(2)
            
            # Extract language from class (language-xxx or just xxx)
            lang = lang_class.replace('language-', '') if lang_class else None
            
            # Unescape HTML entities
            code = code.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            code = code.replace('&quot;', '"').replace('&#39;', "'")
            
            # If code is already highlighted (contains spans), keep it
            if '<span' in code:
                return f'<pre><code>{code}</code></pre>'
            
            # Otherwise, highlight it
            if lang:
                try:
                    lexer = get_lexer_by_name(lang, stripall=True)
                except:
                    lexer = TextLexer()
            else:
                lexer = TextLexer()
            
            highlighted = highlight(code, lexer, self.html_formatter)
            # Extract just the inner HTML from the formatter output
            highlighted = highlighted.replace('<div class="highlight"><pre>', '').replace('</pre></div>', '')
            highlighted = highlighted.replace('<span style="color: #', '<span style="color:#')
            return f'<pre><code>{highlighted}</code></pre>'
        
        return re.sub(pattern, replace_code_block, html, flags=re.DOTALL)
    
    def _process_markdown_extensions(self, markdown_text: str) -> str:
        """Process markdown extensions like info panels"""
        # Convert Confluence-style macros to HTML
        # Info panel: {info}...{info}
        markdown_text = re.sub(
            r'\{info\}(.*?)\{info\}',
            r'<div class="info-panel">\1</div>',
            markdown_text,
            flags=re.DOTALL
        )
        
        # Warning panel: {warning}...{warning}
        markdown_text = re.sub(
            r'\{warning\}(.*?)\{warning\}',
            r'<div class="warning-panel">\1</div>',
            markdown_text,
            flags=re.DOTALL
        )
        
        # Note panel: {note}...{note}
        markdown_text = re.sub(
            r'\{note\}(.*?)\{note\}',
            r'<div class="note-panel">\1</div>',
            markdown_text,
            flags=re.DOTALL
        )
        
        return markdown_text
    
    def markdown_to_pdf(self, markdown_text: str, output_path: Optional[str] = None) -> BytesIO:
        """
        Convert markdown to PDF with Confluence-style formatting
        
        Args:
            markdown_text: Markdown content to convert
            output_path: Optional path to save PDF file
            
        Returns:
            BytesIO object containing PDF data
        """
        # Process markdown extensions
        processed_markdown = self._process_markdown_extensions(markdown_text)
        
        # Convert markdown to HTML
        md = markdown.Markdown(extensions=[
            'extra',
            'codehilite',
            'tables',
            'fenced_code',
            'nl2br',
            'sane_lists'
        ], extension_configs={
            'codehilite': {
                'noclasses': True,
                'use_pygments': True
            }
        })
        
        html_content = md.convert(processed_markdown)
        
        # Process code blocks for syntax highlighting
        html_content = self._process_code_blocks(html_content)
        
        # Wrap in full HTML document
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>TechDocGen by IBMC - Technical Documentation</title>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Generate PDF using available backend
        pdf_bytes = BytesIO()
        
        if WEASYPRINT_AVAILABLE:
            # Use WeasyPrint (preferred, better CSS support)
            try:
                html_doc = HTML(string=full_html)
                css_doc = CSS(string=self.CONFLUENCE_CSS)
                html_doc.write_pdf(pdf_bytes, stylesheets=[css_doc])
                pdf_bytes.seek(0)
            except Exception as e:
                # Fallback to xhtml2pdf if WeasyPrint fails
                if XHTML2PDF_AVAILABLE:
                    self._generate_pdf_xhtml2pdf(full_html, pdf_bytes)
                else:
                    raise RuntimeError(f"WeasyPrint failed: {e}. Please install xhtml2pdf as fallback.")
        elif XHTML2PDF_AVAILABLE:
            # Use xhtml2pdf (Windows-compatible fallback)
            self._generate_pdf_xhtml2pdf(full_html, pdf_bytes)
        else:
            raise RuntimeError("No PDF generation library available")
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes.getvalue())
            pdf_bytes.seek(0)
        
        return pdf_bytes
    
    def _generate_pdf_xhtml2pdf(self, html_content: str, pdf_bytes: BytesIO):
        """Generate PDF using xhtml2pdf (Windows-compatible)"""
        # Convert CSS to inline styles for xhtml2pdf (it has limited CSS support)
        html_with_inline_css = self._convert_css_to_inline(html_content)
        
        try:
            # Generate PDF
            result = pisa.CreatePDF(
                html_with_inline_css,
                dest=pdf_bytes,
                encoding='utf-8'
            )
            
            if result.err:
                raise RuntimeError(f"PDF generation failed: {result.err}")
            
            pdf_bytes.seek(0)
        except TypeError as e:
            # Handle usedforsecurity error specifically
            if 'usedforsecurity' in str(e).lower():
                # Re-apply the patch and retry
                _patch_hashlib_for_xhtml2pdf()
                try:
                    result = pisa.CreatePDF(
                        html_with_inline_css,
                        dest=pdf_bytes,
                        encoding='utf-8'
                    )
                    if result.err:
                        raise RuntimeError(f"PDF generation failed: {result.err}")
                    pdf_bytes.seek(0)
                except Exception as retry_error:
                    raise RuntimeError(
                        f"PDF generation failed due to OpenSSL compatibility issue. "
                        f"Error: {retry_error}. "
                        f"Please try: pip install --upgrade xhtml2pdf reportlab"
                    )
            else:
                raise
        except Exception as e:
            error_msg = str(e)
            if 'usedforsecurity' in error_msg.lower() or 'openssl' in error_msg.lower():
                raise RuntimeError(
                    f"PDF generation failed due to OpenSSL compatibility issue. "
                    f"Please try: pip install --upgrade xhtml2pdf reportlab. "
                    f"Original error: {error_msg}"
                )
            raise
    
    def _convert_css_to_inline(self, html_content: str) -> str:
        """Convert CSS styles to inline styles for xhtml2pdf compatibility"""
        # This is a simplified version - xhtml2pdf has limited CSS support
        # We'll inject basic inline styles
        inline_styles = """
        <style>
            body { font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #172B4D; }
            h1 { font-size: 32px; font-weight: 600; color: #172B4D; margin-top: 0; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #DFE1E6; }
            h2 { font-size: 24px; font-weight: 600; color: #172B4D; margin-top: 32px; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #DFE1E6; }
            h3 { font-size: 20px; font-weight: 600; color: #172B4D; margin-top: 24px; margin-bottom: 12px; }
            h4 { font-size: 16px; font-weight: 600; color: #172B4D; margin-top: 20px; margin-bottom: 10px; }
            code { background-color: #F4F5F7; border: 1px solid #DFE1E6; border-radius: 3px; padding: 2px 6px; font-family: monospace; font-size: 13px; }
            pre { background-color: #F4F5F7; border: 1px solid #DFE1E6; border-radius: 3px; padding: 12px; margin: 16px 0; font-family: monospace; font-size: 13px; }
            table { border-collapse: collapse; width: 100%; margin: 16px 0; border: 1px solid #DFE1E6; }
            th { background-color: #F4F5F7; border: 1px solid #DFE1E6; padding: 8px 12px; font-weight: 600; }
            td { border: 1px solid #DFE1E6; padding: 8px 12px; }
        </style>
        """
        
        # Insert styles into HTML head
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', f'<head>{inline_styles}')
        else:
            html_content = f'<head>{inline_styles}</head>{html_content}'
        
        return html_content
    
    def generate_pdf_from_markdown(self, markdown_text: str, filename: str = "technical_documentation.pdf") -> BytesIO:
        """
        Generate PDF from markdown and return as BytesIO
        
        Args:
            markdown_text: Markdown content
            filename: Output filename (for reference)
            
        Returns:
            BytesIO object containing PDF data
        """
        return self.markdown_to_pdf(markdown_text)

