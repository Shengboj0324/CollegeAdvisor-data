"""Command-line interface for the College Advisor data pipeline."""

import click
import logging
import sys
from pathlib import Path
from typing import Optional

# Add collectors to path
sys.path.append(str(Path(__file__).parent.parent))

from .config import config


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
@click.option('--collector', '-c', type=click.Choice(['scorecard', 'ipeds', 'cds']), default='scorecard', help='Data collector to use')
@click.option('--years', '-y', help='Years to collect (comma-separated)')
@click.option('--states', '-s', help='States to collect (comma-separated)')
@click.option('--field-groups', '-f', help='Field groups to collect (comma-separated)')
@click.option('--page-size', '-p', type=int, default=20, help='Page size for API requests')
def collect(collector: str, years: Optional[str], states: Optional[str], field_groups: Optional[str], page_size: int):
    """Collect data from external sources."""
    click.echo(f"🔄 Starting data collection with {collector} collector...")

    try:
        if collector == 'scorecard':
            from collectors.base_collector import CollectorConfig
            from collectors.government import CollegeScorecardCollector

            # Create collector configuration
            collector_config = CollectorConfig(
                api_key=config.college_scorecard_api_key,
                requests_per_second=config.default_requests_per_second,
                cache_enabled=True,
                cache_ttl_hours=24,
                output_format="json"
            )

            # Initialize collector
            data_collector = CollegeScorecardCollector(collector_config)

            # Parse parameters
            years_list = [int(y.strip()) for y in years.split(',')] if years else [2021]
            states_list = [s.strip().upper() for s in states.split(',')] if states else None
            field_groups_list = [f.strip() for f in field_groups.split(',')] if field_groups else ["basic"]

            # Collect data
            result = data_collector.collect(
                years=years_list,
                states=states_list,
                field_groups=field_groups_list,
                page_size=page_size
            )

            click.echo(f"✅ Collection completed!")
            click.echo(f"   Records collected: {result.total_records}")
            click.echo(f"   Processing time: {result.processing_time:.2f} seconds")
            click.echo(f"   API calls made: {result.api_calls}")

        else:
            click.echo(f"❌ Collector '{collector}' not yet implemented")

    except Exception as e:
        click.echo(f"❌ Collection failed: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option('--collector', '-c', type=click.Choice(['scorecard', 'ipeds', 'cds']), required=True, help='Data collector to use')
@click.option('--years', '-y', help='Years to collect (comma-separated, e.g., 2022,2023)')
@click.option('--states', '-s', help='States to filter by (comma-separated, e.g., CA,NY,TX)')
@click.option('--field-groups', '-f', help='Field groups to collect (comma-separated)')
@click.option('--output', '-o', help='Output directory for collected data')
def collect(collector: str, years: Optional[str], states: Optional[str], field_groups: Optional[str], output: Optional[str]):
    """Collect data from external sources."""
    click.echo(f"🔄 Starting data collection with {collector} collector")

    try:
        # Import collectors
        import sys
        sys.path.append('.')
        from collectors.base_collector import CollectorConfig
        from collectors.government import CollegeScorecardCollector

        # Parse parameters
        years_list = [int(y.strip()) for y in years.split(',')] if years else None
        states_list = [s.strip().upper() for s in states.split(',')] if states else None
        field_groups_list = [f.strip() for f in field_groups.split(',')] if field_groups else None

        # Create collector configuration
        collector_config = CollectorConfig(
            api_key=config.college_scorecard_api_key,
            requests_per_second=config.default_requests_per_second,
            cache_enabled=True,
            output_format="json"
        )

        # Initialize collector
        if collector == 'scorecard':
            data_collector = CollegeScorecardCollector(collector_config)
        else:
            click.echo(f"❌ Collector '{collector}' not yet implemented")
            raise click.Abort()

        # Show source information
        source_info = data_collector.get_source_info()
        click.echo(f"📊 Data Source: {source_info['name']}")
        click.echo(f"   Provider: {source_info['provider']}")
        click.echo(f"   Description: {source_info['description']}")

        # Run collection
        result = data_collector.collect(
            years=years_list,
            states=states_list,
            field_groups=field_groups_list
        )

        # Display results
        click.echo(f"\n✅ Collection completed!")
        click.echo(f"   Total records: {result.total_records}")
        click.echo(f"   Successful: {result.successful_records}")
        click.echo(f"   Failed: {result.failed_records}")
        click.echo(f"   Success rate: {result.success_rate:.1%}")
        click.echo(f"   Duration: {result.duration}")

        if result.errors:
            click.echo(f"\n⚠️  Errors encountered:")
            for error in result.errors:
                click.echo(f"   - {error}")

        if result.metadata.get("output_file"):
            click.echo(f"\n💾 Data saved to: {result.metadata['output_file']}")

    except Exception as e:
        click.echo(f"❌ Collection failed: {e}", err=True)
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
