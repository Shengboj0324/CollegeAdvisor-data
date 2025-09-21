"""Command-line interface for the College Advisor data pipeline."""

import click
import logging
from pathlib import Path
from typing import Optional

from .config import config
from .ingestion.pipeline import IngestionPipeline
from .storage.chroma_client import ChromaDBClient
from .evaluation.metrics import EvaluationMetrics
from .evaluation.coverage import CoverageAnalyzer


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
@click.option('--collection', '-c', default=None, help='ChromaDB collection name')
@click.option('--save-report', '-s', default=None, help='Path to save evaluation report')
def evaluate(collection: Optional[str], save_report: Optional[str]):
    """Evaluate pipeline quality and data coverage."""
    collection_name = collection or config.chroma_collection_name
    click.echo(f"🔍 Evaluating pipeline for collection: {collection_name}")

    evaluator = EvaluationMetrics()
    try:
        report = evaluator.generate_evaluation_report(
            collection_name,
            Path(save_report) if save_report else None
        )

        # Display summary
        click.echo(f"\n📊 Evaluation Results:")
        click.echo(f"Overall Score: {report['metrics'].get('overall_score', 0):.2f}/1.00")

        for category, metrics in report['metrics'].items():
            if isinstance(metrics, dict) and 'score' in metrics:
                score = metrics['score']
                status = "✅" if score >= 0.7 else "⚠️" if score >= 0.5 else "❌"
                click.echo(f"{status} {category.replace('_', ' ').title()}: {score:.2f}")

        # Show recommendations
        if report.get('recommendations'):
            click.echo(f"\n💡 Recommendations:")
            for rec in report['recommendations']:
                click.echo(f"  • {rec}")

        if save_report:
            click.echo(f"\n📄 Full report saved to: {save_report}")

    except Exception as e:
        click.echo(f"❌ Evaluation failed: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option('--collection', '-c', default=None, help='ChromaDB collection name')
def coverage(collection: Optional[str]):
    """Analyze data coverage across different dimensions."""
    collection_name = collection or config.chroma_collection_name
    click.echo(f"📈 Analyzing coverage for collection: {collection_name}")

    analyzer = CoverageAnalyzer()
    try:
        analysis = analyzer.analyze_comprehensive_coverage(collection_name)

        click.echo(f"\n📊 Coverage Analysis Results:")
        click.echo(f"Overall Coverage Score: {analysis.get('overall_coverage_score', 0):.2f}/1.00")

        # Display key metrics
        for category, metrics in analysis.items():
            if isinstance(metrics, dict) and 'coverage_score' in metrics:
                score = metrics['coverage_score']
                status = "✅" if score >= 0.7 else "⚠️" if score >= 0.5 else "❌"
                click.echo(f"{status} {category.replace('_', ' ').title()}: {score:.2f}")

                # Show specific details
                if category == 'university_coverage':
                    click.echo(f"    Universities: {metrics.get('total_universities', 0)}")
                elif category == 'geographic_coverage':
                    click.echo(f"    States: {metrics.get('states_covered', 0)}/50")
                elif category == 'subject_coverage':
                    click.echo(f"    Subject Areas: {metrics.get('total_subject_areas', 0)}")

    except Exception as e:
        click.echo(f"❌ Coverage analysis failed: {e}", err=True)
        raise click.Abort()


@main.command()
def health():
    """Check health of all pipeline components."""
    click.echo("🏥 Checking pipeline health...")

    pipeline = IngestionPipeline()
    try:
        health_status = pipeline.health_check()

        overall_status = health_status.get("pipeline", "unknown")
        status_icon = "✅" if overall_status == "healthy" else "❌"
        click.echo(f"\n{status_icon} Overall Pipeline Status: {overall_status}")

        # Check individual components
        components = health_status.get("components", {})
        for component, status in components.items():
            component_status = status.get("status", "unknown")
            component_icon = "✅" if component_status == "healthy" else "❌"
            click.echo(f"{component_icon} {component.title()}: {component_status}")

            if component_status != "healthy" and "error" in status:
                click.echo(f"    Error: {status['error']}")

    except Exception as e:
        click.echo(f"❌ Health check failed: {e}", err=True)
        raise click.Abort()


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
    click.echo("4. Run: college-data health  # Check component health")
    click.echo("5. Run: college-data evaluate  # Evaluate pipeline quality")


if __name__ == "__main__":
    main()
