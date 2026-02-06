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

# Expected por and para categories
POR_CATEGORIES = ['motivation_reason', 'duration', 'cost_price', 'location_movement', 
                  'means_of_travel', 'means_of_communication', 'passive_voice_action']
PARA_CATEGORIES = ['destination', 'goal', 'recipients', 'deadlines', 
                   'expression_of_opinion', 'disparate_idea']

def load_and_validate_por_para_data(file_path):
    """
    Load por/para JSON data and validate consistency.
    Ensures all categories exist and have at least 10 sentences with placeholders.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    por_data = data.get('por', {})
    para_data = data.get('para', {})
    
    if not por_data or not para_data:
        print("Warning: Missing 'por' or 'para' keys in data")
        return data
    
    issues_found = []
    fixed_count = 0
    
    # Validate por categories
    for category in POR_CATEGORIES:
        if category not in por_data:
            por_data[category] = []
            issues_found.append(f"Missing por category '{category}'")
        else:
            sentences = por_data[category]
            if len(sentences) < 10:
                issues_found.append(f"Por category '{category}' has only {len(sentences)} sentences (minimum 10)")
            
            # Check for placeholder
            for i, sentence in enumerate(sentences):
                if '_____' not in sentence:
                    issues_found.append(f"Por category '{category}', sentence {i+1} missing '_____' placeholder")
                if not sentence.strip():
                    issues_found.append(f"Por category '{category}', sentence {i+1} is empty")
    
    # Validate para categories
    for category in PARA_CATEGORIES:
        if category not in para_data:
            para_data[category] = []
            issues_found.append(f"Missing para category '{category}'")
        else:
            sentences = para_data[category]
            if len(sentences) < 10:
                issues_found.append(f"Para category '{category}' has only {len(sentences)} sentences (minimum 10)")
            
            # Check for placeholder
            for i, sentence in enumerate(sentences):
                if '_____' not in sentence:
                    issues_found.append(f"Para category '{category}', sentence {i+1} missing '_____' placeholder")
                if not sentence.strip():
                    issues_found.append(f"Para category '{category}', sentence {i+1} is empty")
    
    # Report issues
    if issues_found:
        print(f"\nPor/Para data validation found {len(issues_found)} issues:")
        for issue in issues_found[:15]:  # Show first 15
            print(f"  - {issue}")
        if len(issues_found) > 15:
            print(f"  ... and {len(issues_found) - 15} more issues")
    else:
        print("Por/Para data validation passed: All categories exist with at least 10 sentences containing '_____' placeholder")
    
    # Save fixed data back if there were fixes
    if fixed_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Updated data file: {file_path}")
    
    return data

def load_and_validate_vocabulary_data(file_path):
    """
    Load vocabulary JSON data and validate consistency.
    Ensures all vocab sets exist, each entry has spanish, german, and english keys,
    and there are no duplicate Spanish words within a set.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    vocab_sets = data.get('vocab_sets', {})
    
    if not vocab_sets:
        print("Warning: No vocab_sets found in data")
        return data
    
    issues_found = []
    fixed_count = 0
    
    # Validate each vocab set
    for set_name, vocab_list in vocab_sets.items():
        if not isinstance(vocab_list, list):
            issues_found.append(f"Vocab set '{set_name}' is not a list")
            continue
        
        if len(vocab_list) < 10:
            issues_found.append(f"Vocab set '{set_name}' has only {len(vocab_list)} entries (minimum 10)")
        
        # Track Spanish words to check for duplicates
        spanish_words = set()
        
        for i, entry in enumerate(vocab_list):
            if not isinstance(entry, dict):
                issues_found.append(f"Vocab set '{set_name}', entry {i+1} is not a dictionary")
                continue
            
            # Check for required keys
            required_keys = ['spanish', 'german', 'english']
            for key in required_keys:
                if key not in entry:
                    issues_found.append(f"Vocab set '{set_name}', entry {i+1} missing '{key}' key")
                elif not entry[key] or not str(entry[key]).strip():
                    issues_found.append(f"Vocab set '{set_name}', entry {i+1} has empty '{key}' value")
            
            # Check for duplicate Spanish words
            if 'spanish' in entry:
                spanish_word = entry['spanish'].strip().lower()
                if spanish_word in spanish_words:
                    issues_found.append(f"Vocab set '{set_name}', duplicate Spanish word: '{entry['spanish']}'")
                else:
                    spanish_words.add(spanish_word)
    
    # Report issues
    if issues_found:
        print(f"\nVocabulary data validation found {len(issues_found)} issues:")
        for issue in issues_found[:15]:  # Show first 15
            print(f"  - {issue}")
        if len(issues_found) > 15:
            print(f"  ... and {len(issues_found) - 15} more issues")
    else:
        print("Vocabulary data validation passed: All vocab sets exist with valid entries containing spanish, german, and english translations")
    
    # Save fixed data back if there were fixes
    if fixed_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Updated data file: {file_path}")
    
    return data
