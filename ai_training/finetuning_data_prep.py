"""
Fine-tuning data preparation for Ollama LLM.

Prepares comprehensive training datasets from multiple sources:
- Institutional data from ChromaDB
- Q&A pairs for instruction tuning
- Conversational data for chat fine-tuning
- Domain-specific knowledge for RAG enhancement

Outputs data in formats compatible with:
- Ollama Modelfile format
- JSONL for instruction tuning
- Alpaca format for supervised fine-tuning
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class FineTuningDataPreparator:
    """
    Prepares training data for Ollama fine-tuning.
    
    Supports multiple fine-tuning approaches:
    1. Instruction tuning (Q&A pairs)
    2. Conversational fine-tuning (multi-turn dialogues)
    3. Domain adaptation (college admissions knowledge)
    4. RAG enhancement (retrieval-augmented generation)
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("data/finetuning")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            "total_examples": 0,
            "instruction_pairs": 0,
            "conversations": 0,
            "domain_texts": 0
        }
    
    def prepare_instruction_dataset(
        self,
        qa_pairs: List[Dict[str, str]],
        output_format: str = "alpaca"
    ) -> Path:
        """
        Prepare instruction tuning dataset from Q&A pairs.
        
        Args:
            qa_pairs: List of dicts with 'question' and 'answer' keys
            output_format: Format to use ('alpaca', 'jsonl', 'ollama')
            
        Returns:
            Path to generated dataset file
        """
        logger.info(f"Preparing instruction dataset with {len(qa_pairs)} examples...")
        
        if output_format == "alpaca":
            dataset = self._format_alpaca(qa_pairs)
            output_file = self.output_dir / "instruction_dataset_alpaca.json"
        elif output_format == "jsonl":
            dataset = self._format_jsonl(qa_pairs)
            output_file = self.output_dir / "instruction_dataset.jsonl"
        elif output_format == "ollama":
            dataset = self._format_ollama(qa_pairs)
            output_file = self.output_dir / "instruction_dataset_ollama.txt"
        else:
            raise ValueError(f"Unknown format: {output_format}")
        
        # Save dataset
        if output_format == "jsonl":
            with open(output_file, 'w') as f:
                for item in dataset:
                    f.write(json.dumps(item) + '\n')
        elif output_format == "ollama":
            with open(output_file, 'w') as f:
                f.write(dataset)
        else:
            with open(output_file, 'w') as f:
                json.dump(dataset, f, indent=2)
        
        self.stats["instruction_pairs"] = len(qa_pairs)
        self.stats["total_examples"] += len(qa_pairs)
        
        logger.info(f"Saved instruction dataset to {output_file}")
        return output_file
    
    def _format_alpaca(self, qa_pairs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format data in Alpaca instruction format."""
        formatted = []
        
        for qa in qa_pairs:
            formatted.append({
                "instruction": qa.get("question", ""),
                "input": qa.get("context", ""),
                "output": qa.get("answer", "")
            })
        
        return formatted
    
    def _format_jsonl(self, qa_pairs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Format data as JSONL for instruction tuning."""
        formatted = []
        
        for qa in qa_pairs:
            formatted.append({
                "prompt": qa.get("question", ""),
                "completion": qa.get("answer", ""),
                "metadata": {
                    "category": qa.get("category", "general"),
                    "difficulty": qa.get("difficulty", "medium")
                }
            })
        
        return formatted
    
    def _format_ollama(self, qa_pairs: List[Dict[str, str]]) -> str:
        """Format data for Ollama Modelfile."""
        lines = []
        
        for qa in qa_pairs:
            question = qa.get("question", "").strip()
            answer = qa.get("answer", "").strip()
            
            # Ollama expects conversational format
            lines.append(f"### Human: {question}")
            lines.append(f"### Assistant: {answer}")
            lines.append("")  # Blank line between examples
        
        return "\n".join(lines)
    
    def prepare_conversational_dataset(
        self,
        conversations: List[List[Dict[str, str]]],
        output_format: str = "jsonl"
    ) -> Path:
        """
        Prepare conversational dataset for chat fine-tuning.
        
        Args:
            conversations: List of conversation threads
            output_format: Format to use
            
        Returns:
            Path to generated dataset file
        """
        logger.info(f"Preparing conversational dataset with {len(conversations)} conversations...")
        
        formatted_convos = []
        
        for convo in conversations:
            formatted_convo = {
                "messages": []
            }
            
            for turn in convo:
                formatted_convo["messages"].append({
                    "role": turn.get("role", "user"),
                    "content": turn.get("content", "")
                })
            
            formatted_convos.append(formatted_convo)
        
        # Save dataset
        output_file = self.output_dir / "conversational_dataset.jsonl"
        with open(output_file, 'w') as f:
            for convo in formatted_convos:
                f.write(json.dumps(convo) + '\n')
        
        self.stats["conversations"] = len(conversations)
        self.stats["total_examples"] += len(conversations)
        
        logger.info(f"Saved conversational dataset to {output_file}")
        return output_file
    
    def prepare_domain_knowledge_dataset(
        self,
        knowledge_texts: List[Dict[str, str]],
        chunk_size: int = 512
    ) -> Path:
        """
        Prepare domain knowledge dataset for continued pre-training.
        
        Args:
            knowledge_texts: List of domain-specific texts
            chunk_size: Size of text chunks
            
        Returns:
            Path to generated dataset file
        """
        logger.info(f"Preparing domain knowledge dataset with {len(knowledge_texts)} texts...")
        
        chunks = []
        
        for text_doc in knowledge_texts:
            content = text_doc.get("content", "")
            
            # Split into chunks
            words = content.split()
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                chunks.append({
                    "text": chunk,
                    "source": text_doc.get("source", "unknown"),
                    "category": text_doc.get("category", "general")
                })
        
        # Save dataset
        output_file = self.output_dir / "domain_knowledge.jsonl"
        with open(output_file, 'w') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk) + '\n')
        
        self.stats["domain_texts"] = len(chunks)
        self.stats["total_examples"] += len(chunks)
        
        logger.info(f"Saved domain knowledge dataset to {output_file}")
        return output_file
    
    def create_ollama_modelfile(
        self,
        base_model: str = "llama3",
        system_prompt: str = None,
        parameters: Dict[str, Any] = None,
        training_data_path: Path = None
    ) -> Path:
        """
        Create Ollama Modelfile for fine-tuning.
        
        Args:
            base_model: Base model to fine-tune from
            system_prompt: Custom system prompt
            parameters: Model parameters (temperature, top_p, etc.)
            training_data_path: Path to training data file
            
        Returns:
            Path to generated Modelfile
        """
        logger.info("Creating Ollama Modelfile...")
        
        default_system_prompt = """You are an expert college admissions advisor with comprehensive knowledge of:
- College admissions requirements and processes
- University programs and academic offerings
- Financial aid and scholarship opportunities
- Student life and campus culture
- Career outcomes and ROI analysis

Provide accurate, helpful, and personalized guidance to students and families navigating the college admissions process."""
        
        system_prompt = system_prompt or default_system_prompt
        
        # Default parameters
        default_params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "num_ctx": 4096
        }
        
        if parameters:
            default_params.update(parameters)
        
        # Build Modelfile
        modelfile_lines = [
            f"FROM {base_model}",
            "",
            "# System prompt",
            f'SYSTEM """{system_prompt}"""',
            "",
            "# Parameters"
        ]
        
        for param, value in default_params.items():
            modelfile_lines.append(f"PARAMETER {param} {value}")
        
        if training_data_path:
            modelfile_lines.extend([
                "",
                "# Training data",
                f"# Use: ollama create collegeadvisor -f Modelfile",
                f"# Training data: {training_data_path}"
            ])
        
        modelfile_content = "\n".join(modelfile_lines)
        
        # Save Modelfile
        output_file = self.output_dir / "Modelfile"
        with open(output_file, 'w') as f:
            f.write(modelfile_content)
        
        logger.info(f"Saved Modelfile to {output_file}")
        return output_file
    
    def generate_qa_from_institutional_data(
        self,
        institutions: List[Dict[str, Any]],
        num_questions_per_institution: int = 5
    ) -> List[Dict[str, str]]:
        """
        Generate Q&A pairs from institutional data.
        
        Args:
            institutions: List of institution records
            num_questions_per_institution: Number of Q&A pairs to generate per institution
            
        Returns:
            List of Q&A pairs
        """
        logger.info(f"Generating Q&A pairs from {len(institutions)} institutions...")
        
        qa_pairs = []
        
        question_templates = [
            ("What is the admission rate at {name}?", "admission_rate"),
            ("What is the average SAT score at {name}?", "sat_average"),
            ("How much is tuition at {name}?", "tuition"),
            ("What is the enrollment size at {name}?", "enrollment"),
            ("Where is {name} located?", "location"),
        ]
        
        for inst in institutions:
            name = inst.get("name", "Unknown")
            
            for question_template, field_key in question_templates[:num_questions_per_institution]:
                question = question_template.format(name=name)
                
                # Generate answer based on available data
                answer = self._generate_answer(inst, field_key)
                
                if answer:
                    qa_pairs.append({
                        "question": question,
                        "answer": answer,
                        "category": "institutional_data",
                        "institution": name
                    })
        
        logger.info(f"Generated {len(qa_pairs)} Q&A pairs")
        return qa_pairs
    
    def _generate_answer(self, inst: Dict[str, Any], field_key: str) -> Optional[str]:
        """Generate answer from institutional data."""
        name = inst.get("name", "Unknown")
        
        if field_key == "admission_rate":
            rate = inst.get("admission_rate")
            if rate:
                return f"The admission rate at {name} is approximately {rate}%."
        
        elif field_key == "sat_average":
            sat = inst.get("sat_average")
            if sat:
                return f"The average SAT score at {name} is {sat}."
        
        elif field_key == "tuition":
            tuition = inst.get("tuition")
            if tuition:
                return f"The tuition at {name} is approximately ${tuition:,} per year."
        
        elif field_key == "enrollment":
            enrollment = inst.get("enrollment")
            if enrollment:
                return f"{name} has an enrollment of approximately {enrollment:,} students."
        
        elif field_key == "location":
            city = inst.get("city", "")
            state = inst.get("state", "")
            if city and state:
                return f"{name} is located in {city}, {state}."
        
        return None
    
    def export_statistics(self) -> Path:
        """Export dataset preparation statistics."""
        stats_file = self.output_dir / "preparation_stats.json"
        
        stats = {
            **self.stats,
            "timestamp": datetime.now().isoformat(),
            "output_directory": str(self.output_dir)
        }
        
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Exported statistics to {stats_file}")
        return stats_file


def prepare_complete_finetuning_dataset(
    institutions_file: Path,
    qa_pairs_file: Path = None,
    output_dir: Path = None
) -> Dict[str, Path]:
    """
    Prepare complete fine-tuning dataset from all sources.
    
    Args:
        institutions_file: Path to institutions JSON file
        qa_pairs_file: Optional path to existing Q&A pairs
        output_dir: Output directory for datasets
        
    Returns:
        Dict mapping dataset types to file paths
    """
    preparator = FineTuningDataPreparator(output_dir)
    
    # Load institutional data
    with open(institutions_file, 'r') as f:
        institutions = json.load(f)
    
    # Generate Q&A pairs from institutional data
    generated_qa = preparator.generate_qa_from_institutional_data(institutions)
    
    # Load additional Q&A pairs if provided
    if qa_pairs_file and qa_pairs_file.exists():
        with open(qa_pairs_file, 'r') as f:
            additional_qa = json.load(f)
        generated_qa.extend(additional_qa)
    
    # Prepare datasets in multiple formats
    datasets = {
        "alpaca": preparator.prepare_instruction_dataset(generated_qa, "alpaca"),
        "jsonl": preparator.prepare_instruction_dataset(generated_qa, "jsonl"),
        "ollama": preparator.prepare_instruction_dataset(generated_qa, "ollama"),
        "modelfile": preparator.create_ollama_modelfile(
            training_data_path=preparator.output_dir / "instruction_dataset_ollama.txt"
        )
    }
    
    # Export statistics
    preparator.export_statistics()
    
    return datasets

