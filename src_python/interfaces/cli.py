import typer
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON
import webbrowser
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import orchestrator, graphing, database

app = typer.Typer()
console = Console()


@app.command()
def search(target_type: str, target_value: str):
    """
    Search for OSINT information on a target.
    
    TARGET_TYPE: The type of target (name, email, address, website, business)
    TARGET_VALUE: The value to search for
    """
    console.print(f"[bold blue]Searching for {target_type}: {target_value}[/bold blue]")
    
    # Run the async search
    results = asyncio.run(orchestrator.run_search(target_type, target_value))
    
    # Display results
    _display_search_results(results)


@app.command()
def show_graph():
    """
    Generate and display the relationship graph.
    """
    console.print("[bold blue]Generating graph visualization...[/bold blue]")
    
    # Generate HTML
    html_content = graphing.generate_interactive_html()
    
    # Save to temporary file
    temp_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'graph.html')
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    
    with open(temp_path, 'w') as f:
        f.write(html_content)
    
    console.print(f"[green]Graph saved to: {temp_path}[/green]")
    
    # Open in default browser
    webbrowser.open(f'file://{os.path.abspath(temp_path)}')


@app.command()
def create_profile(name: str):
    """
    Create a profile and allow user to link entities via CLI prompts.
    
    NAME: The name for the profile
    """
    console.print(f"[bold blue]Creating profile: {name}[/bold blue]")
    
    # Get notes from user
    notes = typer.prompt("Enter notes for this profile (optional)", default="")
    
    # Create profile in database
    profile_id = database.create_profile(name, notes if notes else None)
    
    console.print(f"[green]Profile created with ID: {profile_id}[/green]")
    
    # Ask if user wants to link entities
    link_entities = typer.confirm("Do you want to link existing entities to this profile?")
    
    if link_entities:
        _link_entities_to_profile(profile_id)


@app.command()
def list_profiles():
    """List all existing profiles."""
    console.print("[bold blue]Existing Profiles:[/bold blue]")
    
    profiles = database.get_profiles()
    
    if not profiles:
        console.print("[yellow]No profiles found.[/yellow]")
        return
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Notes")
    table.add_column("Created")
    
    for profile in profiles:
        table.add_row(
            profile['id'][:8] + "...",
            profile['name'],
            profile['notes'][:50] + "..." if profile['notes'] and len(profile['notes']) > 50 else (profile['notes'] or ""),
            profile['created_at']
        )
    
    console.print(table)


@app.command()
def show_profile(profile_id: str):
    """Show details of a specific profile."""
    console.print(f"[bold blue]Profile Details: {profile_id}[/bold blue]")
    
    # Get profile entities
    entities = database.get_profile_entities(profile_id)
    
    if not entities:
        console.print("[yellow]No entities linked to this profile.[/yellow]")
        return
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Type")
    table.add_column("Value")
    table.add_column("Source")
    
    for entity in entities:
        table.add_row(
            entity['id'][:8] + "...",
            entity['type'],
            entity['value'],
            entity['source'] or "N/A"
        )
    
    console.print(table)


def _display_search_results(results: dict):
    """Display search results in a formatted way."""
    # Show summary
    console.print(Panel.fit(
        f"[bold]Search Summary[/bold]\n"
        f"Target: {results['target_value']} ({results['target_type']})\n"
        f"Entities Created: {len(results.get('entities_created', []))}\n"
        f"Relationships Created: {len(results.get('relationships_created', []))}",
        title="Results"
    ))
    
    # Show search results by source
    search_results = results.get('search_results', {})
    
    for source, data in search_results.items():
        if data and isinstance(data, dict):
            console.print(f"\n[bold cyan]{source.upper()} Results:[/bold cyan]")
            console.print(JSON(data, indent=2))
        elif data and isinstance(data, list):
            console.print(f"\n[bold cyan]{source.upper()} Results:[/bold cyan]")
            console.print(f"Found {len(data)} items")
            for item in data[:5]:  # Show first 5 items
                console.print(f"  - {item}")
    
    # Show created entities
    entities = results.get('entities_created', [])
    if entities:
        console.print(f"\n[bold green]Entities Created:[/bold green]")
        table = Table(show_header=True, header_style="bold green")
        table.add_column("ID", style="dim")
        table.add_column("Type")
        table.add_column("Value")
        
        for entity in entities:
            table.add_row(
                entity['id'][:8] + "...",
                entity['type'],
                entity['value']
            )
        
        console.print(table)
    
    # Show created relationships
    relationships = results.get('relationships_created', [])
    if relationships:
        console.print(f"\n[bold yellow]Relationships Created:[/bold yellow]")
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Source")
        table.add_column("Target")
        table.add_column("Type")
        
        for rel in relationships:
            table.add_row(
                rel['source'][:8] + "...",
                rel['target'][:8] + "...",
                rel['type']
            )
        
        console.print(table)


def _link_entities_to_profile(profile_id: str):
    """Interactive prompt to link entities to a profile."""
    console.print("[bold blue]Available Entity Types:[/bold blue]")
    console.print("1. name")
    console.print("2. email")
    console.print("3. address")
    console.print("4. website")
    console.print("5. business")
    
    while True:
        entity_type = typer.prompt("Enter entity type (or 'done' to finish)", default="done")
        
        if entity_type.lower() == 'done':
            break
        
        entity_value = typer.prompt(f"Enter {entity_type} value")
        
        # Create or get entity
        entity_id = database.upsert_entity(entity_type, entity_value, source="manual_link")
        
        # Link to profile
        database.link_entity_to_profile(profile_id, entity_id)
        
        console.print(f"[green]Linked {entity_type}: {entity_value} to profile[/green]")
    
    console.print("[green]Profile linking complete![/green]")


if __name__ == "__main__":
    app()
