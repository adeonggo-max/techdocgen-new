"""PDF generator with Confluence-style formatting"""

import re
from io import BytesIO
from pathlib import Path
from typing import Optional
import markdown
from weasyprint import HTML, CSS
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter


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
        
        # Generate PDF
        html_doc = HTML(string=full_html)
        css_doc = CSS(string=self.CONFLUENCE_CSS)
        
        pdf_bytes = BytesIO()
        html_doc.write_pdf(pdf_bytes, stylesheets=[css_doc])
        pdf_bytes.seek(0)
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes.getvalue())
            pdf_bytes.seek(0)
        
        return pdf_bytes
    
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

