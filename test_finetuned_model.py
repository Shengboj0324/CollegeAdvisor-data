#!/usr/bin/env python3
"""
Comprehensive Testing Suite for Fine-Tuned College Advisor Model
Tests professional understanding, accuracy, and detailed knowledge
"""

import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import sys
from pathlib import Path

print("=" * 100)
print("COMPREHENSIVE COLLEGE ADVISOR MODEL EVALUATION")
print("=" * 100)
print()

# Configuration
MODEL_PATH = "collegeadvisor_model_macos"
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

# Check if model exists
if not Path(MODEL_PATH).exists():
    print(f"❌ ERROR: Model not found at {MODEL_PATH}")
    print("Please ensure fine-tuning completed successfully")
    sys.exit(1)

print(f"Loading model from: {MODEL_PATH}")
print(f"Device: {DEVICE}")
print()

# Load model and tokenizer
print("Step 1: Loading tokenizer and model...")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.float16 if DEVICE != "cpu" else torch.float32,
        low_cpu_mem_usage=True
    )
    
    if DEVICE == "mps":
        model = model.to(DEVICE)
    
    print("✓ Model loaded successfully")
    print(f"✓ Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"✓ Trainable parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")
except Exception as e:
    print(f"❌ ERROR loading model: {e}")
    sys.exit(1)

print()

# Test cases covering different aspects of college advising
TEST_CASES = [
    {
        "category": "Admission Rates & Selectivity",
        "questions": [
            "What is the admission rate at Stanford University?",
            "How selective is Harvard University?",
            "Compare the admission rates of MIT and Caltech",
            "Which Ivy League school has the highest acceptance rate?",
        ]
    },
    {
        "category": "Tuition & Financial Information",
        "questions": [
            "What is the tuition cost at Yale University?",
            "How much does it cost to attend Princeton University?",
            "Compare the tuition costs of public vs private universities",
            "What is the average student debt at Columbia University?",
        ]
    },
    {
        "category": "Academic Programs & Majors",
        "questions": [
            "What are the most popular majors at UC Berkeley?",
            "Does Cornell University offer engineering programs?",
            "What programs is Carnegie Mellon known for?",
            "Which universities have the best computer science programs?",
        ]
    },
    {
        "category": "Student Demographics & Size",
        "questions": [
            "How many students attend University of Michigan?",
            "What is the student-to-faculty ratio at Brown University?",
            "What percentage of students live on campus at Duke University?",
            "How diverse is the student body at UCLA?",
        ]
    },
    {
        "category": "Location & Campus",
        "questions": [
            "Where is Dartmouth College located?",
            "What is the campus setting of Northwestern University?",
            "Which universities are in the Boston area?",
            "Is University of Pennsylvania in an urban or rural setting?",
        ]
    },
    {
        "category": "Graduation & Outcomes",
        "questions": [
            "What is the graduation rate at Johns Hopkins University?",
            "What percentage of students complete their degree at Vanderbilt?",
            "What are the employment outcomes for graduates of Rice University?",
            "How long does it take to graduate from University of Chicago?",
        ]
    },
    {
        "category": "Comparative Analysis",
        "questions": [
            "Compare Stanford and MIT in terms of selectivity and programs",
            "What are the differences between Harvard and Yale?",
            "How does UC Berkeley compare to UCLA?",
            "Which is better for engineering: Caltech or MIT?",
        ]
    },
    {
        "category": "Specific Data Points",
        "questions": [
            "What is the SAT score range for admitted students at Princeton?",
            "What is the average GPA of students at Georgetown University?",
            "How many applications does Harvard receive each year?",
            "What is the endowment size of Yale University?",
        ]
    }
]

def generate_response(question, max_length=200, temperature=0.7):
    """Generate response from the model"""
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
            max_new_tokens=max_length,
            temperature=temperature,
            do_sample=True,
            top_p=0.9,
            top_k=50,
            pad_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.1
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract only the response part
    if "### Response:" in response:
        response = response.split("### Response:")[1].strip()
    
    return response

# Evaluation criteria
def evaluate_response(response, question):
    """Evaluate response quality"""
    scores = {
        "length": 0,
        "specificity": 0,
        "professionalism": 0,
        "data_mention": 0,
        "coherence": 0
    }
    
    # Length check (should be substantial but not too long)
    word_count = len(response.split())
    if 20 <= word_count <= 150:
        scores["length"] = 10
    elif 10 <= word_count < 20 or 150 < word_count <= 200:
        scores["length"] = 7
    else:
        scores["length"] = 5
    
    # Specificity (mentions numbers, percentages, specific data)
    specific_indicators = ['%', 'percent', 'rate', 'approximately', 'around', '$', 'students', 'ratio']
    specificity_count = sum(1 for indicator in specific_indicators if indicator.lower() in response.lower())
    scores["specificity"] = min(10, specificity_count * 3)
    
    # Professionalism (avoids casual language, uses proper terms)
    professional_terms = ['university', 'college', 'institution', 'program', 'academic', 'admission', 'enrollment']
    casual_terms = ['like', 'stuff', 'things', 'kinda', 'sorta', 'yeah', 'nah']
    
    prof_count = sum(1 for term in professional_terms if term.lower() in response.lower())
    casual_count = sum(1 for term in casual_terms if term.lower() in response.lower())
    
    scores["professionalism"] = max(0, min(10, prof_count * 2 - casual_count * 3))
    
    # Data mention (references specific universities, numbers, facts)
    has_numbers = any(char.isdigit() for char in response)
    has_university_name = any(word[0].isupper() for word in response.split())
    
    if has_numbers and has_university_name:
        scores["data_mention"] = 10
    elif has_numbers or has_university_name:
        scores["data_mention"] = 6
    else:
        scores["data_mention"] = 3
    
    # Coherence (complete sentences, logical flow)
    sentences = response.split('.')
    complete_sentences = [s for s in sentences if len(s.strip()) > 10]
    
    if len(complete_sentences) >= 2:
        scores["coherence"] = 10
    elif len(complete_sentences) == 1:
        scores["coherence"] = 7
    else:
        scores["coherence"] = 4
    
    total_score = sum(scores.values())
    return scores, total_score

# Run comprehensive tests
print("=" * 100)
print("RUNNING COMPREHENSIVE EVALUATION")
print("=" * 100)
print()

all_results = []
category_scores = {}

for test_category in TEST_CASES:
    category = test_category["category"]
    questions = test_category["questions"]
    
    print(f"\n{'=' * 100}")
    print(f"CATEGORY: {category}")
    print(f"{'=' * 100}\n")
    
    category_total = 0
    category_count = 0
    
    for i, question in enumerate(questions, 1):
        print(f"\n[Question {i}/{len(questions)}]")
        print(f"Q: {question}")
        print(f"{'-' * 100}")
        
        # Generate response
        response = generate_response(question)
        
        # Evaluate
        scores, total = evaluate_response(response, question)
        
        print(f"A: {response}")
        print(f"{'-' * 100}")
        print(f"Evaluation Scores:")
        print(f"  • Length:          {scores['length']}/10")
        print(f"  • Specificity:     {scores['specificity']}/10")
        print(f"  • Professionalism: {scores['professionalism']}/10")
        print(f"  • Data Mention:    {scores['data_mention']}/10")
        print(f"  • Coherence:       {scores['coherence']}/10")
        print(f"  • TOTAL:           {total}/50")
        
        # Grade
        if total >= 45:
            grade = "A+ (Excellent)"
        elif total >= 40:
            grade = "A  (Very Good)"
        elif total >= 35:
            grade = "B+ (Good)"
        elif total >= 30:
            grade = "B  (Satisfactory)"
        elif total >= 25:
            grade = "C+ (Fair)"
        else:
            grade = "C  (Needs Improvement)"
        
        print(f"  • GRADE:           {grade}")
        
        all_results.append({
            "category": category,
            "question": question,
            "response": response,
            "scores": scores,
            "total": total,
            "grade": grade
        })
        
        category_total += total
        category_count += 1
    
    category_avg = category_total / category_count
    category_scores[category] = category_avg
    
    print(f"\n{'-' * 100}")
    print(f"Category Average: {category_avg:.1f}/50")
    print(f"{'=' * 100}")

# Final Summary
print(f"\n\n{'=' * 100}")
print("FINAL EVALUATION SUMMARY")
print(f"{'=' * 100}\n")

overall_avg = sum(r["total"] for r in all_results) / len(all_results)

print(f"Total Questions Tested: {len(all_results)}")
print(f"Overall Average Score:  {overall_avg:.1f}/50 ({overall_avg*2:.1f}%)")
print()

print("Category Performance:")
for category, avg_score in category_scores.items():
    percentage = (avg_score / 50) * 100
    print(f"  • {category:40s} {avg_score:5.1f}/50 ({percentage:5.1f}%)")

print()

# Overall grade
if overall_avg >= 45:
    final_grade = "A+ (EXCELLENT - Production Ready)"
elif overall_avg >= 40:
    final_grade = "A  (VERY GOOD - Highly Professional)"
elif overall_avg >= 35:
    final_grade = "B+ (GOOD - Professional Quality)"
elif overall_avg >= 30:
    final_grade = "B  (SATISFACTORY - Acceptable)"
elif overall_avg >= 25:
    final_grade = "C+ (FAIR - Needs Refinement)"
else:
    final_grade = "C  (NEEDS IMPROVEMENT)"

print(f"FINAL GRADE: {final_grade}")
print()

# Save detailed results
results_file = "model_evaluation_results.json"
with open(results_file, 'w') as f:
    json.dump({
        "overall_average": overall_avg,
        "final_grade": final_grade,
        "category_scores": category_scores,
        "detailed_results": all_results
    }, f, indent=2)

print(f"✓ Detailed results saved to: {results_file}")
print()
print(f"{'=' * 100}")
print("EVALUATION COMPLETE")
print(f"{'=' * 100}")

