"""
Training utilities for CollegeAdvisor AI training pipeline.

This module provides utilities for handling different training environments
and gracefully falling back when GPU-specific libraries are not available.
"""

import logging
import warnings
from typing import Optional, Tuple, Any

logger = logging.getLogger(__name__)


def check_training_environment() -> dict:
    """
    Check the current training environment and available libraries.
    
    Returns:
        dict: Environment information including available libraries and capabilities
    """
    env_info = {
        "cuda_available": False,
        "unsloth_available": False,
        "torch_available": False,
        "transformers_available": False,
        "recommended_trainer": "cpu",
        "warnings": []
    }
    
    # Check PyTorch
    try:
        import torch
        env_info["torch_available"] = True
        env_info["cuda_available"] = torch.cuda.is_available()
        env_info["torch_version"] = torch.__version__
        logger.info(f"PyTorch {torch.__version__} available, CUDA: {env_info['cuda_available']}")
    except ImportError:
        env_info["warnings"].append("PyTorch not available")
        logger.warning("PyTorch not available")
    
    # Check Transformers
    try:
        import transformers
        env_info["transformers_available"] = True
        env_info["transformers_version"] = transformers.__version__
        logger.info(f"Transformers {transformers.__version__} available")
    except ImportError:
        env_info["warnings"].append("Transformers not available")
        logger.warning("Transformers not available")
    
    # Check Unsloth (with graceful fallback)
    try:
        # Suppress CUDA warnings temporarily
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import unsloth
            env_info["unsloth_available"] = True
            env_info["unsloth_version"] = getattr(unsloth, '__version__', 'unknown')
            logger.info(f"Unsloth available")
    except (ImportError, AssertionError, RuntimeError) as e:
        env_info["warnings"].append(f"Unsloth not available: {str(e)}")
        logger.warning(f"Unsloth not available: {str(e)}")
    
    # Determine recommended trainer
    if env_info["cuda_available"] and env_info["unsloth_available"]:
        env_info["recommended_trainer"] = "unsloth"
    elif env_info["cuda_available"] and env_info["transformers_available"]:
        env_info["recommended_trainer"] = "gpu"
    elif env_info["transformers_available"]:
        env_info["recommended_trainer"] = "cpu"
    else:
        env_info["recommended_trainer"] = "none"
        env_info["warnings"].append("No suitable training environment found")
    
    return env_info


def get_trainer_class(trainer_type: str = "auto"):
    """
    Get the appropriate trainer class based on environment and preference.
    
    Args:
        trainer_type: Type of trainer ("auto", "unsloth", "gpu", "cpu")
        
    Returns:
        Trainer class or None if not available
    """
    env_info = check_training_environment()
    
    if trainer_type == "auto":
        trainer_type = env_info["recommended_trainer"]
    
    if trainer_type == "unsloth":
        if env_info["unsloth_available"] and env_info["cuda_available"]:
            try:
                from .run_sft import CollegeAdvisorSFTTrainer
                return CollegeAdvisorSFTTrainer
            except ImportError as e:
                logger.warning(f"Could not import unsloth trainer: {e}")
                trainer_type = "gpu"
        else:
            logger.warning("Unsloth trainer requested but not available, falling back to GPU trainer")
            trainer_type = "gpu"
    
    if trainer_type == "gpu":
        if env_info["cuda_available"] and env_info["transformers_available"]:
            try:
                from .run_sft_cpu import CollegeAdvisorCPUTrainer
                
                class GPUTrainer(CollegeAdvisorCPUTrainer):
                    def __init__(self, *args, **kwargs):
                        kwargs['use_cpu'] = False
                        super().__init__(*args, **kwargs)
                
                return GPUTrainer
            except ImportError as e:
                logger.warning(f"Could not import GPU trainer: {e}")
                trainer_type = "cpu"
        else:
            logger.warning("GPU trainer requested but CUDA not available, falling back to CPU trainer")
            trainer_type = "cpu"
    
    if trainer_type == "cpu":
        if env_info["transformers_available"]:
            try:
                from .run_sft_cpu import CollegeAdvisorCPUTrainer
                return CollegeAdvisorCPUTrainer
            except ImportError as e:
                logger.error(f"Could not import CPU trainer: {e}")
                return None
        else:
            logger.error("CPU trainer requested but transformers not available")
            return None
    
    logger.error(f"No suitable trainer found for type: {trainer_type}")
    return None


def create_sample_training_data(output_path: str, num_samples: int = 10):
    """
    Create sample training data for testing purposes.
    
    Args:
        output_path: Path to save the sample data
        num_samples: Number of sample Q&A pairs to generate
    """
    import json
    from pathlib import Path
    
    sample_data = [
        {
            "question": "What should I consider when choosing a college major?",
            "answer": "When choosing a college major, consider your interests, career goals, job market prospects, required coursework, and potential salary. It's also important to think about your strengths and what subjects you enjoy studying."
        },
        {
            "question": "How important are extracurricular activities for college admissions?",
            "answer": "Extracurricular activities are very important for college admissions as they demonstrate your interests, leadership skills, and commitment outside of academics. Quality and depth of involvement matter more than quantity."
        },
        {
            "question": "What is the difference between in-state and out-of-state tuition?",
            "answer": "In-state tuition is typically much lower than out-of-state tuition at public universities. In-state students are residents of the state where the university is located, while out-of-state students come from other states and pay higher fees."
        },
        {
            "question": "How can I prepare for college entrance exams like the SAT or ACT?",
            "answer": "To prepare for college entrance exams, take practice tests, review fundamental concepts, consider prep courses or tutoring, and start preparing well in advance. Focus on your weaker areas and develop test-taking strategies."
        },
        {
            "question": "What financial aid options are available for college students?",
            "answer": "Financial aid options include federal grants (like Pell Grants), scholarships, work-study programs, and student loans. Complete the FAFSA to determine eligibility for federal aid, and research institutional and private scholarships."
        }
    ]
    
    # Add more samples if requested
    while len(sample_data) < num_samples:
        sample_data.extend(sample_data[:min(len(sample_data), num_samples - len(sample_data))])
    
    sample_data = sample_data[:num_samples]
    
    # Save to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    logger.info(f"Created sample training data with {len(sample_data)} examples at: {output_path}")


def print_environment_report():
    """Print a detailed environment report for debugging."""
    env_info = check_training_environment()
    
    print("\n" + "="*60)
    print("COLLEGEADVISOR AI TRAINING ENVIRONMENT REPORT")
    print("="*60)
    
    print(f"PyTorch Available: {env_info['torch_available']}")
    if env_info['torch_available']:
        print(f"  Version: {env_info.get('torch_version', 'unknown')}")
        print(f"  CUDA Available: {env_info['cuda_available']}")
    
    print(f"Transformers Available: {env_info['transformers_available']}")
    if env_info['transformers_available']:
        print(f"  Version: {env_info.get('transformers_version', 'unknown')}")
    
    print(f"Unsloth Available: {env_info['unsloth_available']}")
    if env_info['unsloth_available']:
        print(f"  Version: {env_info.get('unsloth_version', 'unknown')}")
    
    print(f"\nRecommended Trainer: {env_info['recommended_trainer']}")
    
    if env_info['warnings']:
        print(f"\nWarnings:")
        for warning in env_info['warnings']:
            print(f"  - {warning}")
    
    print("="*60)


if __name__ == "__main__":
    print_environment_report()
