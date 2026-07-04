"""
Apple Maps Bulk Listing Manager CLI
"""
import click
import asyncio
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from src.config.settings import Settings
from src.config.logging_config import setup_logging
from src.engine.bulk_uploader import BulkUploader
from src.data.reader import DataReader


console = Console()


@click.group()
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, debug):
    """Apple Maps Bulk Listing Manager"""
    try:
        ctx.ensure_object(dict)
        settings = Settings()
        ctx.obj['settings'] = settings
        ctx.obj['debug'] = debug
        
        setup_logging(settings)
        
        if debug:
            console.print("[yellow]Debug mode enabled[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Failed to initialize: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--aggregator', '-a', 
              type=click.Choice(['apple', 'yext', 'uberall', 'rio_seo']),
              default='apple',
              help='Target aggregator')
@click.option('--validate-only', is_flag=True, help='Only validate data')
@click.pass_context
def upload(ctx, input_file, aggregator, validate_only):
    """Upload locations to specified aggregator"""
    settings = ctx.obj['settings']
    input_path = Path(input_file)
    
    console.print(f"[blue]Uploading {input_path.name} to {aggregator}[/blue]")
    
    async def run_upload():
        uploader = BulkUploader(settings)
        try:
            result = await uploader.upload_from_file(
                file_path=str(input_path),
                aggregator=aggregator,
                validate_only=validate_only
            )
            
            console.print("[green]Upload completed successfully![/green]")
            console.print(f"Processed: {result.total_records} records")
            console.print(f"Valid: {result.valid_records}")
            console.print(f"Invalid: {result.invalid_records}")
            
        except Exception as e:
            console.print(f"[red]Upload failed: {str(e)}[/red]")
            raise
        finally:
            uploader.close()
    
    try:
        asyncio.run(run_upload())
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.pass_context
def preview(ctx, file_path):
    """Preview file contents"""
    reader = DataReader()
    file_path = Path(file_path)
    
    try:
        preview_data = reader.preview_file(file_path)
        console.print(f"[blue]Preview of {file_path.name}:[/blue]")
        
        table = Table()
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_row("Format", preview_data['format'])
        table.add_row("Size", f"{preview_data['size_mb']} MB")
        table.add_row("Rows", str(preview_data['rows']))
        table.add_row("Modified", str(preview_data['modified']))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


def main():
    cli()


if __name__ == '__main__':
    main()