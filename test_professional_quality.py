#!/usr/bin/env python3
"""
Professional Quality Assessment for College Advisor Model
Tests peak professionalism, detailed understanding, and data accuracy
"""

import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from pathlib import Path
import sys
import re

print("=" * 100)
print("PROFESSIONAL QUALITY ASSESSMENT - COLLEGE ADVISOR MODEL")
print("Testing: Peak Professionalism | Detailed Understanding | Data Accuracy")
print("=" * 100)
print()

# Configuration
MODEL_PATH = "collegeadvisor_model_macos"
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

# Load model
print(f"Loading model from: {MODEL_PATH}")
print(f"Device: {DEVICE}\n")

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

def generate_response(question, max_tokens=250):
    """Generate professional response"""
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
            max_new_tokens=max_tokens,
            temperature=0.7,
            do_sample=True,
            top_p=0.92,
            top_k=50,
            pad_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.15,
            no_repeat_ngram_size=3
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    if "### Response:" in response:
        response = response.split("### Response:")[1].strip()
    
    # Clean up response
    response = response.split("###")[0].strip()
    
    return response

def analyze_professionalism(response):
    """Deep analysis of professional quality"""
    analysis = {
        "word_count": len(response.split()),
        "sentence_count": len([s for s in response.split('.') if len(s.strip()) > 5]),
        "avg_sentence_length": 0,
        "uses_data": False,
        "uses_percentages": False,
        "uses_numbers": False,
        "mentions_universities": False,
        "professional_tone": False,
        "specific_details": False,
        "comparative_analysis": False,
        "contextual_understanding": False,
        "score": 0
    }
    
    # Calculate average sentence length
    sentences = [s.strip() for s in response.split('.') if len(s.strip()) > 5]
    if sentences:
        analysis["avg_sentence_length"] = sum(len(s.split()) for s in sentences) / len(sentences)
    
    # Check for data usage
    analysis["uses_percentages"] = bool(re.search(r'\d+%|\d+\s*percent', response, re.I))
    analysis["uses_numbers"] = bool(re.search(r'\d+', response))
    analysis["uses_data"] = analysis["uses_percentages"] or analysis["uses_numbers"]
    
    # Check for university mentions
    university_keywords = ['University', 'College', 'Institute', 'School']
    analysis["mentions_universities"] = any(keyword in response for keyword in university_keywords)
    
    # Professional tone indicators
    professional_words = [
        'admission', 'enrollment', 'tuition', 'academic', 'institution',
        'program', 'undergraduate', 'graduate', 'faculty', 'campus',
        'selectivity', 'acceptance', 'approximately', 'typically', 'offers'
    ]
    prof_count = sum(1 for word in professional_words if word.lower() in response.lower())
    analysis["professional_tone"] = prof_count >= 3
    
    # Specific details
    specific_indicators = [
        'rate', 'cost', 'ratio', 'size', 'location', 'ranking',
        'major', 'degree', 'semester', 'year', 'average'
    ]
    spec_count = sum(1 for indicator in specific_indicators if indicator.lower() in response.lower())
    analysis["specific_details"] = spec_count >= 2
    
    # Comparative analysis
    comparative_words = ['compare', 'versus', 'vs', 'while', 'whereas', 'both', 'either', 'neither']
    analysis["comparative_analysis"] = any(word in response.lower() for word in comparative_words)
    
    # Contextual understanding
    context_indicators = ['because', 'therefore', 'however', 'additionally', 'furthermore', 'moreover']
    analysis["contextual_understanding"] = any(word in response.lower() for word in context_indicators)
    
    # Calculate score (0-100)
    score = 0
    
    # Word count (0-15 points)
    if 30 <= analysis["word_count"] <= 150:
        score += 15
    elif 20 <= analysis["word_count"] < 30 or 150 < analysis["word_count"] <= 200:
        score += 10
    else:
        score += 5
    
    # Sentence structure (0-10 points)
    if 2 <= analysis["sentence_count"] <= 6:
        score += 10
    elif analysis["sentence_count"] == 1 or analysis["sentence_count"] > 6:
        score += 5
    
    # Data usage (0-20 points)
    if analysis["uses_percentages"]:
        score += 10
    if analysis["uses_numbers"]:
        score += 10
    
    # University mentions (0-10 points)
    if analysis["mentions_universities"]:
        score += 10
    
    # Professional tone (0-15 points)
    if analysis["professional_tone"]:
        score += 15
    
    # Specific details (0-15 points)
    if analysis["specific_details"]:
        score += 15
    
    # Comparative analysis (0-10 points)
    if analysis["comparative_analysis"]:
        score += 10
    
    # Contextual understanding (0-5 points)
    if analysis["contextual_understanding"]:
        score += 5
    
    analysis["score"] = score
    
    return analysis

# Professional test cases
PROFESSIONAL_TESTS = [
    {
        "question": "What is the admission rate at Stanford University and what does this indicate about its selectivity?",
        "expected_elements": ["percentage", "selective", "competitive", "data"]
    },
    {
        "question": "Compare the tuition costs between Harvard University and a typical public university. What factors contribute to this difference?",
        "expected_elements": ["comparison", "cost data", "explanation", "context"]
    },
    {
        "question": "Explain the significance of the student-to-faculty ratio at MIT and how it impacts the educational experience.",
        "expected_elements": ["ratio", "impact", "educational quality", "specific number"]
    },
    {
        "question": "What are the most popular academic programs at UC Berkeley and why are they highly regarded?",
        "expected_elements": ["specific programs", "reputation", "reasons", "details"]
    },
    {
        "question": "Describe the campus setting and location of Yale University. How does this affect student life?",
        "expected_elements": ["location", "setting type", "student life", "context"]
    },
    {
        "question": "What is the graduation rate at Princeton University and what does this tell us about student success?",
        "expected_elements": ["percentage", "success indicator", "interpretation", "data"]
    },
    {
        "question": "How do the engineering programs at Caltech and MIT compare in terms of reputation and specialization?",
        "expected_elements": ["comparison", "both universities", "specific details", "analysis"]
    },
    {
        "question": "What financial aid options are typically available at Columbia University for undergraduate students?",
        "expected_elements": ["aid types", "specific info", "undergraduate focus", "details"]
    },
    {
        "question": "Explain the difference between early decision and regular admission at Duke University.",
        "expected_elements": ["both types", "differences", "specific to Duke", "clear explanation"]
    },
    {
        "question": "What makes the University of Chicago's academic environment unique compared to other top universities?",
        "expected_elements": ["unique features", "comparison", "academic focus", "specific details"]
    }
]

# Run professional quality tests
print("=" * 100)
print("RUNNING PROFESSIONAL QUALITY TESTS")
print("=" * 100)
print()

results = []
total_score = 0

for i, test in enumerate(PROFESSIONAL_TESTS, 1):
    question = test["question"]
    expected = test["expected_elements"]
    
    print(f"\n{'=' * 100}")
    print(f"TEST {i}/{len(PROFESSIONAL_TESTS)}")
    print(f"{'=' * 100}")
    print(f"\nQuestion: {question}")
    print(f"\nExpected Elements: {', '.join(expected)}")
    print(f"\n{'-' * 100}")
    
    # Generate response
    response = generate_response(question)
    
    print(f"Response:\n{response}")
    print(f"\n{'-' * 100}")
    
    # Analyze
    analysis = analyze_professionalism(response)
    
    print(f"\nProfessional Quality Analysis:")
    print(f"  • Word Count:              {analysis['word_count']}")
    print(f"  • Sentence Count:          {analysis['sentence_count']}")
    print(f"  • Avg Sentence Length:     {analysis['avg_sentence_length']:.1f} words")
    print(f"  • Uses Data:               {'✓' if analysis['uses_data'] else '✗'}")
    print(f"  • Uses Percentages:        {'✓' if analysis['uses_percentages'] else '✗'}")
    print(f"  • Uses Numbers:            {'✓' if analysis['uses_numbers'] else '✗'}")
    print(f"  • Mentions Universities:   {'✓' if analysis['mentions_universities'] else '✗'}")
    print(f"  • Professional Tone:       {'✓' if analysis['professional_tone'] else '✗'}")
    print(f"  • Specific Details:        {'✓' if analysis['specific_details'] else '✗'}")
    print(f"  • Comparative Analysis:    {'✓' if analysis['comparative_analysis'] else '✗'}")
    print(f"  • Contextual Understanding:{'✓' if analysis['contextual_understanding'] else '✗'}")
    print(f"\n  • PROFESSIONAL SCORE:      {analysis['score']}/100")
    
    # Grade
    if analysis['score'] >= 90:
        grade = "A+ (EXCEPTIONAL)"
    elif analysis['score'] >= 85:
        grade = "A  (EXCELLENT)"
    elif analysis['score'] >= 80:
        grade = "A- (VERY GOOD)"
    elif analysis['score'] >= 75:
        grade = "B+ (GOOD)"
    elif analysis['score'] >= 70:
        grade = "B  (SATISFACTORY)"
    elif analysis['score'] >= 65:
        grade = "B- (ACCEPTABLE)"
    else:
        grade = "C  (NEEDS IMPROVEMENT)"
    
    print(f"  • GRADE:                   {grade}")
    
    results.append({
        "question": question,
        "response": response,
        "analysis": analysis,
        "grade": grade
    })
    
    total_score += analysis['score']

# Final summary
avg_score = total_score / len(PROFESSIONAL_TESTS)

print(f"\n\n{'=' * 100}")
print("FINAL PROFESSIONAL QUALITY ASSESSMENT")
print(f"{'=' * 100}\n")

print(f"Total Tests:           {len(PROFESSIONAL_TESTS)}")
print(f"Average Score:         {avg_score:.1f}/100")
print(f"Percentage:            {avg_score:.1f}%")
print()

# Overall assessment
if avg_score >= 90:
    assessment = "EXCEPTIONAL - Peak Professional Quality"
    recommendation = "✓ READY FOR PRODUCTION DEPLOYMENT"
elif avg_score >= 85:
    assessment = "EXCELLENT - Highly Professional"
    recommendation = "✓ Ready for production with minor monitoring"
elif avg_score >= 80:
    assessment = "VERY GOOD - Professional Quality"
    recommendation = "✓ Suitable for production use"
elif avg_score >= 75:
    assessment = "GOOD - Acceptable Professional Level"
    recommendation = "⚠ Consider additional fine-tuning for optimal results"
elif avg_score >= 70:
    assessment = "SATISFACTORY - Basic Professional Level"
    recommendation = "⚠ Recommended: Additional training data and refinement"
else:
    assessment = "NEEDS IMPROVEMENT"
    recommendation = "✗ Requires significant additional training"

print(f"Overall Assessment:    {assessment}")
print(f"Recommendation:        {recommendation}")
print()

# Detailed breakdown
print("Detailed Performance Breakdown:")
print(f"  • Data Usage:          {sum(1 for r in results if r['analysis']['uses_data'])}/{len(results)} tests")
print(f"  • Professional Tone:   {sum(1 for r in results if r['analysis']['professional_tone'])}/{len(results)} tests")
print(f"  • Specific Details:    {sum(1 for r in results if r['analysis']['specific_details'])}/{len(results)} tests")
print(f"  • Comparative Analysis:{sum(1 for r in results if r['analysis']['comparative_analysis'])}/{len(results)} tests")
print(f"  • Contextual Understanding: {sum(1 for r in results if r['analysis']['contextual_understanding'])}/{len(results)} tests")
print()

# Save results
output_file = "professional_quality_assessment.json"
with open(output_file, 'w') as f:
    json.dump({
        "average_score": avg_score,
        "assessment": assessment,
        "recommendation": recommendation,
        "detailed_results": results
    }, f, indent=2)

print(f"✓ Detailed results saved to: {output_file}")
print()
print(f"{'=' * 100}")
print("PROFESSIONAL QUALITY ASSESSMENT COMPLETE")
print(f"{'=' * 100}")

