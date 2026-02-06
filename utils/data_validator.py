import json
import os

# Standard 6 persons in Spanish conjugation
PERSONS = ['yo', 'tu', 'el/ella/usted', 'nosotros', 'vosotros', 'ellos/ellas/ustedes']

def load_and_validate_data(file_path):
    """
    Load JSON data and validate consistency.
    Ensures all verbs have all tenses, and all tenses have all 6 persons.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    quiz_data = data.get('conjugations_quiz', {})
    
    if not quiz_data:
        print("Warning: No conjugations_quiz data found")
        return data
    
    # Collect all tenses from all verbs
    all_tenses = set()
    for verb_data in quiz_data.values():
        all_tenses.update(verb_data.keys())
    
    # Validate and fix consistency
    issues_found = []
    fixed_count = 0
    
    for verb_name, verb_data in quiz_data.items():
        # Ensure all tenses exist for this verb
        for tense in all_tenses:
            if tense not in verb_data:
                verb_data[tense] = {}
                issues_found.append(f"Missing tense '{tense}' for verb '{verb_name}'")
            
            # Ensure all persons exist for this tense
            for person in PERSONS:
                if person not in verb_data[tense]:
                    verb_data[tense][person] = "[MISSING]"
                    issues_found.append(f"Missing person '{person}' for verb '{verb_name}', tense '{tense}'")
                    fixed_count += 1
    
    # Report issues
    if issues_found:
        print(f"\nData validation found {len(issues_found)} issues:")
        for issue in issues_found[:10]:  # Show first 10
            print(f"  - {issue}")
        if len(issues_found) > 10:
            print(f"  ... and {len(issues_found) - 10} more issues")
        print(f"\nAuto-filled {fixed_count} missing conjugations with '[MISSING]' placeholder")
    else:
        print("Data validation passed: All verbs have all tenses with all 6 persons")
    
    # Save fixed data back if there were fixes
    if fixed_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Updated data file: {file_path}")
    
    return data
