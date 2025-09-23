"""Simple command-line interface for the College Advisor data pipeline."""

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
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(verbose: bool):
    """College Advisor Data Pipeline CLI."""
    if verbose:
        config.log_level = "DEBUG"
    setup_logging()


@main.command()
@click.option('--collector', '-c', type=click.Choice(['scorecard']), default='scorecard', help='Data collector to use')
@click.option('--years', '-y', help='Years to collect (comma-separated)')
@click.option('--states', '-s', help='States to collect (comma-separated)')
@click.option('--field-groups', '-f', help='Field groups to collect (comma-separated)')
@click.option('--page-size', '-p', type=int, default=5, help='Page size for API requests')
def collect(collector: str, years: Optional[str], states: Optional[str], field_groups: Optional[str], page_size: int):
    """Collect data from external sources."""
    click.echo(f"🔄 Starting data collection with {collector} collector...")
    
    try:
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
        
        # Show source information
        source_info = data_collector.get_source_info()
        click.echo(f"📊 Data Source: {source_info['name']}")
        click.echo(f"   Provider: {source_info['provider']}")
        click.echo(f"   Description: {source_info['description']}")
        
        # Note about DEMO_KEY limitations
        if config.college_scorecard_api_key == "DEMO_KEY":
            click.echo("⚠️  Using DEMO_KEY - limited to 10 requests per hour")
            click.echo("   Get a production API key from: https://api.data.gov/signup/")
        
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
        
        if result.errors:
            click.echo(f"⚠️  Errors: {len(result.errors)}")
            for error in result.errors[:3]:
                click.echo(f"   - {error}")
            
    except Exception as e:
        click.echo(f"❌ Collection failed: {e}", err=True)
        raise click.Abort()


@main.command()
def init():
    """Initialize the College Advisor data pipeline."""
    click.echo("🚀 Initializing College Advisor Data Pipeline...")
    
    try:
        # Create necessary directories
        config.data_dir.mkdir(parents=True, exist_ok=True)
        config.processed_dir.mkdir(parents=True, exist_ok=True)
        config.cache_dir.mkdir(parents=True, exist_ok=True)
        
        if config.log_file:
            config.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        click.echo(f"✅ Created data directory: {config.data_dir}")
        click.echo(f"✅ Created processed directory: {config.processed_dir}")
        click.echo(f"✅ Created cache directory: {config.cache_dir}")
        
        click.echo("\n🎉 Initialization completed!")
        click.echo("\nNext steps:")
        click.echo("1. Configure your API keys in .env file")
        click.echo("2. Start collecting data: college-data collect --help")
        
    except Exception as e:
        click.echo(f"❌ Initialization failed: {e}", err=True)
        raise click.Abort()


@main.command()
def config_show():
    """Show current configuration."""
    click.echo("⚙️  Current Configuration:")
    click.echo(f"   Data Directory: {config.data_dir}")
    click.echo(f"   Cache Directory: {config.cache_dir}")
    click.echo(f"   Log Level: {config.log_level}")
    click.echo(f"   College Scorecard API Key: {config.college_scorecard_api_key}")
    click.echo(f"   Default Requests/Second: {config.default_requests_per_second}")


@main.command()
def test():
    """Test the collector functionality."""
    click.echo("🧪 Testing College Scorecard collector...")
    
    try:
        from collectors.base_collector import CollectorConfig
        from collectors.government import CollegeScorecardCollector
        
        # Create collector configuration
        collector_config = CollectorConfig(
            api_key=config.college_scorecard_api_key,
            requests_per_second=0.5,  # Very slow for DEMO_KEY
            cache_enabled=True,
            cache_ttl_hours=24,
            output_format="json"
        )
        
        # Initialize collector
        collector = CollegeScorecardCollector(collector_config)
        
        # Test source info
        source_info = collector.get_source_info()
        click.echo(f"✅ Source: {source_info['name']}")
        click.echo(f"   Fields: {source_info['total_fields']}")
        click.echo(f"   Categories: {len(source_info['data_categories'])}")
        
        # Test field groups
        field_groups = collector.FIELD_GROUPS
        click.echo(f"✅ Found {len(field_groups)} field groups:")
        for name, fields in field_groups.items():
            click.echo(f"   - {name}: {len(fields)} fields")
        
        click.echo("\n🎉 Basic tests passed!")
        click.echo("\nNote: Data collection test skipped due to DEMO_KEY rate limits.")
        click.echo("To test data collection, get a production API key from:")
        click.echo("https://api.data.gov/signup/")
        
    except Exception as e:
        click.echo(f"❌ Test failed: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    main()
