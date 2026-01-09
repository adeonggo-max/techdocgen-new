#!/usr/bin/env python3
"""Main CLI entry point for TechDocGen by IBMC - Technical Documentation Generator"""

import click
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from src.generator import DocumentationGenerator

console = Console()


@click.command()
@click.option('--source', '-s', required=True, help='Source path: file path, folder path, or git repository URL')
@click.option('--type', '-t', type=click.Choice(['file', 'folder', 'git'], case_sensitive=False), 
              default='auto', help='Source type (auto-detect if not specified)')
@click.option('--output', '-o', help='Output file path (default: ./docs/technical_docs.md)')
@click.option('--provider', '-p', type=click.Choice(['openai', 'anthropic', 'ollama', 'mcp'], case_sensitive=False),
              help='LLM provider to use (default: from config)')
@click.option('--config', '-c', help='Path to config.yaml file')
@click.option('--branch', '-b', help='Git branch to use (for git sources)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--dep-map', is_flag=True, help='Generate dependency map')
@click.option('--dep-map-format', type=click.Choice(['json', 'dot', 'mermaid', 'markdown'], case_sensitive=False),
              default='json', help='Dependency map output format (default: json)')
@click.option('--dep-map-output', help='Dependency map output file path')
def main(source, type, output, provider, config, branch, verbose, dep_map, dep_map_format, dep_map_output):
    """Generate technical documentation from source code"""
    
    console.print("[bold blue]TechDocGen by IBMC[/bold blue]")
    console.print("[dim]Technical Documentation Generator[/dim]\n")
    
    # Auto-detect source type if not specified
    if type == 'auto':
        source_path = Path(source)
        if source_path.is_file():
            source_type = 'file'
        elif source_path.is_dir():
            source_type = 'folder'
        elif source.startswith('http') or source.startswith('git@') or source.endswith('.git'):
            source_type = 'git'
        else:
            # Check if it's a git URL or local git repo
            if source_path.exists() and (source_path / '.git').exists():
                source_type = 'folder'
            else:
                source_type = 'git'
    else:
        source_type = type.lower()
    
    if verbose:
        console.print(f"[dim]Source: {source}[/dim]")
        console.print(f"[dim]Type: {source_type}[/dim]")
        console.print(f"[dim]Provider: {provider or 'default'}[/dim]\n")
    
    try:
        # Initialize generator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing generator...", total=None)
            generator = DocumentationGenerator(config_path=config, llm_provider=provider)
            progress.update(task, description="Generator ready")
        
        # Read source code
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Reading source code...", total=None)
            
            if source_type == 'file':
                reader = generator._get_reader('file', source)
            elif source_type == 'folder':
                reader = generator._get_reader('folder', source)
            elif source_type == 'git':
                reader = generator._get_reader('git', source, branch)
            else:
                raise ValueError(f"Unknown source type: {source_type}")
            
            files = reader.read()
            progress.update(task, description="Source code read")
        
        # Generate dependency map if requested
        if dep_map:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing dependencies...", total=None)
                dep_map_file = generator.generate_dependency_map(files, dep_map_format, dep_map_output)
                progress.update(task, description="Dependency map generated")
            
            console.print(f"\n[bold green]✓ Dependency map generated![/bold green]")
            console.print(f"[dim]Output: {dep_map_file.absolute()}[/dim]\n")
        
        # Generate documentation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating documentation with LLM...", total=None)
            
            # Use pre-read files if available (when dep_map was requested), otherwise read again
            if dep_map and files:
                documentation = generator.generate_docs_from_files(files)
            else:
                if source_type == 'file':
                    documentation = generator.generate_from_file(source)
                elif source_type == 'folder':
                    documentation = generator.generate_from_folder(source)
                elif source_type == 'git':
                    documentation = generator.generate_from_git(source, branch)
                else:
                    raise ValueError(f"Unknown source type: {source_type}")
            
            progress.update(task, description="Documentation generated")
        
        # Save documentation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Saving documentation...", total=None)
            output_file = generator.save_documentation(documentation, output)
            progress.update(task, description="Documentation saved")
        
        console.print(f"\n[bold green]✓ Documentation generated successfully![/bold green]")
        console.print(f"[dim]Output: {output_file.absolute()}[/dim]\n")
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error: {e}[/bold red]\n")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise click.Abort()


if __name__ == '__main__':
    main()

