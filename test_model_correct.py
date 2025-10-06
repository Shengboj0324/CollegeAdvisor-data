#!/usr/bin/env python3
"""
CORRECT Model Testing - Loads base model + LoRA adapters
Professional Quality Assessment
"""

import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from pathlib import Path
import sys

print("=" * 100)
print("COLLEGE ADVISOR MODEL - PROFESSIONAL QUALITY TEST")
print("=" * 100)
print()

# Configuration
BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
ADAPTER_PATH = "collegeadvisor_model_macos"
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

# Check adapter exists
if not Path(ADAPTER_PATH).exists():
    print(f"❌ ERROR: Adapter not found at {ADAPTER_PATH}")
    sys.exit(1)

print(f"Base Model:    {BASE_MODEL}")
print(f"Adapter Path:  {ADAPTER_PATH}")
print(f"Device:        {DEVICE}\n")

# Load base model
print("Step 1: Loading base model...")
try:
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token
    
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16 if DEVICE != "cpu" else torch.float32,
        low_cpu_mem_usage=True
    )
    print("✓ Base model loaded")
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# Load LoRA adapters
print("\nStep 2: Loading LoRA adapters...")
try:
    model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
    print("✓ LoRA adapters loaded")
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# Move to device
if DEVICE == "mps":
    model = model.to(DEVICE)

print(f"\n✓ Model ready on {DEVICE}\n")

def generate_response(question, max_tokens=200):
    """Generate response from fine-tuned model"""
    prompt = f"""### Instruction:
{question}

### Input:


### Response:
"""
    
    inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=512)
    if DEVICE != "cpu":
        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            top_k=50,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.1,
            no_repeat_ngram_size=3
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract response part
    if "### Response:" in response:
        response = response.split("### Response:")[1].strip()
    
    # Clean up
    if "###" in response:
        response = response.split("###")[0].strip()
    
    return response

# Professional test questions
TEST_QUESTIONS = [
    {
        "category": "Admission & Selectivity",
        "question": "What is the admission rate at Stanford University?",
    },
    {
        "category": "Tuition & Costs",
        "question": "How much does it cost to attend Harvard University?",
    },
    {
        "category": "Academic Programs",
        "question": "What are the most popular majors at MIT?",
    },
    {
        "category": "Student Demographics",
        "question": "How many students attend UC Berkeley?",
    },
    {
        "category": "Location & Campus",
        "question": "Where is Yale University located?",
    },
    {
        "category": "Graduation Rates",
        "question": "What is the graduation rate at Princeton University?",
    },
    {
        "category": "Comparative Analysis",
        "question": "Compare Stanford and MIT in terms of engineering programs",
    },
    {
        "category": "Student-Faculty Ratio",
        "question": "What is the student-to-faculty ratio at Caltech?",
    },
    {
        "category": "Campus Setting",
        "question": "What is the campus setting of Columbia University?",
    },
    {
        "category": "Specific Data",
        "question": "What percentage of students receive financial aid at Duke University?",
    }
]

print("=" * 100)
print("RUNNING PROFESSIONAL QUALITY TESTS")
print("=" * 100)
print()

results = []

for i, test in enumerate(TEST_QUESTIONS, 1):
    category = test["category"]
    question = test["question"]
    
    print(f"\n[Test {i}/{len(TEST_QUESTIONS)}] {category}")
    print(f"Q: {question}")
    print(f"{'-' * 100}")
    
    # Generate response
    response = generate_response(question)
    
    print(f"A: {response}")
    
    # Simple quality check
    word_count = len(response.split())
    has_data = any(char.isdigit() for char in response)
    has_university = any(word[0].isupper() for word in response.split() if len(word) > 1)
    
    quality_score = 0
    if 10 <= word_count <= 150:
        quality_score += 25
    if has_data:
        quality_score += 25
    if has_university:
        quality_score += 25
    if word_count >= 20:
        quality_score += 25
    
    print(f"\nQuality Metrics:")
    print(f"  • Word Count:        {word_count}")
    print(f"  • Contains Data:     {'✓' if has_data else '✗'}")
    print(f"  • Mentions University: {'✓' if has_university else '✗'}")
    print(f"  • Quality Score:     {quality_score}/100")
    
    if quality_score >= 75:
        grade = "EXCELLENT"
    elif quality_score >= 50:
        grade = "GOOD"
    elif quality_score >= 25:
        grade = "FAIR"
    else:
        grade = "POOR"
    
    print(f"  • Grade:             {grade}")
    print(f"{'=' * 100}")
    
    results.append({
        "category": category,
        "question": question,
        "response": response,
        "word_count": word_count,
        "has_data": has_data,
        "has_university": has_university,
        "quality_score": quality_score,
        "grade": grade
    })

# Summary
print(f"\n\n{'=' * 100}")
print("FINAL ASSESSMENT SUMMARY")
print(f"{'=' * 100}\n")

avg_score = sum(r["quality_score"] for r in results) / len(results)
avg_words = sum(r["word_count"] for r in results) / len(results)
data_count = sum(1 for r in results if r["has_data"])
univ_count = sum(1 for r in results if r["has_university"])

print(f"Total Tests:              {len(results)}")
print(f"Average Quality Score:    {avg_score:.1f}/100")
print(f"Average Word Count:       {avg_words:.1f}")
print(f"Tests with Data:          {data_count}/{len(results)}")
print(f"Tests with Universities:  {univ_count}/{len(results)}")
print()

if avg_score >= 75:
    assessment = "EXCELLENT - Professional Quality"
    recommendation = "✓ Ready for production use"
elif avg_score >= 50:
    assessment = "GOOD - Acceptable Quality"
    recommendation = "✓ Suitable for use with monitoring"
elif avg_score >= 25:
    assessment = "FAIR - Basic Quality"
    recommendation = "⚠ Needs improvement"
else:
    assessment = "POOR - Insufficient Quality"
    recommendation = "✗ Requires retraining"

print(f"Overall Assessment:       {assessment}")
print(f"Recommendation:           {recommendation}")
print()

# Save results
output_file = "model_test_results.json"
with open(output_file, 'w') as f:
    json.dump({
        "average_score": avg_score,
        "average_words": avg_words,
        "assessment": assessment,
        "recommendation": recommendation,
        "detailed_results": results
    }, f, indent=2)

print(f"✓ Results saved to: {output_file}")
print()
print(f"{'=' * 100}")
print("TESTING COMPLETE")
print(f"{'=' * 100}")

