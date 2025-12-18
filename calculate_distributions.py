#!/usr/bin/env python3

import json
import os
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import numpy as np

def map_labels_to_scores():
    """Map categorical labels to 1-5 numerical scores."""
    
    evidence_mapping = {
        'excellent': 5,
        'good': 4,
        'fair': 3,
        'poor': 2,
        "na": 1
    }
    
    errors_mapping = {
        'none': 5,
        'minor': 3,
        'major': 2,
    }
    
    singlecell_mapping = {
        'excellent': 5,
        'good': 4,
        'adequate': 3,
        'poor': 2,
        'very-poor': 1
    }
    
    novelty_mapping = {
        'breakthrough': 5,
        'highly-novel': 4,
        'moderately-novel': 3,
        'incremental': 2,
        'well-known': 1
    }
    
    return {
        'evidence': evidence_mapping,
        'errors': errors_mapping,
        'singlecell': singlecell_mapping,
        'novelty': novelty_mapping
    }

def calculate_distributions():
    """Calculate distribution for each field in human_labels JSON files, excluding null values."""
    
    labels_dir = "/Users/machang/Documents/research-work/CellMMAgent/Visualize_DeepResearch/human_labels"
    distributions = defaultdict(Counter)
    score_distributions = defaultdict(Counter)
    total_files = 0
    
    # Store individual scores for box plot
    score_data = {
        'Evidence': [],
        'Errors': [],
        'Single Cell Analysis': [],
        'Novelty': []
    }
    
    # Get score mappings
    mappings = map_labels_to_scores()
    
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
                            
                            # Map to scores if applicable
                            if key in mappings and value in mappings[key]:
                                score = mappings[key][value]
                                score_distributions[f"{key}_score"][score] += 1
                                
                                # Store individual scores for box plot
                                if key == 'evidence':
                                    score_data['Evidence'].append(score)
                                elif key == 'errors':
                                    score_data['Errors'].append(score)
                                elif key == 'singlecell':
                                    score_data['Single Cell Analysis'].append(score)
                                elif key == 'novelty':
                                    score_data['Novelty'].append(score)
            
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error reading {filename}: {e}")
    
    print(f"Analyzed {total_files} files")
    print("=" * 50)
    
    # Create plots directory for box plot
    plots_dir = "distribution_plots"
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
    
    # Create stacked bar plot for performance distributions
    criteria_with_data = []
    
    for criterion, scores in score_data.items():
        if scores:  # Only include criteria with data
            criteria_with_data.append(criterion)
    
    if criteria_with_data:
        # Set up the figure with Nature journal standards
        plt.figure(figsize=(7, 4))  # Single column width for Nature
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams.update({
            'font.family': 'Arial',
            'font.size': 8,
            'axes.linewidth': 0.5,
            'grid.linewidth': 0.5,
            'lines.linewidth': 1.0,
            'patch.linewidth': 0.5,
            'xtick.major.width': 0.5,
            'ytick.major.width': 0.5,
            'xtick.minor.width': 0.3,
            'ytick.minor.width': 0.3,
        })
        
        # Nature journal approved color scheme - grayscale with subtle color
        score_colors = {
            1: '#2D2D2D',  # Dark gray (poor)
            2: '#5A5A5A',  # Medium dark gray (fair) 
            3: '#878787',  # Medium gray (neutral)
            4: '#B4B4B4',  # Light gray (good)
            5: '#E0E0E0'   # Very light gray (excellent)
        }
        
        
        # Calculate proportions for each criterion
        proportions_data = []
        labels = []
        
        for criterion in criteria_with_data:
            scores = score_data[criterion]
            if scores:
                # Count occurrences of each score
                score_counts = Counter(scores)
                total = len(scores)
                
                # Calculate proportions for scores 1-5
                proportions = []
                for score in range(1, 6):
                    proportion = score_counts.get(score, 0) / total
                    proportions.append(proportion)
                
                proportions_data.append(proportions)
                labels.append(criterion)
        
        if proportions_data:
            # Create diverging stacked bar chart
            x_pos = np.arange(len(labels))
            width = 0.7
            
            # For diverging chart, we need to position negative scores to the left of center
            # and positive scores to the right of center (neutral at center)
            for i, proportions in enumerate(proportions_data):
                # Calculate positions for diverging layout
                # Left side: poor (1) and fair (2) - go leftward from center
                # Center: neutral (3)  
                # Right side: good (4) and excellent (5) - go rightward from center
                
                # Left side (<=3) - poor, fair, and neutral - all warm colors
                left_total = proportions[0] + proportions[1] + proportions[2]
                left_start = -left_total  # Start position for all <=3 scores
                
                # Plot poor (leftmost)
                if proportions[0] > 0:
                    plt.barh(x_pos[i], proportions[0], height=width, 
                           left=left_start, color=score_colors[1], 
                           edgecolor='white', linewidth=0.8)
                    # Add percentage label with scientific formatting
                    if proportions[0] >= 0.03:  # Only show label if segment is large enough
                        plt.text(left_start + proportions[0]/2, x_pos[i], 
                               f'{proportions[0]:.0%}', ha='center', va='center',
                               fontsize=7, fontweight='normal', color='white')
                
                # Plot fair
                if proportions[1] > 0:
                    plt.barh(x_pos[i], proportions[1], height=width,
                           left=left_start + proportions[0], color=score_colors[2],
                           edgecolor='white', linewidth=0.8)
                    # Add percentage label
                    if proportions[1] >= 0.03:
                        plt.text(left_start + proportions[0] + proportions[1]/2, x_pos[i],
                               f'{proportions[1]:.0%}', ha='center', va='center',
                               fontsize=7, fontweight='normal', color='white')
                
                # Plot neutral (still on left side, <=3)
                if proportions[2] > 0:
                    plt.barh(x_pos[i], proportions[2], height=width,
                           left=left_start + proportions[0] + proportions[1], color=score_colors[3],
                           edgecolor='white', linewidth=0.8)
                    # Add percentage label
                    if proportions[2] >= 0.03:
                        plt.text(left_start + proportions[0] + proportions[1] + proportions[2]/2, x_pos[i], 
                               f'{proportions[2]:.0%}', ha='center', va='center', fontsize=7, 
                               fontweight='normal', color='black')
                
                # Right side (>3) - good and excellent - cool colors
                right_start = 0  # Start at center line (value 3)
                
                # Plot good
                if proportions[3] > 0:
                    plt.barh(x_pos[i], proportions[3], height=width,
                           left=right_start, color=score_colors[4],
                           edgecolor='white', linewidth=0.8)
                    # Add percentage label  
                    if proportions[3] >= 0.03:
                        plt.text(right_start + proportions[3]/2, x_pos[i],
                               f'{proportions[3]:.0%}', ha='center', va='center',
                               fontsize=7, fontweight='normal', color='black')
                
                # Plot excellent (rightmost)
                if proportions[4] > 0:
                    plt.barh(x_pos[i], proportions[4], height=width,
                           left=right_start + proportions[3], color=score_colors[5],
                           edgecolor='white', linewidth=0.8)
                    # Add percentage label
                    if proportions[4] >= 0.03:
                        plt.text(right_start + proportions[3] + proportions[4]/2, x_pos[i],
                               f'{proportions[4]:.0%}', ha='center', va='center',
                               fontsize=7, fontweight='normal', color='black')
            
            # Scientific title formatting
            plt.title('Quality Assessment Distribution', 
                     fontsize=10, fontweight='normal', pad=15, color='black')
            
            # Set y-axis labels (criteria names) with scientific formatting
            plt.yticks(x_pos, labels, fontsize=8, color='black')
            
            # Set x-axis (horizontal axis for proportions)
            ax = plt.gca()
            
            # Add vertical line at center (value 3 - the dividing line)
            plt.axvline(x=0, color='black', linewidth=2, alpha=0.8)
            
            
            # Set axis limits to show full range with space for percentage labels
            max_range = 0.7  # Increased to accommodate percentage labels
            plt.xlim(-max_range, max_range)
            
            # Remove y-axis grid, keep it clean like the image
            plt.grid(False)
            
            # Style axes for scientific publication
            ax.set_facecolor('white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('black')
            ax.spines['left'].set_linewidth(0.5)
            ax.spines['bottom'].set_color('black')
            ax.spines['bottom'].set_linewidth(0.5)
            
            # Remove x-axis ticks and labels for cleaner look
            plt.xticks([])
            plt.xlabel('')
            plt.ylabel('')
            
            # Scientific legend formatting
            legend_elements = [
                plt.Rectangle((0,0),1,1, facecolor=score_colors[1], label='Poor (≤3)', edgecolor='black', linewidth=0.5),
                plt.Rectangle((0,0),1,1, facecolor=score_colors[2], label='Fair (≤3)', edgecolor='black', linewidth=0.5),  
                plt.Rectangle((0,0),1,1, facecolor=score_colors[3], label='Neutral (≤3)', edgecolor='black', linewidth=0.5),
                plt.Rectangle((0,0),1,1, facecolor=score_colors[4], label='Good (>3)', edgecolor='black', linewidth=0.5),
                plt.Rectangle((0,0),1,1, facecolor=score_colors[5], label='Excellent (>3)', edgecolor='black', linewidth=0.5)
            ]
            plt.legend(handles=legend_elements, loc='upper center', 
                      bbox_to_anchor=(0.5, -0.08), ncol=5, frameon=True,
                      fontsize=7, fancybox=False, shadow=False, 
                      edgecolor='black', facecolor='white', framealpha=1)
            
            plt.tight_layout()
            
            # Save with Nature journal specifications
            stacked_plot_filename = os.path.join(plots_dir, "performance_stacked_distribution.png")
            plt.savefig(stacked_plot_filename, dpi=600, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', format='png')
            
            # Also save as vector format for publication
            stacked_plot_filename_eps = os.path.join(plots_dir, "performance_stacked_distribution.eps")
            plt.savefig(stacked_plot_filename_eps, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', format='eps')
            plt.show()
            print(f"\nStacked bar plot saved as: {stacked_plot_filename}")

if __name__ == "__main__":
    calculate_distributions()