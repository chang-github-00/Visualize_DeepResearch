#!/usr/bin/env python3

import json
import os
from collections import defaultdict, Counter

def calculate_distributions():
    """Calculate distribution for each field in human_labels JSON files, excluding null values."""
    
    labels_dir = "/Users/machang/Documents/research-work/CellMMAgent/Visualize_DeepResearch/human_labels"
    distributions = defaultdict(Counter)
    total_files = 0
    
    # Process all JSON files in the human_labels directory
    for filename in os.listdir(labels_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(labels_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    total_files += 1
                    
                    # Count values for each field, excluding null/empty values
                    for key, value in data.items():
                        if key in ['attemptId', 'geneName', 'timestamp']:
                            continue  # Skip ID fields
                        
                        if value is not None and value != "" and value != "null":
                            distributions[key][value] += 1
            
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error reading {filename}: {e}")
    
    print(f"Analyzed {total_files} files")
    print("=" * 50)
    
    # Print distributions for each field
    for field, counter in distributions.items():
        print(f"\n{field.upper()} Distribution:")
        print("-" * 30)
        total_count = sum(counter.values())
        
        for value, count in counter.most_common():
            percentage = (count / total_count) * 100
            print(f"  {value:<15} : {count:>3} ({percentage:5.1f}%)")
        
        print(f"  Total responses: {total_count}")

if __name__ == "__main__":
    calculate_distributions()