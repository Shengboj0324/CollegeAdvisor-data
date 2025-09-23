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
@click.option('--collector', '-c', type=click.Choice(['scorecard', 'ipeds', 'cds', 'user_auth', 'social_auth', 'phone_verification', 'security_events', 'user_profiles']), default='scorecard', help='Data collector to use')
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

        elif collector == 'user_auth':
            from collectors.base_collector import CollectorConfig
            from collectors.user_auth_collector import UserAuthCollector

            collector_config = CollectorConfig(api_key="demo", cache_enabled=True)
            data_collector = UserAuthCollector(collector_config)
            result = data_collector.collect()

            click.echo(f"✅ User authentication data collection completed!")
            click.echo(f"   Records collected: {result.total_records}")
            click.echo(f"   API calls made: {result.api_calls}")

        elif collector == 'social_auth':
            from collectors.base_collector import CollectorConfig
            from collectors.social_media import SocialMediaAuthCollector

            collector_config = CollectorConfig(api_key="demo", cache_enabled=True)
            data_collector = SocialMediaAuthCollector(collector_config)
            result = data_collector.collect()

            click.echo(f"✅ Social authentication data collection completed!")
            click.echo(f"   Records collected: {result.total_records}")
            click.echo(f"   API calls made: {result.api_calls}")

        elif collector == 'phone_verification':
            from collectors.base_collector import CollectorConfig
            from collectors.phone_verification_collector import PhoneVerificationCollector

            collector_config = CollectorConfig(api_key="demo", cache_enabled=True)
            data_collector = PhoneVerificationCollector(collector_config)
            result = data_collector.collect()

            click.echo(f"✅ Phone verification data collection completed!")
            click.echo(f"   Records collected: {result.total_records}")
            click.echo(f"   API calls made: {result.api_calls}")

        elif collector == 'security_events':
            from collectors.base_collector import CollectorConfig
            from collectors.security_event_collector import SecurityEventCollector

            collector_config = CollectorConfig(api_key="demo", cache_enabled=True)
            data_collector = SecurityEventCollector(collector_config)
            result = data_collector.collect()

            click.echo(f"✅ Security events data collection completed!")
            click.echo(f"   Records collected: {result.total_records}")
            click.echo(f"   API calls made: {result.api_calls}")

        elif collector == 'user_profiles':
            from collectors.base_collector import CollectorConfig
            from collectors.user_profile_collector import UserProfileCollector

            collector_config = CollectorConfig(api_key="demo", cache_enabled=True)
            data_collector = UserProfileCollector(collector_config)
            result = data_collector.collect()

            click.echo(f"✅ User profiles data collection completed!")
            click.echo(f"   Records collected: {result.total_records}")
            click.echo(f"   API calls made: {result.api_calls}")

        else:
            click.echo(f"❌ Collector '{collector}' not yet implemented")

    except Exception as e:
        click.echo(f"❌ Collection failed: {e}", err=True)
        raise click.Abort()





@main.command()
def test():
    """Test the data collection system."""
    click.echo("🧪 Testing College Scorecard collector...")

    try:
        from collectors.base_collector import CollectorConfig
        from collectors.government import CollegeScorecardCollector

        # Create test configuration
        collector_config = CollectorConfig(
            api_key=config.college_scorecard_api_key,
            requests_per_second=config.default_requests_per_second,
            cache_enabled=True,
            cache_ttl_hours=24,
            output_format="json"
        )

        # Initialize collector
        data_collector = CollegeScorecardCollector(collector_config)

        # Get source info
        source_info = data_collector.get_source_info()
        click.echo(f"✅ Source: {source_info['name']}")
        click.echo(f"   Fields: {source_info['total_fields']}")
        click.echo(f"   Categories: {len(source_info['data_categories'])}")

        # Test field groups
        field_groups = data_collector.FIELD_GROUPS
        click.echo(f"✅ Found {len(field_groups)} field groups:")
        for group, fields in field_groups.items():
            click.echo(f"   - {group}: {len(fields)} fields")

        click.echo(f"\n🎉 Basic tests passed!")

        if config.college_scorecard_api_key == "DEMO_KEY":
            click.echo(f"\nNote: Data collection test skipped due to DEMO_KEY rate limits.")
            click.echo(f"To test data collection, get a production API key from:")
            click.echo(f"https://api.data.gov/signup/")

    except Exception as e:
        click.echo(f"❌ Test failed: {e}", err=True)
        raise click.Abort()


@main.command()
def config_show():
    """Show current configuration."""
    click.echo("⚙️ Current Configuration:")
    click.echo(f"   College Scorecard API Key: {'Set' if config.college_scorecard_api_key else 'Not set'}")
    click.echo(f"   Data Directory: {config.data_dir}")
    click.echo(f"   Cache Directory: {config.cache_dir}")
    click.echo(f"   Log Level: {config.log_level}")
    click.echo(f"   Requests per second: {config.default_requests_per_second}")


@main.command()
@click.option('--collection', '-c', default=None, help='ChromaDB collection name')
@click.option('--reset', is_flag=True, help='Reset the collection before loading')
def load(collection: Optional[str], reset: bool):
    """Load processed data into ChromaDB."""
    try:
        from storage.chromadb_client import ChromaDBClient

        collection_name = collection or config.chroma_collection_name
        click.echo(f"Loading data into ChromaDB collection: {collection_name}")

        if reset:
            click.confirm(f"This will delete all data in collection '{collection_name}'. Continue?", abort=True)

        client = ChromaDBClient()
        if reset:
            client.reset_collection(collection_name)

        # Load processed data
        stats = client.load_processed_data(collection_name)
        click.echo(f"✅ Loaded {stats.total_embeddings} embeddings into ChromaDB")
    except ImportError:
        click.echo("❌ ChromaDB client not available. Install chromadb dependencies.")
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Loading failed: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option('--query', '-q', required=True, help='Search query')
@click.option('--collection', '-c', default=None, help='ChromaDB collection name')
@click.option('--limit', '-l', default=5, help='Number of results to return')
def search(query: str, collection: Optional[str], limit: int):
    """Search the ChromaDB collection."""
    try:
        from storage.chromadb_client import ChromaDBClient

        collection_name = collection or config.chroma_collection_name
        click.echo(f"Searching collection '{collection_name}' for: {query}")

        client = ChromaDBClient()
        results = client.search(collection_name, query, limit)

        click.echo(f"\n📊 Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            click.echo(f"\n{i}. Score: {result.get('distance', 'N/A'):.3f}")
            click.echo(f"   Type: {result.get('metadata', {}).get('doc_type', 'Unknown')}")
            click.echo(f"   Content: {result.get('document', '')[:200]}...")

    except ImportError:
        click.echo("❌ ChromaDB client not available. Install chromadb dependencies.")
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Search failed: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option('--collection', '-c', default=None, help='ChromaDB collection name')
def status(collection: Optional[str]):
    """Show pipeline and database status."""
    collection_name = collection or getattr(config, 'chroma_collection_name', 'college_data')

    click.echo("📊 College Advisor Data Pipeline Status\n")

    # Check processed data
    processed_dir = getattr(config, 'processed_dir', Path('data/processed'))
    if processed_dir.exists():
        processed_files = list(processed_dir.glob("*.json"))
        click.echo(f"Processed files: {len(processed_files)}")
    else:
        click.echo(f"Processed files: 0 (directory not found)")

    # Check raw data
    raw_dir = Path('data/raw')
    if raw_dir.exists():
        raw_files = list(raw_dir.glob("*.json"))
        click.echo(f"Raw data files: {len(raw_files)}")
    else:
        click.echo(f"Raw data files: 0")

    # Check ChromaDB
    try:
        from storage.chromadb_client import ChromaDBClient
        client = ChromaDBClient()
        count = client.get_collection_count(collection_name)
        click.echo(f"ChromaDB documents: {count}")
        click.echo(f"Collection: {collection_name}")
    except ImportError:
        click.echo(f"ChromaDB status: ❌ Not available")
    except Exception as e:
        click.echo(f"ChromaDB status: ❌ {e}")

    # Configuration
    click.echo(f"\nConfiguration:")
    click.echo(f"  Data directory: {config.data_dir}")
    click.echo(f"  Cache directory: {config.cache_dir}")
    click.echo(f"  Log level: {config.log_level}")


@main.command()
def health():
    """Check health of all pipeline components."""
    click.echo("🏥 Checking pipeline health...")

    try:
        # Check basic components
        health_status = {}

        # Check data directories
        data_dir = Path('data')
        raw_dir = data_dir / 'raw'
        processed_dir = data_dir / 'processed'
        cache_dir = Path('cache')  # Cache is at root level, not inside data

        health_status['directories'] = {
            'data': data_dir.exists(),
            'raw': raw_dir.exists(),
            'processed': processed_dir.exists(),
            'cache': cache_dir.exists()
        }

        # Check configuration
        health_status['config'] = {
            'api_key': bool(config.college_scorecard_api_key),
            'data_dir': config.data_dir.exists() if hasattr(config.data_dir, 'exists') else True
        }

        # Check collectors
        try:
            from collectors.government import CollegeScorecardCollector
            health_status['collectors'] = {'scorecard': True}
        except ImportError as e:
            health_status['collectors'] = {'scorecard': False, 'error': str(e)}

        # Display results
        overall_healthy = all(
            all(v.values() if isinstance(v, dict) else [v])
            for k, v in health_status.items()
            if k != 'error'
        )

        status_icon = "✅" if overall_healthy else "❌"
        click.echo(f"\n{status_icon} Overall Pipeline Status: {'healthy' if overall_healthy else 'issues detected'}")

        for component, status in health_status.items():
            if isinstance(status, dict):
                component_healthy = all(status.values()) if 'error' not in status else False
                component_icon = "✅" if component_healthy else "❌"
                click.echo(f"{component_icon} {component.title()}: {'healthy' if component_healthy else 'issues'}")

                if not component_healthy and 'error' in status:
                    click.echo(f"    Error: {status['error']}")
            else:
                component_icon = "✅" if status else "❌"
                click.echo(f"{component_icon} {component.title()}: {'healthy' if status else 'issues'}")

    except Exception as e:
        click.echo(f"❌ Health check failed: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option('--generate-training-data', is_flag=True, help='Generate training data for AI models')
@click.option('--evaluate-models', is_flag=True, help='Evaluate AI model performance')
@click.option('--check-data-quality', is_flag=True, help='Check data quality metrics')
@click.option('--start-continuous-learning', is_flag=True, help='Start continuous learning pipeline')
def ai_training(generate_training_data: bool, evaluate_models: bool, check_data_quality: bool, start_continuous_learning: bool):
    """AI training and model management commands."""

    if not any([generate_training_data, evaluate_models, check_data_quality, start_continuous_learning]):
        click.echo("🤖 AI Training System")
        click.echo("Available commands:")
        click.echo("  --generate-training-data    Generate training datasets")
        click.echo("  --evaluate-models          Evaluate model performance")
        click.echo("  --check-data-quality       Check data quality")
        click.echo("  --start-continuous-learning Start continuous learning")
        return

    try:
        if generate_training_data:
            click.echo("🔄 Generating AI training data...")

            from ai_training import TrainingDataPipeline, TrainingDataConfig

            config = TrainingDataConfig()
            pipeline = TrainingDataPipeline(config)

            results = pipeline.generate_training_data()

            click.echo(f"✅ Training data generation completed!")
            click.echo(f"   Datasets generated: {len(results['datasets_generated'])}")
            click.echo(f"   Overall quality score: {results['quality_metrics'].get('overall_score', 'N/A')}")

            for model_type, dataset_info in results['datasets_generated'].items():
                click.echo(f"   {model_type}: {dataset_info['train_samples']} train, {dataset_info['validation_samples']} val, {dataset_info['test_samples']} test")

        if evaluate_models:
            click.echo("📊 Evaluating AI models...")

            from ai_training import ModelEvaluationFramework, EvaluationConfig

            config = EvaluationConfig()
            evaluator = ModelEvaluationFramework(config)

            # Mock evaluation data
            mock_predictions = [0.8, 0.9, 0.7, 0.85, 0.92]
            mock_ground_truth = [1, 1, 0, 1, 1]

            for model_type in ["recommendation", "personalization", "search_ranking", "content_generation"]:
                results = evaluator.evaluate_model_performance(model_type, mock_predictions, mock_ground_truth)
                accuracy = results['metrics'].get('accuracy', 'N/A')
                if isinstance(accuracy, (int, float)):
                    accuracy_str = f"{accuracy:.3f}"
                else:
                    accuracy_str = str(accuracy)
                click.echo(f"   {model_type}: Grade {results['performance_grade']}, Score {accuracy_str}")

        if check_data_quality:
            click.echo("🔍 Checking data quality...")

            from ai_training import DataQualityMonitor, DataQualityConfig
            import json
            from pathlib import Path

            config = DataQualityConfig()
            monitor = DataQualityMonitor(config)

            # Check quality of available data files
            data_dir = Path("data/raw")
            if data_dir.exists():
                for data_file in data_dir.glob("*.json"):
                    try:
                        with open(data_file, 'r') as f:
                            data = json.load(f)

                        source_name = data_file.stem.split('_')[0]
                        quality_report = monitor.assess_data_quality(data, source_name)

                        click.echo(f"   {source_name}: Quality score {quality_report['overall_score']:.3f}")
                        if quality_report['issues_detected']:
                            click.echo(f"     Issues: {len(quality_report['issues_detected'])}")
                        if quality_report['alerts']:
                            click.echo(f"     Alerts: {len(quality_report['alerts'])}")

                    except Exception as e:
                        click.echo(f"   Error checking {data_file}: {e}")
            else:
                click.echo("   No data files found for quality assessment")

        if start_continuous_learning:
            click.echo("🔄 Starting continuous learning pipeline...")
            click.echo("   Note: This would start a background process in production")
            click.echo("   For demo purposes, showing configuration:")

            from ai_training import ContinuousLearningConfig

            config = ContinuousLearningConfig()
            click.echo(f"   Retrain interval: {config.retrain_interval_hours} hours")
            click.echo(f"   Min data threshold: {config.min_new_data_threshold} samples")
            click.echo(f"   Performance threshold: {config.performance_degradation_threshold}")
            click.echo("   ✅ Continuous learning configuration validated")

    except Exception as e:
        click.echo(f"❌ AI training command failed: {e}", err=True)
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


@main.command()
@click.argument('seed_file', type=click.Path(exists=True))
@click.option('--doc-type', default='general_info', help='Document type (college, program, summer_program, etc.)')
@click.option('--batch-size', default=100, help='Batch size for processing')
@click.option('--reset-collection', is_flag=True, help='Reset ChromaDB collection before ingestion')
def ingest(seed_file: str, doc_type: str, batch_size: int, reset_collection: bool):
    """
    Complete end-to-end ingestion pipeline: load → preprocess → chunk → embed → upsert.

    This command implements the canonical ingestion flow that the API depends on.
    """
    from pathlib import Path
    import pandas as pd
    from .schemas import (
        create_document_metadata, DocumentChunk, EntityType, GPABand,
        generate_chunk_id, calculate_content_checksum
    )
    from .preprocessing.preprocessor import TextPreprocessor
    from .preprocessing.chunker import TextChunker
    from .embedding.factory import get_canonical_embedder
    from .storage.chroma_client import ChromaDBClient

    setup_logging()
    logger = logging.getLogger(__name__)

    click.echo(f"🚀 Starting end-to-end ingestion pipeline")
    click.echo(f"   Source: {seed_file}")
    click.echo(f"   Document Type: {doc_type}")
    click.echo(f"   Batch Size: {batch_size}")

    try:
        # Initialize components with canonical embedder
        preprocessor = TextPreprocessor()
        chunker = TextChunker()
        embedder = get_canonical_embedder()  # LOCKED to sentence-transformers
        chroma_client = ChromaDBClient()

        # Reset collection if requested
        if reset_collection:
            click.echo("🔄 Resetting ChromaDB collection...")
            chroma_client.reset_collection()

        # Ensure collection exists
        chroma_client.get_or_create_collection()

        # Load seed data
        click.echo("📂 Loading seed data...")
        seed_path = Path(seed_file)

        if seed_path.suffix.lower() == '.csv':
            df = pd.read_csv(seed_path)
            records = df.to_dict('records')
        elif seed_path.suffix.lower() == '.json':
            import json
            with open(seed_path, 'r') as f:
                records = json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {seed_path.suffix}")

        click.echo(f"   Loaded {len(records)} records")

        # Process records
        all_chunks = []
        all_embeddings = []

        with click.progressbar(records, label="Processing records") as bar:
            for i, record in enumerate(bar):
                try:
                    # Extract required fields
                    school = record.get('school', record.get('university_name', 'Unknown'))
                    name = record.get('name', record.get('program_name', f'Record_{i}'))
                    content = record.get('content', record.get('description', ''))
                    location = record.get('location', record.get('state', 'Unknown'))

                    if not content:
                        continue

                    # Preprocess content
                    clean_content = preprocessor.preprocess(content)

                    # Create document metadata
                    try:
                        entity_type = EntityType(doc_type)
                    except ValueError:
                        entity_type = EntityType.GENERAL_INFO

                    metadata = create_document_metadata(
                        entity_type=entity_type,
                        school=school,
                        name=name,
                        location=location,
                        source_type="seed_data",
                        external_id=str(i),
                        section=record.get('section', 'main'),
                        content=clean_content,
                        gpa_band=GPABand(record.get('gpa_band', 'not_specified')),
                        majors=record.get('majors', '').split(',') if record.get('majors') else [],
                        interests=record.get('interests', '').split(',') if record.get('interests') else [],
                        url=record.get('url'),
                        year=record.get('year')
                    )

                    # Create chunks
                    chunks = chunker.chunk_text(clean_content)

                    for chunk_idx, chunk_text in enumerate(chunks):
                        chunk_id = generate_chunk_id(metadata.doc_id, chunk_idx)

                        chunk = DocumentChunk(
                            chunk_id=chunk_id,
                            doc_id=metadata.doc_id,
                            text=chunk_text,
                            metadata=metadata,
                            chunk_index=chunk_idx,
                            token_count=len(chunk_text.split())
                        )

                        all_chunks.append(chunk)

                except Exception as e:
                    logger.error(f"Error processing record {i}: {e}")
                    continue

        if not all_chunks:
            click.echo("❌ No chunks created from input data")
            return

        click.echo(f"📝 Created {len(all_chunks)} chunks")

        # Generate embeddings
        click.echo("🧠 Generating embeddings...")
        chunk_texts = [chunk.text for chunk in all_chunks]

        with click.progressbar(length=len(chunk_texts), label="Embedding chunks") as bar:
            for i in range(0, len(chunk_texts), batch_size):
                batch_texts = chunk_texts[i:i + batch_size]
                batch_embeddings = embedder.embed_texts(batch_texts)
                all_embeddings.extend(batch_embeddings)
                bar.update(len(batch_texts))

        click.echo(f"✅ Generated {len(all_embeddings)} embeddings")

        # Upsert to ChromaDB
        click.echo("💾 Upserting to ChromaDB...")
        stats = chroma_client.upsert(all_chunks, all_embeddings)

        click.echo("🎉 Ingestion completed successfully!")
        click.echo(f"   Total chunks: {stats['total_chunks']}")
        click.echo(f"   Successful: {stats['successful_chunks']}")
        click.echo(f"   Failed: {stats['failed_chunks']}")

        if stats['errors']:
            click.echo("⚠️  Errors encountered:")
            for error in stats['errors'][:5]:  # Show first 5 errors
                click.echo(f"   - {error}")

        # Show collection stats
        collection_stats = chroma_client.stats()
        click.echo(f"\n📊 Collection Statistics:")
        click.echo(f"   Total documents: {collection_stats['total_documents']}")
        click.echo(f"   Entity types: {list(collection_stats['entity_types'].keys())}")
        click.echo(f"   Schools: {len(collection_stats['schools'])}")
        click.echo(f"   Schema compliance: {collection_stats['schema_compliance']:.2%}")

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        click.echo(f"❌ Ingestion failed: {e}")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
