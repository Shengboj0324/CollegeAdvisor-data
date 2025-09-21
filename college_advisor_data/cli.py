"""Command-line interface for the College Advisor data pipeline."""

import click
import logging
from pathlib import Path
from typing import Optional

from .config import config
from .ingestion.pipeline import IngestionPipeline
from .storage.chroma_client import ChromaDBClient


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.log_file) if config.log_file else logging.NullHandler()
        ]
    )


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(verbose: bool):
    """College Advisor Data Pipeline CLI."""
    if verbose:
        config.log_level = "DEBUG"
    setup_logging()


@main.command()
@click.option('--source', '-s', required=True, help='Source data file or directory')
@click.option('--format', '-f', type=click.Choice(['csv', 'json', 'txt']), default='csv', help='Input format')
@click.option('--doc-type', '-t', type=click.Choice(['university', 'program', 'summer_program']), required=True, help='Document type')
def ingest(source: str, format: str, doc_type: str):
    """Ingest data from source files."""
    click.echo(f"Ingesting {doc_type} data from {source} (format: {format})")
    
    pipeline = IngestionPipeline()
    try:
        stats = pipeline.ingest_from_file(Path(source), format, doc_type)
        click.echo(f"✅ Ingested {stats.total_documents} documents, {stats.total_chunks} chunks")
    except Exception as e:
        click.echo(f"❌ Ingestion failed: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option('--collection', '-c', default=None, help='ChromaDB collection name')
@click.option('--reset', is_flag=True, help='Reset the collection before loading')
def load(collection: Optional[str], reset: bool):
    """Load processed data into ChromaDB."""
    collection_name = collection or config.chroma_collection_name
    click.echo(f"Loading data into ChromaDB collection: {collection_name}")
    
    if reset:
        click.confirm(f"This will delete all data in collection '{collection_name}'. Continue?", abort=True)
    
    client = ChromaDBClient()
    try:
        if reset:
            client.reset_collection(collection_name)
        
        # Load processed data
        stats = client.load_processed_data(collection_name)
        click.echo(f"✅ Loaded {stats.total_embeddings} embeddings into ChromaDB")
    except Exception as e:
        click.echo(f"❌ Loading failed: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option('--query', '-q', required=True, help='Search query')
@click.option('--collection', '-c', default=None, help='ChromaDB collection name')
@click.option('--limit', '-l', default=5, help='Number of results to return')
def search(query: str, collection: Optional[str], limit: int):
    """Search the ChromaDB collection."""
    collection_name = collection or config.chroma_collection_name
    click.echo(f"Searching collection '{collection_name}' for: {query}")
    
    client = ChromaDBClient()
    try:
        results = client.search(collection_name, query, limit)
        
        click.echo(f"\n📊 Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            click.echo(f"\n{i}. Score: {result.get('distance', 'N/A'):.3f}")
            click.echo(f"   Type: {result.get('metadata', {}).get('doc_type', 'Unknown')}")
            click.echo(f"   Content: {result.get('document', '')[:200]}...")
            
    except Exception as e:
        click.echo(f"❌ Search failed: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option('--collection', '-c', default=None, help='ChromaDB collection name')
def status(collection: Optional[str]):
    """Show pipeline and database status."""
    collection_name = collection or config.chroma_collection_name
    
    click.echo("📊 College Advisor Data Pipeline Status\n")
    
    # Check processed data
    processed_files = list(config.processed_dir.glob("*.json"))
    click.echo(f"Processed files: {len(processed_files)}")
    
    # Check ChromaDB
    client = ChromaDBClient()
    try:
        count = client.get_collection_count(collection_name)
        click.echo(f"ChromaDB documents: {count}")
        click.echo(f"Collection: {collection_name}")
    except Exception as e:
        click.echo(f"ChromaDB status: ❌ {e}")
    
    # Configuration
    click.echo(f"\nConfiguration:")
    click.echo(f"  Embedding model: {config.embedding_model}")
    click.echo(f"  Chunk size: {config.chunk_size}")
    click.echo(f"  Data directory: {config.data_dir}")


@main.command()
def init():
    """Initialize the data pipeline environment."""
    click.echo("🚀 Initializing College Advisor Data Pipeline")
    
    # Create directories
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.processed_dir.mkdir(parents=True, exist_ok=True)
    config.cache_dir.mkdir(parents=True, exist_ok=True)
    
    if config.log_file:
        config.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        env_example = Path(".env.example")
        if env_example.exists():
            env_file.write_text(env_example.read_text())
            click.echo("📝 Created .env file from .env.example")
    
    click.echo("✅ Pipeline initialized successfully!")
    click.echo("\nNext steps:")
    click.echo("1. Edit .env file with your configuration")
    click.echo("2. Add seed data to data/seed/ directory")
    click.echo("3. Run: college-data ingest --source data/seed/universities.csv --doc-type university")


if __name__ == "__main__":
    main()
