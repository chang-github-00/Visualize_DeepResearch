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
    """Calculate distribution for each field in human_labels JSON files, comparing first and second rounds."""
    
    labels_dir = "/Users/machang/Documents/research-work/CellMMAgent/Visualize_DeepResearch/human_labels"
    total_files = 0
    
    # Store individual scores for both rounds
    score_data_first = {
        'Evidence': [],
        'Errors': [],
        'Single Cell Analysis': [],
        'Novelty': []
    }
    
    score_data_second = {
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
                    
                    # Determine if this is first round (no underscore after attempt_X) or second round (has _Y suffix)
                    # First round: labels_attempt_X.json
                    # Second round: labels_attempt_X_Y.json
                    is_second_round = filename.count('_') >= 3  # labels_attempt_X_Y has 3+ underscores
                    
                    # Choose appropriate data structure
                    current_score_data = score_data_second if is_second_round else score_data_first
                    
                    # Count values for each field, excluding null/empty values
                    for key, value in data.items():
                        if key in ['attemptId', 'geneName', 'timestamp', 'explore', 'comments']:
                            continue  # Skip ID and non-scoring fields
                        
                        if value is not None and value != "" and value != "null":
                            # Map to scores if applicable
                            if key in mappings and value in mappings[key]:
                                score = mappings[key][value]
                                
                                # Store individual scores
                                if key == 'evidence':
                                    current_score_data['Evidence'].append(score)
                                elif key == 'errors':
                                    current_score_data['Errors'].append(score)
                                elif key == 'singlecell':
                                    current_score_data['Single Cell Analysis'].append(score)
                                elif key == 'novelty':
                                    current_score_data['Novelty'].append(score)
            
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error reading {filename}: {e}")
    
    print(f"Analyzed {total_files} files")
    print(f"First round files: {sum(len(scores) for scores in score_data_first.values())}")
    print(f"Second round files: {sum(len(scores) for scores in score_data_second.values())}")
    print("=" * 50)
    
    # Create plots directory for plots
    plots_dir = "distribution_plots"
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
    
    # Create side-by-side stacked bar plot for performance distributions comparison
    criteria_with_data = []
    
    # Find criteria that have data in either round
    all_criteria = set(score_data_first.keys()) | set(score_data_second.keys())
    for criterion in all_criteria:
        if (criterion in score_data_first and score_data_first[criterion]) or \
           (criterion in score_data_second and score_data_second[criterion]):
            criteria_with_data.append(criterion)
    
    if criteria_with_data:
        # Set up single figure for grouped comparison
        plt.figure(figsize=(6, 3))
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams.update({
            'font.family': 'DejaVu Sans',
            'font.size': 8,
            'axes.linewidth': 0.5,
            'grid.linewidth': 0.5,
            'lines.linewidth': 0.8,
            'patch.linewidth': 0.5,
            'xtick.major.width': 0.5,
            'ytick.major.width': 0.5,
            'xtick.minor.width': 0.3,
            'ytick.minor.width': 0.3,
        })
        
        # Color scheme from the provided palette
        score_colors = {
            1: '#E58585',  # Coral/salmon (poor) - from RGB 229,133,119
            3: '#F2B76F',  # Light orange (fair) - from RGB 242,187,124
            2: '#FCB3D9',  # Light purple (fair) - from RGB 188,186,218
            # 3: '#F8F8BB',  # Light yellow (neutral) - from RGB 250,248,187
            4: '#BDD788',  # Light green/teal (good) - from RGB 156,207,198
            5: '#B2E1F6'   # Light blue (excellent) - from RGB 138,176,207
        }
        
        # Create grouped data - each criterion appears twice (first round, then second round)
        proportions_data_grouped = []
        labels_grouped = []
        use_hatching = []
        y_positions = []
        
        # Calculate positions with touching bars within groups
        current_y = 0
        group_spacing = 1.0  # Space between different criteria groups
        bar_width = 0.7   # Bar width
        
        for criterion in criteria_with_data:
            # First round data
            scores_first = score_data_first.get(criterion, [])
            if scores_first:
                score_counts = Counter(scores_first)
                total = len(scores_first)
                proportions_first = []
                for score in range(1, 6):
                    proportion = score_counts.get(score, 0) / total
                    proportions_first.append(proportion)
                proportions_data_grouped.append(proportions_first)
            else:
                proportions_data_grouped.append([0, 0, 0, 0, 0])
            labels_grouped.append(f"{criterion}")
            use_hatching.append(False)
            y_positions.append(current_y)
            
            # Second round data (touching the first round bar)
            current_y += bar_width  # Move by exactly bar width to make them touch
            scores_second = score_data_second.get(criterion, [])
            if scores_second:
                score_counts = Counter(scores_second)
                total = len(scores_second)
                proportions_second = []
                for score in range(1, 6):
                    proportion = score_counts.get(score, 0) / total
                    proportions_second.append(proportion)
                proportions_data_grouped.append(proportions_second)
            else:
                proportions_data_grouped.append([0, 0, 0, 0, 0])
            labels_grouped.append(f"{criterion}")
            use_hatching.append(True)
            y_positions.append(current_y)
            
            # Move to next group
            current_y += bar_width + group_spacing
        
        if proportions_data_grouped:
            # Create grouped stacked bar chart
            width = bar_width  # Use the same width as defined above
            
            for i, proportions in enumerate(proportions_data_grouped):
                if any(p > 0 for p in proportions):  # Only plot if there's data
                    # Left side (<=3) - poor, fair, and neutral
                    left_total = proportions[0] + proportions[1] + proportions[2]
                    left_start = -left_total
                    
                    # Choose pattern based on round
                    hatch_pattern = '///' if use_hatching[i] else None
                    
                    # Plot poor, fair, neutral on left side with thicker interior lines
                    if proportions[0] > 0:
                        plt.barh(y_positions[i], proportions[0], height=width, 
                               left=left_start, color=score_colors[1], alpha=0.3,
                               edgecolor='black', linewidth=1.0, hatch=hatch_pattern)
                    if proportions[1] > 0:
                        plt.barh(y_positions[i], proportions[1], height=width,
                               left=left_start + proportions[0], color=score_colors[2], alpha=0.3,
                               edgecolor='black', linewidth=1.0, hatch=hatch_pattern)
                    if proportions[2] > 0:
                        plt.barh(y_positions[i], proportions[2], height=width,
                               left=left_start + proportions[0] + proportions[1], color=score_colors[3], alpha=0.3,
                               edgecolor='black', linewidth=1.0, hatch=hatch_pattern)
                    
                    # Right side (>3) - good and excellent with thicker interior lines
                    right_start = 0
                    if proportions[3] > 0:
                        plt.barh(y_positions[i], proportions[3], height=width,
                               left=right_start, color=score_colors[4], alpha=0.3,
                               edgecolor='black', linewidth=1.0, hatch=hatch_pattern)
                    if proportions[4] > 0:
                        plt.barh(y_positions[i], proportions[4], height=width,
                               left=right_start + proportions[3], color=score_colors[5], alpha=0.3,
                               edgecolor='black', linewidth=1.0, hatch=hatch_pattern)
                    
                    # Draw thicker outline around the entire bar
                    total_left = left_total
                    total_right = proportions[3] + proportions[4]
                    
                    # Outer box with much thicker lines (3x thicker)
                    from matplotlib.patches import Rectangle
                    full_width = total_left + total_right
                    rect = Rectangle((-total_left, y_positions[i] - width/2), 
                                   full_width, width, 
                                   fill=False, edgecolor='black', linewidth=1.0)
                    plt.gca().add_patch(rect)
            
            # No title - removed as requested
            
            # Create single label per criterion group, positioned in the middle
            group_labels = []
            group_positions = []
            
            # Map criteria to more descriptive labels
            criteria_labels = {
                'Evidence': 'Evidence Grounding Quality',
                'Single Cell Analysis': 'Single Cell Analysis Quality',
                'Novelty': 'Novelty',
                'Errors': 'No Factual Errors'
            }
            
            # Get unique criteria and calculate middle positions
            for i, criterion in enumerate(criteria_with_data):
                # Find the middle position between R1 and R2 bars for this criterion
                r1_pos = y_positions[i*2]      # First bar position for this criterion
                r2_pos = y_positions[i*2 + 1]  # Second bar position for this criterion
                middle_pos = (r1_pos + r2_pos) / 2
                
                # Use descriptive label if available, otherwise use original
                descriptive_label = criteria_labels.get(criterion, criterion)
                group_labels.append(descriptive_label)
                group_positions.append(middle_pos)
            
            plt.yticks(group_positions, group_labels, fontsize=8, color='black')
            plt.axvline(x=0, color='black', linewidth=2, alpha=0.3)
            
            max_range = 0.9
            padding = 0.05  # Add padding to prevent cutoff
            plt.xlim(-0.7 * max_range - padding, max_range + padding)
            
            # Set y-axis limits to accommodate all groups with padding
            y_padding = 0.3  # Extra padding for y-axis
            plt.ylim(-y_padding, max(y_positions) + bar_width + y_padding)
            
            plt.grid(False)
            
            ax = plt.gca()
            ax.set_facecolor('white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('black')
            ax.spines['left'].set_linewidth(0.5)
            ax.spines['bottom'].set_color('black')
            ax.spines['bottom'].set_linewidth(0.5)
            
            # Add 50% markers on x-axis
            plt.xticks([-0.5, 0, 0.5], ['50%', '0%', '50%'], fontsize=8, color='black')
            plt.xlabel('')
            plt.ylabel('')
            
            # Create two separate legend groups without boxes
            
            # First legend group for score categories (colors)
            color_legend_elements = [
                plt.Rectangle((0,0),1,1, facecolor=score_colors[1], label='Poor', edgecolor='gainsboro', linewidth=0.5),
                plt.Rectangle((0,0),1,1, facecolor=score_colors[2], label='Fair', edgecolor='gainsboro', linewidth=0.5), 
                plt.Rectangle((0,0),1,1, facecolor=score_colors[3], label='Neutral', edgecolor='gainsboro', linewidth=0.5),
                plt.Rectangle((0,0),1,1, facecolor=score_colors[4], label='Good', edgecolor='gainsboro', linewidth=0.5),
                plt.Rectangle((0,0),1,1, facecolor=score_colors[5], label='Excellent', edgecolor='gainsboro', linewidth=0.5)
            ]
            
            # Second legend group for method indicators (line types)
            method_legend_elements = [
                plt.Rectangle((0,0),1,1, facecolor='white', label='AgentSee', edgecolor='black', linewidth=0.5),
                plt.Rectangle((0,0),1,1, facecolor='white', hatch='///', label='Human Review + AgentSee', edgecolor='black', linewidth=0.5)
            ]
            
            # Create first legend for colors (no box) - positioned at top center
            first_legend = plt.legend(handles=color_legend_elements, loc='upper center', 
                                    bbox_to_anchor=(0.5, 1.17), ncol=5, frameon=False,
                                    fontsize=7)
            
            # Add the first legend back to the plot
            plt.gca().add_artist(first_legend)
            
            # Create second legend for methods (no box) - positioned at top center
            plt.legend(handles=method_legend_elements, loc='upper center', 
                      bbox_to_anchor=(0.5, 1.12), ncol=2, frameon=False,
                      fontsize=7)
            
            # Add a smaller black-edged box around both legends
            from matplotlib.patches import Rectangle
            ax = plt.gca()
            
            # Calculate box dimensions to fit snugly around the legends
            legend_box = Rectangle((-0.1, 1.02), 1.2, 0.13, 
                                 transform=ax.transAxes, 
                                 fill=False, edgecolor='lightgray', linewidth=0.5, 
                                 clip_on=False)
            ax.add_patch(legend_box)
            
            plt.tight_layout(pad=2.0)  # Add padding around the entire plot
            
            # Save with Nature journal specifications
            stacked_plot_filename = os.path.join(plots_dir, "performance_stacked_distribution.png")
            plt.savefig(stacked_plot_filename, dpi=600, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', format='png')
            
            # Save as PDF for publication
            stacked_plot_filename_pdf = os.path.join(plots_dir, "performance_stacked_distribution.pdf")
            plt.savefig(stacked_plot_filename_pdf, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', format='pdf')
            
            # Also save as vector format for publication
            stacked_plot_filename_eps = os.path.join(plots_dir, "performance_stacked_distribution.eps")
            plt.savefig(stacked_plot_filename_eps, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', format='eps')
            plt.show()
            print(f"\nStacked bar plot saved as: {stacked_plot_filename}")
            print(f"PDF version saved as: {stacked_plot_filename_pdf}")
            print(f"EPS version saved as: {stacked_plot_filename_eps}")

if __name__ == "__main__":
    calculate_distributions()