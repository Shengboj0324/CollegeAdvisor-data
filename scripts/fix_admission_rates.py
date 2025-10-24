#!/usr/bin/env python3
"""
Fix admission rate data - multiply by 100 to convert decimal to percentage.

This script fixes the critical data error where all admission rates are off by 100x.
Example: 0.6622 should be displayed as 66.22%, not 0.6622%
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List
import shutil
from datetime import datetime

def backup_file(file_path: Path) -> Path:
    """Create backup of original file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = file_path.with_suffix(f'.backup_{timestamp}{file_path.suffix}')
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def extract_rate_from_text(text: str) -> tuple[float, str]:
    """
    Extract admission rate from text.
    Returns: (rate_value, full_match_text)
    """
    # Pattern: "approximately X%" or "is X%"
    pattern = r'(approximately|is)\s+([\d.]+)%'
    match = re.search(pattern, text)
    if match:
        rate = float(match.group(2))
        return rate, match.group(0)
    return None, None

def fix_admission_rate_in_text(text: str) -> tuple[str, bool]:
    """
    Fix admission rate in text if it's less than 1% (likely wrong).
    Returns: (fixed_text, was_fixed)
    """
    rate, match_text = extract_rate_from_text(text)
    
    if rate is None:
        return text, False
    
    # If rate is less than 1%, it's likely the decimal-to-percentage bug
    if rate < 1.0:
        corrected_rate = rate * 100
        # Replace the old rate with corrected rate
        new_match = match_text.replace(f"{rate}%", f"{corrected_rate:.2f}%")
        fixed_text = text.replace(match_text, new_match)
        return fixed_text, True
    
    return text, False

def fix_alpaca_dataset(file_path: Path) -> Dict[str, Any]:
    """Fix admission rates in Alpaca format dataset."""
    print(f"\n📂 Processing: {file_path}")
    
    # Backup original
    backup_path = backup_file(file_path)
    
    # Load data
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 Total examples: {len(data)}")
    
    # Fix admission rates
    fixed_count = 0
    examples_fixed = []
    
    for i, example in enumerate(data):
        instruction = example.get('instruction', '')
        output = example.get('output', '')
        
        # Check if this is an admission rate question
        if 'admission rate' in instruction.lower():
            fixed_output, was_fixed = fix_admission_rate_in_text(output)
            
            if was_fixed:
                old_rate, _ = extract_rate_from_text(output)
                new_rate, _ = extract_rate_from_text(fixed_output)
                
                examples_fixed.append({
                    'index': i,
                    'instruction': instruction,
                    'old_output': output,
                    'new_output': fixed_output,
                    'old_rate': old_rate,
                    'new_rate': new_rate
                })
                
                example['output'] = fixed_output
                fixed_count += 1
    
    # Save fixed data
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Fixed {fixed_count} admission rates")
    
    # Show examples
    if examples_fixed:
        print(f"\n📋 Sample fixes (showing first 5):")
        for ex in examples_fixed[:5]:
            print(f"\n  Example {ex['index']}:")
            print(f"    Question: {ex['instruction']}")
            print(f"    Old: {ex['old_rate']}% → New: {ex['new_rate']:.2f}%")
    
    return {
        'file': str(file_path),
        'total_examples': len(data),
        'fixed_count': fixed_count,
        'backup': str(backup_path),
        'examples_fixed': examples_fixed
    }

def fix_ollama_dataset(file_path: Path) -> Dict[str, Any]:
    """Fix admission rates in Ollama format dataset."""
    print(f"\n📂 Processing: {file_path}")
    
    # Backup original
    backup_path = backup_file(file_path)
    
    # Load data
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📊 Total lines: {len(lines)}")
    
    # Fix admission rates
    fixed_count = 0
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Check if this is an assistant response with admission rate
        if '### Assistant:' in line and 'admission rate' in line.lower():
            fixed_line, was_fixed = fix_admission_rate_in_text(line)
            
            if was_fixed:
                fixed_count += 1
                old_rate, _ = extract_rate_from_text(line)
                new_rate, _ = extract_rate_from_text(fixed_line)
                print(f"  Line {i}: {old_rate}% → {new_rate:.2f}%")
            
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)
    
    # Save fixed data
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"✅ Fixed {fixed_count} admission rates")
    
    return {
        'file': str(file_path),
        'total_lines': len(lines),
        'fixed_count': fixed_count,
        'backup': str(backup_path)
    }

def verify_fixes(file_path: Path, format_type: str = 'alpaca') -> Dict[str, Any]:
    """Verify that all admission rates are now reasonable (> 1%)."""
    print(f"\n🔍 Verifying fixes in: {file_path}")
    
    suspicious_rates = []
    
    if format_type == 'alpaca':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for i, example in enumerate(data):
            instruction = example.get('instruction', '')
            output = example.get('output', '')
            
            if 'admission rate' in instruction.lower():
                rate, _ = extract_rate_from_text(output)
                if rate and rate < 1.0:
                    suspicious_rates.append({
                        'index': i,
                        'instruction': instruction,
                        'output': output,
                        'rate': rate
                    })
    
    elif format_type == 'ollama':
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            if '### Assistant:' in line and 'admission rate' in line.lower():
                rate, _ = extract_rate_from_text(line)
                if rate and rate < 1.0:
                    suspicious_rates.append({
                        'line': i,
                        'text': line.strip(),
                        'rate': rate
                    })
    
    if suspicious_rates:
        print(f"⚠️  Found {len(suspicious_rates)} suspicious rates (< 1%):")
        for item in suspicious_rates[:5]:
            print(f"  {item}")
        return {'verified': False, 'suspicious_count': len(suspicious_rates), 'suspicious_rates': suspicious_rates}
    else:
        print(f"✅ All admission rates verified (all > 1%)")
        return {'verified': True, 'suspicious_count': 0}

def main():
    """Main execution."""
    print("=" * 80)
    print("🔧 FIXING ADMISSION RATE DATA (100x ERROR)")
    print("=" * 80)
    
    results = {}
    
    # Fix Alpaca format
    alpaca_file = Path('training_data_alpaca.json')
    if alpaca_file.exists():
        results['alpaca'] = fix_alpaca_dataset(alpaca_file)
        results['alpaca_verification'] = verify_fixes(alpaca_file, 'alpaca')
    else:
        print(f"⚠️  File not found: {alpaca_file}")
    
    # Fix Ollama format
    ollama_file = Path('training_data_ollama.txt')
    if ollama_file.exists():
        results['ollama'] = fix_ollama_dataset(ollama_file)
        results['ollama_verification'] = verify_fixes(ollama_file, 'ollama')
    else:
        print(f"⚠️  File not found: {ollama_file}")
    
    # Save report
    report_file = Path('admission_rate_fix_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Report saved: {report_file}")
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ ADMISSION RATE FIX COMPLETE")
    print("=" * 80)
    
    if 'alpaca' in results:
        print(f"\nAlpaca format:")
        print(f"  - Fixed: {results['alpaca']['fixed_count']} examples")
        print(f"  - Verified: {results['alpaca_verification']['verified']}")
        print(f"  - Backup: {results['alpaca']['backup']}")
    
    if 'ollama' in results:
        print(f"\nOllama format:")
        print(f"  - Fixed: {results['ollama']['fixed_count']} lines")
        print(f"  - Verified: {results['ollama_verification']['verified']}")
        print(f"  - Backup: {results['ollama']['backup']}")
    
    # Check if all verified
    all_verified = all(
        results.get(f'{fmt}_verification', {}).get('verified', False)
        for fmt in ['alpaca', 'ollama']
        if fmt in results
    )
    
    if all_verified:
        print("\n🎉 All data verified successfully!")
        return 0
    else:
        print("\n⚠️  Some data still has issues - check report for details")
        return 1

if __name__ == "__main__":
    exit(main())

