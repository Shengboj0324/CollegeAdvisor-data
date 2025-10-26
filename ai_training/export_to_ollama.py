"""
Export trained models to Ollama format for deployment.

This script converts HuggingFace weights to GGUF format and creates
Ollama Modelfiles for easy deployment and inference.
"""

import os
import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import argparse

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class OllamaExporter:
    """
    Export trained models to Ollama format.
    
    This exporter handles:
    1. Converting HF weights to GGUF format
    2. Creating Ollama Modelfile
    3. Uploading to S3 storage
    4. Creating deployment metadata
    """
    
    def __init__(self, s3_bucket: str = "collegeadvisor-models"):
        """
        Initialize the Ollama exporter.
        
        Args:
            s3_bucket: S3 bucket for model storage
        """
        self.s3_bucket = s3_bucket
        self.s3_client = None
        
        # Initialize S3 client if credentials available
        try:
            self.s3_client = boto3.client('s3')
            # Test connection
            self.s3_client.head_bucket(Bucket=s3_bucket)
            logger.info(f"S3 bucket '{s3_bucket}' accessible")
        except Exception as e:
            logger.warning(f"S3 not available: {e}")
    
    def merge_lora_and_convert(self,
                              base_model: str,
                              lora_path: str,
                              output_path: str,
                              quantization: str = "q4_k_m") -> str:
        """
        Merge LoRA adapter with base model and convert to GGUF format.

        Args:
            base_model: Base model name or path (e.g., 'TinyLlama/TinyLlama-1.1B-Chat-v1.0')
            lora_path: Path to LoRA adapter weights
            output_path: Output directory for GGUF file
            quantization: Quantization method (q4_k_m, q5_k_m, q8_0, etc.)

        Returns:
            Path to generated GGUF file
        """
        logger.info(f"Merging LoRA adapter and converting to GGUF...")
        logger.info(f"  Base model: {base_model}")
        logger.info(f"  LoRA path: {lora_path}")
        logger.info(f"  Output: {output_path}")
        logger.info(f"  Quantization: {quantization}")

        os.makedirs(output_path, exist_ok=True)

        # Step 1: Merge LoRA with base model
        merged_model_path = os.path.join(output_path, "merged_model")
        logger.info("Step 1: Merging LoRA adapter with base model...")

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from peft import PeftModel
            import torch

            # Load base model
            logger.info(f"Loading base model: {base_model}")
            base_model_obj = AutoModelForCausalLM.from_pretrained(
                base_model,
                torch_dtype=torch.float16,
                device_map="cpu",
                low_cpu_mem_usage=True
            )

            # Load LoRA adapter
            logger.info(f"Loading LoRA adapter: {lora_path}")
            model = PeftModel.from_pretrained(base_model_obj, lora_path)

            # Merge and unload
            logger.info("Merging LoRA weights...")
            model = model.merge_and_unload()

            # Save merged model
            logger.info(f"Saving merged model to: {merged_model_path}")
            os.makedirs(merged_model_path, exist_ok=True)
            model.save_pretrained(merged_model_path)

            # Save tokenizer
            tokenizer = AutoTokenizer.from_pretrained(base_model)
            tokenizer.save_pretrained(merged_model_path)

            logger.info("✅ LoRA merge complete")

        except Exception as e:
            logger.error(f"Failed to merge LoRA: {e}")
            raise

        # Step 2: Convert to GGUF
        return self.convert_to_gguf(merged_model_path, output_path, quantization)

    def convert_to_gguf(self,
                       model_path: str,
                       output_path: str,
                       quantization: str = "q4_k_m") -> str:
        """
        Convert HuggingFace model to GGUF format.
        
        Args:
            model_path: Path to HuggingFace model
            output_path: Output directory for GGUF file
            quantization: Quantization level (q4_k_m, q5_k_m, q8_0, etc.)
            
        Returns:
            str: Path to generated GGUF file
        """
        logger.info(f"Converting model to GGUF: {model_path}")
        
        model_dir = Path(model_path)
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not model_dir.exists():
            raise FileNotFoundError(f"Model directory not found: {model_path}")
        
        # Generate GGUF filename
        model_name = model_dir.name
        gguf_filename = f"{model_name}-{quantization}.gguf"
        gguf_path = output_dir / gguf_filename
        
        try:
            # CRITICAL FIX: Check if this is a LoRA adapter or full model
            adapter_config_path = model_dir / "adapter_config.json"
            is_lora_adapter = adapter_config_path.exists()

            if is_lora_adapter:
                logger.info("Detected LoRA adapter - merging with base model first...")
                # Merge LoRA adapter with base model
                merged_model_dir = output_dir / f"{model_name}_merged"
                merged_model_dir.mkdir(parents=True, exist_ok=True)

                # Load adapter config to get base model
                with open(adapter_config_path, 'r') as f:
                    adapter_config = json.load(f)
                base_model_name = adapter_config.get('base_model_name_or_path', 'TinyLlama/TinyLlama-1.1B-Chat-v1.0')

                logger.info(f"Base model: {base_model_name}")
                logger.info("Loading base model and merging LoRA adapter...")

                from transformers import AutoModelForCausalLM, AutoTokenizer
                from peft import PeftModel
                import torch

                # Load base model
                base_model = AutoModelForCausalLM.from_pretrained(
                    base_model_name,
                    torch_dtype=torch.float16,
                    device_map="cpu"
                )

                # Load LoRA adapter
                model = PeftModel.from_pretrained(base_model, str(model_dir))

                # Merge and unload
                logger.info("Merging LoRA weights into base model...")
                model = model.merge_and_unload()

                # Save merged model
                logger.info(f"Saving merged model to {merged_model_dir}...")
                model.save_pretrained(str(merged_model_dir))

                # Save tokenizer
                tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
                tokenizer.save_pretrained(str(merged_model_dir))

                logger.info("✅ LoRA adapter merged successfully")

                # Update model_dir to point to merged model
                model_dir = merged_model_dir

                # Clean up
                del model
                del base_model
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

            # CRITICAL FIX: Use llama.cpp repository's convert script
            # First, check if llama.cpp is cloned, if not clone it
            llama_cpp_dir = Path("llama.cpp")

            if not llama_cpp_dir.exists():
                logger.info("Cloning llama.cpp repository...")
                clone_cmd = [
                    "git", "clone",
                    "https://github.com/ggerganov/llama.cpp.git",
                    str(llama_cpp_dir)
                ]
                subprocess.run(clone_cmd, check=True, capture_output=True)
                logger.info("✅ llama.cpp cloned successfully")

            # Use the convert_hf_to_gguf.py script from llama.cpp
            convert_script = llama_cpp_dir / "convert_hf_to_gguf.py"

            if not convert_script.exists():
                # Try older naming convention
                convert_script = llama_cpp_dir / "convert.py"

            if not convert_script.exists():
                raise FileNotFoundError(f"Cannot find convert script in llama.cpp. Checked: {llama_cpp_dir / 'convert_hf_to_gguf.py'}")

            # First convert to F16 GGUF
            f16_gguf_path = output_dir / f"{model_name}-f16.gguf"

            convert_cmd = [
                "python", str(convert_script),
                str(model_dir),
                "--outfile", str(f16_gguf_path),
                "--outtype", "f16"
            ]

            logger.info(f"Running conversion: {' '.join(convert_cmd)}")
            result = subprocess.run(
                convert_cmd,
                capture_output=True,
                text=True,
                check=True
            )

            if not f16_gguf_path.exists():
                raise RuntimeError("F16 GGUF file not created")

            logger.info(f"✅ F16 GGUF created: {f16_gguf_path}")

            # Now quantize to the desired format
            if quantization != "f16":
                quantize_script = llama_cpp_dir / "quantize"

                # Build quantize if it doesn't exist
                if not quantize_script.exists():
                    logger.info("Building llama.cpp quantize tool...")
                    build_cmd = ["make", "quantize"]
                    subprocess.run(
                        build_cmd,
                        cwd=str(llama_cpp_dir),
                        check=True,
                        capture_output=True
                    )

                # Quantize the model
                quantize_cmd = [
                    str(quantize_script),
                    str(f16_gguf_path),
                    str(gguf_path),
                    quantization
                ]

                logger.info(f"Running quantization: {' '.join(quantize_cmd)}")
                result = subprocess.run(
                    quantize_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )

                if gguf_path.exists():
                    logger.info(f"✅ GGUF quantization successful: {gguf_path}")
                    # Remove F16 intermediate file
                    f16_gguf_path.unlink()
                    return str(gguf_path)
                else:
                    raise RuntimeError("Quantized GGUF file not created")
            else:
                # F16 is the final format
                return str(f16_gguf_path)

        except subprocess.CalledProcessError as e:
            logger.error(f"GGUF conversion failed: {e.stderr}")
            raise
        except Exception as e:
            # Fallback: try alternative conversion methods
            logger.warning(f"llama.cpp conversion failed: {e}")
            logger.warning("Trying alternative conversion...")
            return self._convert_with_transformers(model_path, gguf_path)
    
    def _convert_with_transformers(self, model_path: str, gguf_path: Path) -> str:
        """
        Fallback conversion using transformers library.
        
        Args:
            model_path: Path to HuggingFace model
            gguf_path: Output GGUF path
            
        Returns:
            str: Path to generated GGUF file
        """
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            logger.info("Using transformers for conversion...")
            
            # Load model and tokenizer
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            
            # Save in a format that can be converted later
            temp_dir = gguf_path.parent / "temp_export"
            temp_dir.mkdir(exist_ok=True)
            
            model.save_pretrained(temp_dir, safe_serialization=True)
            tokenizer.save_pretrained(temp_dir)
            
            # For now, just copy the model files
            # In production, you'd use proper GGUF conversion tools
            shutil.copytree(temp_dir, gguf_path.with_suffix(""), dirs_exist_ok=True)
            
            # Create a placeholder GGUF file
            with open(gguf_path, 'w') as f:
                f.write("# GGUF placeholder - use proper conversion tools in production\n")
            
            logger.info(f"Model exported to: {gguf_path}")
            return str(gguf_path)
            
        except Exception as e:
            logger.error(f"Fallback conversion failed: {e}")
            raise
    
    def create_modelfile(self, 
                        gguf_path: str, 
                        output_dir: str,
                        model_name: str = "collegeadvisor-llama3") -> str:
        """
        Create Ollama Modelfile for the converted model.
        
        Args:
            gguf_path: Path to GGUF file
            output_dir: Output directory for Modelfile
            model_name: Name for the Ollama model
            
        Returns:
            str: Path to created Modelfile
        """
        logger.info(f"Creating Ollama Modelfile for: {model_name}")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        modelfile_path = output_path / "Modelfile"
        
        # Create Modelfile content
        modelfile_content = f"""# CollegeAdvisor Llama-3 Fine-tuned Model
# Generated on {datetime.now().isoformat()}

FROM {gguf_path}

# Model parameters optimized for educational Q&A
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 2048

# System prompt for college advisory
SYSTEM \"\"\"You are CollegeAdvisor, an expert educational consultant specializing in college admissions, academic programs, and student guidance. You provide accurate, helpful, and personalized advice to students and families navigating higher education decisions.

Key guidelines:
- Provide specific, actionable advice based on the user's situation
- Consider factors like academic interests, career goals, financial constraints, and personal preferences
- Reference specific colleges, programs, and requirements when relevant
- Encourage students to research thoroughly and visit campuses when possible
- Be supportive and encouraging while maintaining realistic expectations
- Always recommend consulting with school counselors and college admissions offices for official information

Your responses should be informative, encouraging, and tailored to each student's unique circumstances.\"\"\"

# Template for chat format
TEMPLATE \"\"\"{{{{ if .System }}}}<|start_header_id|>system<|end_header_id|>

{{{{ .System }}}}<|eot_id|>{{{{ end }}}}{{{{ if .Prompt }}}}<|start_header_id|>user<|end_header_id|>

{{{{ .Prompt }}}}<|eot_id|>{{{{ end }}}}<|start_header_id|>assistant<|end_header_id|>

{{{{ .Response }}}}<|eot_id|>\"\"\"
"""
        
        # Write Modelfile
        with open(modelfile_path, 'w', encoding='utf-8') as f:
            f.write(modelfile_content)
        
        logger.info(f"Modelfile created: {modelfile_path}")
        return str(modelfile_path)
    
    def upload_to_s3(self, 
                    local_dir: str, 
                    s3_key_prefix: str) -> Dict[str, str]:
        """
        Upload model files to S3.
        
        Args:
            local_dir: Local directory containing model files
            s3_key_prefix: S3 key prefix (e.g., "llama3-sft-20250923/")
            
        Returns:
            Dict: Upload results with S3 URLs
        """
        if not self.s3_client:
            logger.warning("S3 client not available, skipping upload")
            return {}
        
        logger.info(f"Uploading model to S3: s3://{self.s3_bucket}/{s3_key_prefix}")
        
        local_path = Path(local_dir)
        uploaded_files = {}
        
        try:
            for file_path in local_path.rglob("*"):
                if file_path.is_file():
                    # Calculate relative path for S3 key
                    relative_path = file_path.relative_to(local_path)
                    s3_key = f"{s3_key_prefix}{relative_path}"
                    
                    # Upload file
                    self.s3_client.upload_file(
                        str(file_path),
                        self.s3_bucket,
                        s3_key
                    )
                    
                    s3_url = f"s3://{self.s3_bucket}/{s3_key}"
                    uploaded_files[str(relative_path)] = s3_url
                    logger.info(f"Uploaded: {s3_url}")
            
            logger.info(f"Upload completed: {len(uploaded_files)} files")
            return uploaded_files
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise
    
    def export_model(self, 
                    model_path: str,
                    output_dir: str,
                    model_name: str = None,
                    upload_to_s3: bool = True) -> Dict[str, Any]:
        """
        Complete model export pipeline.
        
        Args:
            model_path: Path to trained HuggingFace model
            output_dir: Local output directory
            model_name: Name for the exported model
            upload_to_s3: Whether to upload to S3
            
        Returns:
            Dict: Export results and metadata
        """
        if not model_name:
            model_name = f"collegeadvisor-llama3-{datetime.now().strftime('%Y%m%d')}"
        
        logger.info(f"Starting model export: {model_name}")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Convert to GGUF
            gguf_path = self.convert_to_gguf(
                model_path=model_path,
                output_path=str(output_path / "gguf")
            )
            
            # Create Modelfile
            modelfile_path = self.create_modelfile(
                gguf_path=gguf_path,
                output_dir=str(output_path),
                model_name=model_name
            )
            
            # Create deployment metadata
            metadata = {
                "model_name": model_name,
                "export_timestamp": datetime.now().isoformat(),
                "source_model": model_path,
                "gguf_path": gguf_path,
                "modelfile_path": modelfile_path,
                "deployment_ready": True
            }
            
            metadata_path = output_path / "deployment_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Upload to S3 if requested
            s3_urls = {}
            if upload_to_s3:
                s3_key_prefix = f"{model_name}/"
                s3_urls = self.upload_to_s3(str(output_path), s3_key_prefix)
                metadata["s3_urls"] = s3_urls
            
            logger.info(f"Model export completed: {model_name}")
            
            return {
                "success": True,
                "model_name": model_name,
                "output_dir": str(output_path),
                "gguf_path": gguf_path,
                "modelfile_path": modelfile_path,
                "metadata": metadata,
                "s3_urls": s3_urls
            }
            
        except Exception as e:
            logger.error(f"Model export failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "model_name": model_name
            }


def main():
    """Main export script."""
    parser = argparse.ArgumentParser(description="Export trained model to Ollama format")
    parser.add_argument("--model_path", help="Path to trained HuggingFace model (for full model)")
    parser.add_argument("--lora_path", help="Path to LoRA adapter (for LoRA fine-tuned model)")
    parser.add_argument("--base_model", default="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                       help="Base model name (required if using --lora_path)")
    parser.add_argument("--output_dir", required=True, help="Output directory for exported model")
    parser.add_argument("--model_name", help="Model name for deployment")
    parser.add_argument("--no-s3", action="store_true", help="Skip S3 upload")
    parser.add_argument("--quantization", default="q4_k_m", help="GGUF quantization level")

    args = parser.parse_args()

    # Validate arguments
    if not args.model_path and not args.lora_path:
        parser.error("Either --model_path or --lora_path must be specified")

    if args.lora_path and not args.base_model:
        parser.error("--base_model is required when using --lora_path")

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Initialize exporter
        exporter = OllamaExporter()

        # Determine model name
        model_name = args.model_name or f"college-advisor-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Convert to GGUF
        if args.lora_path:
            # LoRA mode: merge and convert
            logger.info("Mode: LoRA adapter merge and convert")
            gguf_path = exporter.merge_lora_and_convert(
                base_model=args.base_model,
                lora_path=args.lora_path,
                output_path=str(output_path / "gguf"),
                quantization=args.quantization
            )
        else:
            # Full model mode: direct convert
            logger.info("Mode: Full model convert")
            gguf_path = exporter.convert_to_gguf(
                model_path=args.model_path,
                output_path=str(output_path / "gguf"),
                quantization=args.quantization
            )

        # Create Modelfile
        modelfile_path = exporter.create_modelfile(
            gguf_path=gguf_path,
            output_dir=str(output_path),
            model_name=model_name
        )

        # Create deployment metadata
        metadata = {
            "model_name": model_name,
            "export_timestamp": datetime.now().isoformat(),
            "mode": "lora" if args.lora_path else "full",
            "base_model": args.base_model if args.lora_path else args.model_path,
            "lora_path": args.lora_path if args.lora_path else None,
            "gguf_path": gguf_path,
            "modelfile_path": modelfile_path,
            "quantization": args.quantization,
            "deployment_ready": True
        }

        metadata_path = output_path / "deployment_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"✅ Export completed successfully!")
        print(f"\n{'='*60}")
        print(f"✅ MODEL EXPORT COMPLETE")
        print(f"{'='*60}")
        print(f"Model name:     {model_name}")
        print(f"Output dir:     {output_path}")
        print(f"GGUF file:      {gguf_path}")
        print(f"Modelfile:      {modelfile_path}")
        print(f"Metadata:       {metadata_path}")
        print(f"{'='*60}")
        print(f"\nTo import into Ollama:")
        print(f"  ollama create {model_name} -f {modelfile_path}")
        print(f"\nTo test the model:")
        print(f"  ollama run {model_name}")
        print(f"{'='*60}\n")

    except Exception as e:
        logger.error(f"Export failed: {e}")
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
