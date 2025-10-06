#!/usr/bin/env python3
"""
Interactive Demo - Fine-Tuned College Advisor Model
Quick demonstration of model capabilities
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from pathlib import Path
import sys

print("=" * 100)
print("COLLEGE ADVISOR MODEL - INTERACTIVE DEMO")
print("=" * 100)
print()

# Configuration
MODEL_PATH = "collegeadvisor_model_macos"
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

# Check model
if not Path(MODEL_PATH).exists():
    print(f"❌ ERROR: Model not found at {MODEL_PATH}")
    sys.exit(1)

print(f"Loading model from: {MODEL_PATH}")
print(f"Device: {DEVICE}\n")

# Load model
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.float16 if DEVICE != "cpu" else torch.float32,
        low_cpu_mem_usage=True
    )
    if DEVICE == "mps":
        model = model.to(DEVICE)
    print("✓ Model loaded successfully\n")
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

def ask_question(question):
    """Ask the model a question"""
    prompt = f"""### Instruction:
{question}

### Input:


### Response:
"""
    
    inputs = tokenizer(prompt, return_tensors="pt")
    if DEVICE != "cpu":
        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            top_k=50,
            pad_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.1
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    if "### Response:" in response:
        response = response.split("### Response:")[1].strip()
    
    # Clean up
    response = response.split("###")[0].strip()
    
    return response

# Demo questions
DEMO_QUESTIONS = [
    "What is the admission rate at Stanford University?",
    "How much does it cost to attend Harvard University?",
    "What are the most popular majors at MIT?",
    "Compare UC Berkeley and UCLA",
    "What is the student-to-faculty ratio at Princeton?",
]

print("=" * 100)
print("DEMONSTRATION - Sample Questions")
print("=" * 100)
print()

for i, question in enumerate(DEMO_QUESTIONS, 1):
    print(f"\n[Question {i}]")
    print(f"Q: {question}")
    print(f"{'-' * 100}")
    
    response = ask_question(question)
    
    print(f"A: {response}")
    print(f"{'=' * 100}")

print("\n\n" + "=" * 100)
print("INTERACTIVE MODE")
print("=" * 100)
print("\nYou can now ask your own questions!")
print("Type 'quit' or 'exit' to end the session.\n")

while True:
    try:
        question = input("\nYour Question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("\nThank you for using College Advisor Model!")
            break
        
        if not question:
            continue
        
        print(f"\n{'-' * 100}")
        response = ask_question(question)
        print(f"Answer: {response}")
        print(f"{'-' * 100}")
        
    except KeyboardInterrupt:
        print("\n\nSession ended.")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}")
        continue

print("\n" + "=" * 100)
print("DEMO COMPLETE")
print("=" * 100)

