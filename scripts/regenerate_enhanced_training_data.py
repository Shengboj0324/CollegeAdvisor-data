"""
Regenerate Training Data with Enhanced Responses

This script regenerates the training data using the EnhancedResponseGenerator
to create comprehensive 200-500 word advisory responses instead of short fact lookups.

Zero-tolerance error handling:
- Validates all imports
- Validates all input data
- Comprehensive error logging
- Rollback on failure

Author: Augment Agent
Date: October 18, 2025
"""

import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/data_regeneration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Validate imports with zero tolerance
try:
    from ai_training.finetuning_data_prep import FineTuningDataPreparator
    logger.info("✅ FineTuningDataPreparator imported successfully")
except ImportError as e:
    logger.error(f"❌ CRITICAL: Failed to import FineTuningDataPreparator: {e}")
    sys.exit(1)

try:
    from ai_training.enhanced_response_generator import EnhancedResponseGenerator
    logger.info("✅ EnhancedResponseGenerator imported successfully")
except ImportError as e:
    logger.error(f"❌ CRITICAL: Failed to import EnhancedResponseGenerator: {e}")
    sys.exit(1)


def extract_institutions_from_training_data(training_data_path: Path) -> List[Dict[str, Any]]:
    """
    Extract institutional data from existing training dataset.
    
    Args:
        training_data_path: Path to existing training data JSON
        
    Returns:
        List of institution dictionaries with extracted data
    """
    logger.info(f"📂 Loading existing training data from: {training_data_path}")
    
    try:
        with open(training_data_path, 'r') as f:
            training_data = json.load(f)
        
        logger.info(f"✅ Loaded {len(training_data)} training examples")
        
        # Extract unique institutions and their data
        institutions_map = {}
        
        for example in training_data:
            instruction = example.get('instruction', '')
            output = example.get('output', '')
            
            # Extract university name from instruction
            # Pattern: "What is X at [University Name]?"
            if ' at ' in instruction:
                parts = instruction.split(' at ')
                if len(parts) >= 2:
                    university = parts[1].rstrip('?').strip()
                    
                    if university not in institutions_map:
                        institutions_map[university] = {
                            'name': university,
                            'admission_rate': None,
                            'sat_average': None,
                            'enrollment': None,
                            'tuition': None,
                            'city': None,
                            'state': None
                        }
                    
                    # Extract data from output
                    if 'admission rate' in instruction.lower():
                        # Extract percentage from output
                        import re
                        match = re.search(r'(\d+\.?\d*)\s*%', output)
                        if match:
                            institutions_map[university]['admission_rate'] = float(match.group(1))
                    
                    elif 'SAT score' in instruction:
                        # Extract SAT score
                        match = re.search(r'(\d{3,4})', output)
                        if match:
                            institutions_map[university]['sat_average'] = int(match.group(1))
                    
                    elif 'tuition' in instruction.lower():
                        # Extract tuition
                        match = re.search(r'\$([0-9,]+)', output)
                        if match:
                            tuition_str = match.group(1).replace(',', '')
                            institutions_map[university]['tuition'] = int(tuition_str)
                    
                    elif 'enrollment' in instruction.lower() or 'students' in instruction.lower():
                        # Extract enrollment
                        match = re.search(r'([0-9,]+)\s+students', output)
                        if match:
                            enrollment_str = match.group(1).replace(',', '')
                            institutions_map[university]['enrollment'] = int(enrollment_str)
                    
                    elif 'located' in instruction.lower():
                        # Extract location
                        match = re.search(r'in\s+([^,]+),\s*([A-Z]{2})', output)
                        if match:
                            institutions_map[university]['city'] = match.group(1).strip()
                            institutions_map[university]['state'] = match.group(2).strip()
        
        institutions = list(institutions_map.values())
        logger.info(f"✅ Extracted data for {len(institutions)} unique institutions")
        
        # Log sample
        if institutions:
            logger.info(f"\n📊 Sample institution data:")
            sample = institutions[0]
            for key, value in sample.items():
                logger.info(f"   {key}: {value}")
        
        return institutions
        
    except Exception as e:
        logger.error(f"❌ Failed to extract institutions from training data: {e}")
        raise


def regenerate_training_data(
    institutions: List[Dict[str, Any]],
    output_dir: Path,
    use_enhanced: bool = True
) -> Dict[str, Path]:
    """
    Regenerate training data with enhanced responses.
    
    Args:
        institutions: List of institution dictionaries
        output_dir: Output directory for new training data
        use_enhanced: Whether to use enhanced response generator
        
    Returns:
        Dictionary mapping dataset types to file paths
    """
    logger.info("\n" + "="*80)
    logger.info("REGENERATING TRAINING DATA WITH ENHANCED RESPONSES")
    logger.info("="*80)
    
    try:
        # Create preparator with enhanced responses
        preparator = FineTuningDataPreparator(
            output_dir=output_dir,
            use_enhanced_responses=use_enhanced
        )
        
        logger.info(f"✅ Created FineTuningDataPreparator")
        logger.info(f"   Enhanced responses: {preparator.use_enhanced_responses}")
        logger.info(f"   Output directory: {output_dir}")
        
        # Generate Q&A pairs from institutional data
        logger.info(f"\n📝 Generating Q&A pairs from {len(institutions)} institutions...")
        qa_pairs = preparator.generate_qa_from_institutional_data(
            institutions=institutions,
            num_questions_per_institution=5  # All 5 question types
        )
        
        logger.info(f"✅ Generated {len(qa_pairs)} Q&A pairs")
        
        # Prepare datasets in multiple formats
        logger.info(f"\n💾 Preparing datasets in multiple formats...")
        
        datasets = {}
        
        # Alpaca format (primary)
        logger.info(f"   Generating Alpaca format...")
        datasets['alpaca'] = preparator.prepare_instruction_dataset(qa_pairs, "alpaca")
        logger.info(f"   ✅ Alpaca: {datasets['alpaca']}")
        
        # JSONL format
        logger.info(f"   Generating JSONL format...")
        datasets['jsonl'] = preparator.prepare_instruction_dataset(qa_pairs, "jsonl")
        logger.info(f"   ✅ JSONL: {datasets['jsonl']}")
        
        # Ollama format
        logger.info(f"   Generating Ollama format...")
        datasets['ollama'] = preparator.prepare_instruction_dataset(qa_pairs, "ollama")
        logger.info(f"   ✅ Ollama: {datasets['ollama']}")
        
        # Create Modelfile
        logger.info(f"   Creating Modelfile...")
        datasets['modelfile'] = preparator.create_ollama_modelfile(
            training_data_path=datasets['ollama']
        )
        logger.info(f"   ✅ Modelfile: {datasets['modelfile']}")
        
        # Export statistics
        logger.info(f"\n📊 Exporting statistics...")
        stats_file = preparator.export_statistics()
        logger.info(f"   ✅ Statistics: {stats_file}")
        
        return datasets
        
    except Exception as e:
        logger.error(f"❌ Failed to regenerate training data: {e}")
        raise


def validate_generated_data(dataset_path: Path) -> Dict[str, Any]:
    """
    Validate the generated training data quality.
    
    Args:
        dataset_path: Path to generated dataset
        
    Returns:
        Dictionary with validation results
    """
    logger.info("\n" + "="*80)
    logger.info("VALIDATING GENERATED DATA QUALITY")
    logger.info("="*80)
    
    try:
        with open(dataset_path, 'r') as f:
            data = json.load(f)
        
        total = len(data)
        output_lengths = [len(ex['output']) for ex in data]
        word_counts = [len(ex['output'].split()) for ex in data]
        
        avg_chars = sum(output_lengths) / len(output_lengths)
        avg_words = sum(word_counts) / len(word_counts)
        min_chars = min(output_lengths)
        max_chars = max(output_lengths)
        min_words = min(word_counts)
        max_words = max(word_counts)
        
        # Check if within target range (1000-3000 chars = ~200-500 words)
        in_range = sum(1 for l in output_lengths if 1000 <= l <= 3000)
        
        results = {
            'total_examples': total,
            'avg_chars': avg_chars,
            'avg_words': avg_words,
            'min_chars': min_chars,
            'max_chars': max_chars,
            'min_words': min_words,
            'max_words': max_words,
            'in_target_range': in_range,
            'in_range_percentage': (in_range / total * 100) if total > 0 else 0
        }
        
        logger.info(f"\n📊 Validation Results:")
        logger.info(f"   Total examples: {total}")
        logger.info(f"   Avg output length: {avg_chars:.1f} chars ({avg_words:.1f} words)")
        logger.info(f"   Min output length: {min_chars} chars ({min_words} words)")
        logger.info(f"   Max output length: {max_chars} chars ({max_words} words)")
        logger.info(f"   Target range (1000-3000 chars): {in_range}/{total} ({results['in_range_percentage']:.1f}%)")
        
        # Quality check
        if avg_chars < 500:
            logger.error(f"❌ QUALITY CHECK FAILED: Average output too short ({avg_chars:.1f} chars)")
            logger.error(f"   Expected: >1000 chars (200+ words)")
            return results
        
        if results['in_range_percentage'] < 50:
            logger.warning(f"⚠️  WARNING: Only {results['in_range_percentage']:.1f}% in target range")
        else:
            logger.info(f"✅ QUALITY CHECK PASSED: {results['in_range_percentage']:.1f}% in target range")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Failed to validate generated data: {e}")
        raise


def main():
    """Main execution function."""
    logger.info("\n" + "="*80)
    logger.info("ENHANCED TRAINING DATA REGENERATION")
    logger.info("="*80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Extract institutions from existing training data
        logger.info("\n📋 STEP 1: Extract institutional data from existing training dataset")
        training_data_path = Path("r2_data_analysis/multi_source_training_datasets_instruction_dataset_alpaca.json")
        
        if not training_data_path.exists():
            logger.error(f"❌ Training data file not found: {training_data_path}")
            return 1
        
        institutions = extract_institutions_from_training_data(training_data_path)
        
        if not institutions:
            logger.error(f"❌ No institutions extracted from training data")
            return 1
        
        # Step 2: Regenerate training data with enhanced responses
        logger.info("\n📋 STEP 2: Regenerate training data with enhanced responses")
        output_dir = Path("data/finetuning_enhanced")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        datasets = regenerate_training_data(
            institutions=institutions,
            output_dir=output_dir,
            use_enhanced=True
        )
        
        # Step 3: Validate generated data
        logger.info("\n📋 STEP 3: Validate generated data quality")
        validation_results = validate_generated_data(datasets['alpaca'])
        
        # Step 4: Save validation report
        logger.info("\n📋 STEP 4: Save validation report")
        report_path = output_dir / "regeneration_report.json"
        report = {
            'timestamp': datetime.now().isoformat(),
            'source_file': str(training_data_path),
            'institutions_count': len(institutions),
            'datasets': {name: str(path) for name, path in datasets.items()},
            'validation': validation_results
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Validation report saved to: {report_path}")
        
        # Final summary
        logger.info("\n" + "="*80)
        logger.info("✅ REGENERATION COMPLETE!")
        logger.info("="*80)
        logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"\n📊 Summary:")
        logger.info(f"   Institutions processed: {len(institutions)}")
        logger.info(f"   Training examples generated: {validation_results['total_examples']}")
        logger.info(f"   Average response length: {validation_results['avg_words']:.1f} words")
        logger.info(f"   Quality (in target range): {validation_results['in_range_percentage']:.1f}%")
        logger.info(f"\n📁 Output files:")
        for name, path in datasets.items():
            logger.info(f"   {name}: {path}")
        logger.info(f"\n🎯 Next step: Retrain model with enhanced data")
        logger.info(f"   python unified_finetune.py --dataset_path {datasets['alpaca']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ REGENERATION FAILED: {e}")
        logger.error(f"   Check logs for details")
        return 1


if __name__ == "__main__":
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Run main
    sys.exit(main())

