#!/usr/bin/env python3
"""
Simple HTTP server to serve the JUMP Discovery Visualizer
and provide API endpoints for dynamic data loading.
"""

import os
import json
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import glob
from collections import Counter

class JUMPVisualizerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.data_dir = "/Users/machang/Documents/research-work/CellMMAgent/Visualize_DeepResearch/JUMPDiscovery_results"
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/attempts':
            self.handle_attempts_api()
        elif parsed_path.path.startswith('/api/attempt/'):
            attempt_id = parsed_path.path.split('/')[-1]
            self.handle_attempt_details_api(attempt_id)
        elif parsed_path.path == '/api/labels':
            self.handle_get_labels_api()
        elif parsed_path.path.endswith('.md'):
            self.handle_markdown_file(parsed_path.path)
        else:
            # Serve static files
            super().do_GET()
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/save_labels':
            self.handle_save_labels_api()
        elif parsed_path.path == '/api/clear_labels':
            self.handle_clear_labels_api()
        else:
            self.send_error(404, "Endpoint not found")
    
    def handle_save_labels_api(self):
        """Save human evaluation labels for an attempt"""
        try:
            # Get request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            labels_data = json.loads(post_data.decode('utf-8'))
            
            # Create labels directory if it doesn't exist
            labels_dir = os.path.join(os.path.dirname(self.data_dir), "human_labels")
            os.makedirs(labels_dir, exist_ok=True)
            
            # Save labels to file
            labels_file = os.path.join(labels_dir, f"labels_{labels_data['attemptId']}.json")
            with open(labels_file, 'w', encoding='utf-8') as f:
                json.dump(labels_data, f, indent=2, ensure_ascii=False)
            
            self.send_json_response({"success": True, "message": "Labels saved successfully"})
            
        except Exception as e:
            self.send_error_response(f"Error saving labels: {str(e)}")
    
    def handle_clear_labels_api(self):
        """Clear all human evaluation labels"""
        try:
            import shutil
            
            labels_dir = os.path.join(os.path.dirname(self.data_dir), "human_labels")
            
            if os.path.exists(labels_dir):
                shutil.rmtree(labels_dir)
                print(f"Cleared labels directory: {labels_dir}")
            
            self.send_json_response({"success": True, "message": "All labels cleared successfully"})
            
        except Exception as e:
            self.send_error_response(f"Error clearing labels: {str(e)}")
    
    def handle_get_labels_api(self):
        """Get all saved human evaluation labels"""
        try:
            labels_dir = os.path.join(os.path.dirname(self.data_dir), "human_labels")
            labels = {}
            
            if os.path.exists(labels_dir):
                for filename in os.listdir(labels_dir):
                    if filename.startswith('labels_') and filename.endswith('.json'):
                        attempt_id = filename.replace('labels_', '').replace('.json', '')
                        file_path = os.path.join(labels_dir, filename)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                labels[attempt_id] = json.load(f)
                        except Exception as e:
                            print(f"Error reading labels file {filename}: {str(e)}")
            
            self.send_json_response(labels)
            
        except Exception as e:
            self.send_error_response(f"Error loading labels: {str(e)}")
    
    def handle_attempts_api(self):
        """Return list of all attempts with basic metadata"""
        try:
            attempts = []
            
            # Scan for attempt folders
            attempt_dirs = glob.glob(os.path.join(self.data_dir, "attempt_*"))
            
            for attempt_dir in sorted(attempt_dirs):
                attempt_id = os.path.basename(attempt_dir)
                attempt_num = attempt_id.replace('attempt_', '')
                
                # Extract gene name from report files
                gene_name = self.extract_gene_name(attempt_dir)
                
                # Find evidence figures (comprehensive, single cell, segmentation, etc.)
                comprehensive_figures = self.find_comprehensive_figures(attempt_dir)
                
                # Find report file
                report_path = self.find_report_file(attempt_dir)
                
                # Extract research hypothesis as title
                research_hypothesis = self.extract_research_hypothesis(attempt_dir, report_path)
                
                # Calculate quality scores
                quality_scores = self.calculate_quality_scores(attempt_dir, report_path)
                
                attempts.append({
                    'id': attempt_id,
                    'name': f'Attempt {attempt_num}',
                    'gene': gene_name,
                    'reportPath': report_path,
                    'comprehensiveFigures': comprehensive_figures,
                    'attemptNumber': attempt_num,
                    'researchHypothesis': research_hypothesis,
                    'scores': quality_scores
                })
            
            self.send_json_response(attempts)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR in handle_attempts_api: {str(e)}")
            print(f"Traceback: {error_details}")
            self.send_error_response(f"Error loading attempts: {str(e)}")
    
    def handle_attempt_details_api(self, attempt_id):
        """Return detailed information for a specific attempt"""
        try:
            attempt_dir = os.path.join(self.data_dir, attempt_id)
            
            if not os.path.exists(attempt_dir):
                self.send_error_response(f"Attempt {attempt_id} not found")
                return
            
            gene_name = self.extract_gene_name(attempt_dir)
            comprehensive_figures = self.find_comprehensive_figures(attempt_dir)
            report_path = self.find_report_file(attempt_dir)
            
            # Read report summary if available
            report_summary = self.extract_report_summary(attempt_dir, report_path)
            
            details = {
                'id': attempt_id,
                'gene': gene_name,
                'reportPath': report_path,
                'comprehensiveFigures': comprehensive_figures,
                'summary': report_summary,
                'files': self.list_attempt_files(attempt_dir)
            }
            
            self.send_json_response(details)
            
        except Exception as e:
            self.send_error_response(f"Error loading attempt details: {str(e)}")
    
    def extract_gene_name(self, attempt_dir):
        """Extract gene name from report files or directory contents"""
        # Try to find gene name from report file names first
        report_files = glob.glob(os.path.join(attempt_dir, "report_*.md"))
        
        for report_file in report_files:
            filename = os.path.basename(report_file)
            # Pattern: report_GENENAME_description.md
            match = re.search(r'report_([A-Z0-9]+)_', filename)
            if match:
                return match.group(1)
        
        # If no report files or gene name not found, analyze file prefixes
        gene_from_prefix = self.extract_gene_from_file_prefixes(attempt_dir)
        if gene_from_prefix:
            return gene_from_prefix
        
        # Fallback: look for gene names in other files
        all_files = os.listdir(attempt_dir)
        
        # Common gene name patterns
        gene_patterns = [
            r'([A-Z][A-Z0-9]{2,8})_',  # Standard gene names
            r'([A-Z]{3,8})_'           # Alternative patterns
        ]
        
        for filename in all_files:
            for pattern in gene_patterns:
                match = re.search(pattern, filename)
                if match:
                    gene_candidate = match.group(1)
                    # Filter out common false positives
                    if gene_candidate not in ['JUMP', 'RESEARCH', 'PROBLEM', 'VERIFIED']:
                        return gene_candidate
        
        # Final fallback
        attempt_num = os.path.basename(attempt_dir).replace('attempt_', '')
        return f"Gene_{attempt_num}"
    
    def extract_gene_from_file_prefixes(self, attempt_dir):
        """Extract gene name from most common prefix in CSV/PNG files"""
        relevant_files = []
        
        # Walk through directory to find CSV and PNG files
        for root, dirs, files in os.walk(attempt_dir):
            for file in files:
                if file.lower().endswith(('.csv', '.png')):
                    relevant_files.append(file)
        
        if not relevant_files:
            return None
        
        # Extract potential gene prefixes (before first underscore or dot)
        prefixes = []
        for filename in relevant_files:
            # Remove extension and get prefix before first underscore
            base_name = os.path.splitext(filename)[0]
            if '_' in base_name:
                prefix = base_name.split('_')[0]
            else:
                prefix = base_name
            
            # Only consider prefixes that look like gene names (2-10 chars, mostly uppercase)
            if 2 <= len(prefix) <= 10 and prefix.isalnum():
                # Convert to uppercase for consistency
                prefix_upper = prefix.upper()
                # Filter out common non-gene prefixes
                if prefix_upper not in ['TOP', 'ALL', 'CELL', 'IMAGE', 'DATA', 'RESULT', 'ANALYSIS', 
                                       'FIGURE', 'TABLE', 'PLOT', 'GRAPH', 'CHART', 'SUMMARY']:
                    prefixes.append(prefix_upper)
        
        if not prefixes:
            return None
        
        # Count occurrences and find most common
        from collections import Counter
        prefix_counts = Counter(prefixes)
        
        # Get most common prefix that appears in at least 2 files
        for prefix, count in prefix_counts.most_common():
            if count >= 2:  # Must appear in at least 2 files
                return prefix
        
        # If no prefix appears twice, return the most common one
        if prefix_counts:
            return prefix_counts.most_common(1)[0][0]
        
        return None
    
    def extract_research_hypothesis(self, attempt_dir, report_path):
        """Extract research hypothesis from report file"""
        if not report_path:
            return None
        
        try:
            full_path = os.path.join(attempt_dir, report_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for research hypothesis section
            lines = content.split('\n')
            for i, line in enumerate(lines):
                # Check for research hypothesis headers
                if any(phrase in line.lower() for phrase in [
                    'research hypothesis', 
                    '# research hypothesis',
                    '## research hypothesis',
                    'hypothesis:',
                    'research question'
                ]):
                    # Get the next non-empty line after the header
                    for j in range(i + 1, min(i + 10, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and not next_line.startswith('#') and not next_line.startswith('*'):
                            # Clean up the hypothesis text
                            hypothesis = next_line.replace('**', '').replace('*', '').strip()
                            if len(hypothesis) > 20:  # Ensure it's substantial
                                return hypothesis
                            break
            
            # Fallback: look for the first substantial paragraph after any title
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith('#'):
                    # Skip metadata lines
                    if not any(keyword in line.lower() for keyword in ['date:', 'author:', 'version:']):
                        cleaned = line.strip().replace('**', '').replace('*', '')
                        if len(cleaned) > 30 and not cleaned.startswith('Investigation'):
                            return cleaned
            
            return None
            
        except Exception:
            return None
    
    def find_comprehensive_figures(self, attempt_dir):
        """Find all evidence figures (comprehensive, single, cell, segmentation, composite, comparison) at any level of hierarchy"""
        figures = []
        
        # Keywords to search for in PNG filenames
        search_keywords = ['comprehensive', 'single', 'cell', 'segmentation', 'composite', 'comparison']
        
        # Walk through all subdirectories to find PNG files with keywords
        for root, dirs, files in os.walk(attempt_dir):
            for file in files:
                # Check if it's a PNG file with any of the keywords in the name
                if file.lower().endswith('.png'):
                    file_lower = file.lower()
                    if any(keyword in file_lower for keyword in search_keywords):
                        full_path = os.path.join(root, file)
                        # Create web-accessible path from the working directory
                        rel_path = os.path.relpath(full_path, os.path.dirname(self.data_dir))
                        figures.append(rel_path)
        
        # Sort for consistent ordering
        figures.sort()
        
        return figures
    
    def find_report_file(self, attempt_dir):
        """Find the main report markdown file"""
        report_files = glob.glob(os.path.join(attempt_dir, "report_*.md"))
        
        if report_files:
            # Return just the filename for proper URL construction
            return os.path.basename(report_files[0])
        
        # Return null if no report file found
        return None
    
    def extract_report_summary(self, attempt_dir, report_path):
        """Extract summary from the report file"""
        if not report_path:
            return None
        
        try:
            full_path = os.path.join(attempt_dir, report_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for executive summary or first few paragraphs
            lines = content.split('\n')
            summary_lines = []
            in_summary = False
            
            for line in lines:
                if '## Executive Summary' in line or '## Summary' in line:
                    in_summary = True
                    continue
                elif in_summary and line.startswith('##'):
                    break
                elif in_summary and line.strip():
                    summary_lines.append(line.strip())
                    if len(summary_lines) >= 3:  # Limit summary length
                        break
            
            return ' '.join(summary_lines) if summary_lines else None
            
        except Exception:
            return None
    
    def calculate_quality_scores(self, attempt_dir, report_path):
        """Calculate quality scores based on report content"""
        if not report_path:
            return {"overall": 50, "confidence": 50, "novelty": 50, "evidence": 50}
        
        try:
            full_path = os.path.join(attempt_dir, report_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
            
            # Calculate confidence score based on statistical significance
            confidence = 30
            if 'p <' in content or 'p<' in content:
                confidence += 20
            if 'significant' in content:
                confidence += 15
            if 'p < 0.05' in content or 'p<0.05' in content:
                confidence += 10
            if 'p < 0.01' in content or 'p<0.01' in content:
                confidence += 15
            if 'comprehensive' in content:
                confidence += 10
            
            # Calculate novelty score based on research terms
            novelty = 40
            if 'novel' in content:
                novelty += 20
            if 'unprecedented' in content or 'first time' in content:
                novelty += 15
            if 'discovery' in content:
                novelty += 10
            if 'mechanism' in content:
                novelty += 10
            if 'pathway' in content:
                novelty += 5
            
            # Calculate evidence score based on data quality indicators
            evidence = 35
            if 'figure' in content:
                evidence += 10
            if 'morphological' in content:
                evidence += 15
            if 'validation' in content:
                evidence += 10
            if 'comprehensive' in content:
                evidence += 15
            if 'statistical' in content:
                evidence += 10
            if 'correlation' in content:
                evidence += 5
            
            # Overall score is weighted average
            overall = (confidence * 0.4 + novelty * 0.3 + evidence * 0.3)
            
            return {
                "overall": min(100, max(20, overall)),
                "confidence": min(100, max(20, confidence)),
                "novelty": min(100, max(20, novelty)),
                "evidence": min(100, max(20, evidence))
            }
            
        except Exception:
            # Default scores if parsing fails
            return {"overall": 50, "confidence": 50, "novelty": 50, "evidence": 50}
    
    def list_attempt_files(self, attempt_dir):
        """List relevant files in the attempt directory"""
        try:
            all_files = os.listdir(attempt_dir)
            
            # Filter for relevant file types
            relevant_files = []
            for filename in all_files:
                if any(filename.endswith(ext) for ext in ['.png', '.jpg', '.md', '.csv', '.json']):
                    if not filename.startswith('.'):  # Skip hidden files
                        relevant_files.append(filename)
            
            return sorted(relevant_files)
            
        except Exception:
            return []
    
    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def send_error_response(self, message):
        """Send error response"""
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = json.dumps({'error': message})
        self.wfile.write(response.encode('utf-8'))
    
    def handle_markdown_file(self, path):
        """Convert markdown file to HTML and serve it"""
        try:
            # Remove leading slash and construct file path
            file_path = path.lstrip('/')
            full_path = os.path.join(os.path.dirname(self.data_dir), file_path)
            
            if not os.path.exists(full_path):
                self.send_error(404, "Markdown file not found")
                return
            
            # Read markdown content
            with open(full_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convert to HTML using simple markdown parser
            html_content = self.convert_markdown_to_html(md_content)
            
            # Extract filename for title
            filename = os.path.basename(full_path)
            title = filename.replace('_', ' ').replace('.md', '').title()
            
            # Create complete HTML page
            html_page = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - JUMP Discovery Report</title>
    <style>
        :root {{
            --primary-bg: #0a0f1e;
            --secondary-bg: #1a2332;
            --accent-bg: #2d3f5f;
            --panel-bg: #162030;
            --border-color: #2d4560;
            --text-primary: #e8f4fd;
            --text-secondary: #a8c5e6;
            --text-muted: #6a8db3;
            --accent-gold: #ffd700;
            --accent-blue: #4fc3f7;
            --success: #4caf50;
            --warning: #ff9800;
            --danger: #f44336;
            --shadow: rgba(0, 0, 0, 0.4);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, var(--primary-bg) 0%, var(--secondary-bg) 50%, var(--accent-bg) 100%);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: var(--panel-bg);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            border: 2px solid var(--border-color);
            box-shadow: 0 8px 32px var(--shadow);
        }}
        
        .header h1 {{
            color: var(--accent-blue);
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        .header .meta {{
            color: var(--text-muted);
            font-size: 14px;
        }}
        
        .back-btn {{
            display: inline-block;
            background: var(--accent-bg);
            color: var(--text-primary);
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            margin-bottom: 20px;
            transition: all 0.3s ease;
            border: 1px solid var(--border-color);
        }}
        
        .back-btn:hover {{
            background: var(--accent-blue);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px var(--shadow);
        }}
        
        .content {{
            background: var(--panel-bg);
            padding: 30px;
            border-radius: 12px;
            border: 2px solid var(--border-color);
            box-shadow: 0 8px 32px var(--shadow);
            text-align: left;
            direction: ltr;
        }}
        
        .content * {{
            text-align: left !important;
            margin-left: 0 !important;
        }}
        
        .content p {{
            line-height: 1.7;
            margin-bottom: 16px;
        }}
        
        .content h1, .content h2, .content h3, .content h4 {{
            margin-top: 24px;
            margin-bottom: 16px;
            line-height: 1.3;
        }}
        
        .content h1:first-child, .content h2:first-child, 
        .content h3:first-child, .content h4:first-child {{
            margin-top: 0;
        }}
        
        .content h1 {{
            color: var(--accent-blue);
            font-size: 32px;
            margin-bottom: 20px;
            border-bottom: 3px solid var(--accent-blue);
            padding-bottom: 10px;
        }}
        
        .content h2 {{
            color: var(--accent-gold);
            font-size: 24px;
            margin: 30px 0 15px 0;
            border-left: 4px solid var(--accent-gold);
            padding-left: 15px;
        }}
        
        .content h3 {{
            color: var(--text-primary);
            font-size: 20px;
            margin: 25px 0 10px 0;
        }}
        
        .content h4 {{
            color: var(--text-secondary);
            font-size: 18px;
            margin: 20px 0 8px 0;
        }}
        
        .content p {{
            margin-bottom: 15px;
            color: var(--text-secondary);
        }}
        
        .content ul, .content ol {{
            margin-bottom: 15px;
            padding-left: 30px;
            color: var(--text-secondary);
            text-align: left;
            margin-left: 0;
        }}
        
        .content li {{
            margin-bottom: 8px;
            text-align: left;
            list-style-position: inside;
        }}
        
        .content ol {{
            counter-reset: item;
        }}
        
        .content ol li {{
            display: block;
            margin-bottom: 0.5em;
            margin-left: 0;
        }}
        
        .content ol li:before {{
            content: counter(item, decimal) ". ";
            counter-increment: item;
            font-weight: bold;
            color: var(--accent-gold);
        }}
        
        .content strong {{
            color: var(--text-primary);
            font-weight: 600;
        }}
        
        .content code {{
            background: var(--accent-bg);
            color: var(--accent-gold);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Monaco', 'Consolas', monospace;
        }}
        
        .content pre {{
            background: var(--accent-bg);
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 20px 0;
            border: 1px solid var(--border-color);
        }}
        
        .content pre code {{
            background: none;
            padding: 0;
        }}
        
        .content blockquote {{
            border-left: 4px solid var(--accent-blue);
            background: var(--accent-bg);
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
            font-style: italic;
        }}
        
        .content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: var(--secondary-bg);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .content th, .content td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .content th {{
            background: var(--accent-bg);
            color: var(--text-primary);
            font-weight: 600;
        }}
        
        .content td {{
            color: var(--text-secondary);
        }}
        
        .content a {{
            color: var(--accent-blue);
            text-decoration: none;
            border-bottom: 1px dotted var(--accent-blue);
        }}
        
        .content a:hover {{
            color: var(--accent-gold);
            border-bottom-color: var(--accent-gold);
        }}
        
        .content hr {{
            border: none;
            height: 2px;
            background: linear-gradient(to right, transparent, var(--border-color), transparent);
            margin: 30px 0;
        }}
        
        .highlight {{
            background: var(--accent-bg);
            padding: 3px 8px;
            border-radius: 4px;
            color: var(--accent-gold);
            font-weight: 600;
        }}
        
        ::-webkit-scrollbar {{
            width: 12px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: var(--accent-bg);
            border-radius: 6px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 6px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--accent-blue);
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="javascript:history.back()" class="back-btn">← Back to Visualizer</a>
        
        <div class="header">
            <h1>📊 JUMP Discovery Report</h1>
            <div class="meta">Research Analysis • {filename}</div>
        </div>
        
        <div class="content">
            {html_content}
        </div>
    </div>
</body>
</html>
"""
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(html_page.encode('utf-8'))
            
        except Exception as e:
            self.send_error_response(f"Error rendering markdown: {str(e)}")
    
    def convert_markdown_to_html(self, md_content):
        """Simple markdown to HTML converter"""
        html = md_content
        
        # Escape HTML entities first
        html = html.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Headers (more specific patterns)
        html = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Bold and italic (non-greedy)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', html)
        
        # Code blocks (preserve formatting)
        html = re.sub(r'```([^`]*?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
        html = re.sub(r'`([^`]+?)`', r'<code>\1</code>', html)
        
        # Links
        html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
        
        # Tables - handle before lists (but only real markdown tables)
        html = self.convert_proper_markdown_tables(html)
        
        # Lists - improved handling
        lines = html.split('\n')
        in_unordered_list = False
        in_ordered_list = False
        result_lines = []
        
        for line in lines:
            # Unordered lists
            if re.match(r'^[\s]*[-\*\+] ', line):
                # Close ordered list if open
                if in_ordered_list:
                    result_lines.append('</ol>')
                    in_ordered_list = False
                # Open unordered list if not already open
                if not in_unordered_list:
                    result_lines.append('<ul>')
                    in_unordered_list = True
                item = re.sub(r'^[\s]*[-\*\+] (.*)', r'<li>\1</li>', line)
                result_lines.append(item)
            # Ordered lists
            elif re.match(r'^[\s]*\d+\. ', line):
                # Close unordered list if open
                if in_unordered_list:
                    result_lines.append('</ul>')
                    in_unordered_list = False
                # Open ordered list if not already open
                if not in_ordered_list:
                    result_lines.append('<ol>')
                    in_ordered_list = True
                item = re.sub(r'^[\s]*\d+\. (.*)', r'<li>\1</li>', line)
                result_lines.append(item)
            else:
                # Close any open lists
                if in_unordered_list:
                    result_lines.append('</ul>')
                    in_unordered_list = False
                if in_ordered_list:
                    result_lines.append('</ol>')
                    in_ordered_list = False
                result_lines.append(line)
        
        # Close any remaining open lists
        if in_unordered_list:
            result_lines.append('</ul>')
        if in_ordered_list:
            result_lines.append('</ol>')
        
        html = '\n'.join(result_lines)
        
        # Paragraphs - better handling
        lines = html.split('\n')
        result_lines = []
        current_para = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                if current_para:
                    para_text = ' '.join(current_para).strip()
                    if para_text and not para_text.startswith('<'):
                        result_lines.append(f'<p>{para_text}</p>')
                    else:
                        result_lines.append(para_text)
                    current_para = []
                result_lines.append('')
                continue
            
            # HTML tags (headers, lists, etc.) - add directly
            if line.startswith('<'):
                if current_para:
                    para_text = ' '.join(current_para).strip()
                    if para_text:
                        result_lines.append(f'<p>{para_text}</p>')
                    current_para = []
                result_lines.append(line)
            else:
                # Regular text - accumulate for paragraph
                current_para.append(line)
        
        # Handle any remaining paragraph
        if current_para:
            para_text = ' '.join(current_para).strip()
            if para_text:
                result_lines.append(f'<p>{para_text}</p>')
        
        html = '\n'.join(result_lines)
        
        # Clean up multiple empty lines
        html = re.sub(r'\n\s*\n\s*\n+', '\n\n', html)
        
        # Horizontal rules
        html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)
        
        return html
    
    def convert_proper_markdown_tables(self, html):
        """Convert only properly formatted markdown tables to HTML tables"""
        lines = html.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Very strict detection: only process if we have a clear markdown table
            if ('|' in line and line.count('|') >= 3 and  # Must have at least 3 pipes (start|col|col|end)
                not any(char in line for char in ['+']) and  # No ASCII art
                line.count('-') < 10):  # Not a separator line itself
                
                # Check if next line is a proper markdown table separator
                if (i + 1 < len(lines)):
                    next_line = lines[i + 1].strip()
                    
                    # Very specific pattern for markdown table separator
                    if (next_line.startswith('|') and next_line.endswith('|') and 
                        next_line.count('-') >= 3 and 
                        re.match(r'^\|[\s\-\:\|]+\|$', next_line)):
                        
                        # Check if we have at least one data row after separator
                        if (i + 2 < len(lines) and '|' in lines[i + 2] and 
                            lines[i + 2].count('|') >= 3):
                            
                            # This looks like a real table - parse it
                            table_html, lines_consumed = self.parse_strict_markdown_table(lines, i)
                            if table_html != line:  # Only if parsing succeeded
                                result_lines.append(table_html)
                                i += lines_consumed
                                continue
            
            result_lines.append(line)
            i += 1
        
        return '\n'.join(result_lines)
    
    def parse_strict_markdown_table(self, lines, start_index):
        """Parse a strictly validated markdown table"""
        table_lines = []
        
        # Collect table lines until we hit an empty line or non-table line
        i = start_index
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                break  # Empty line ends table
            if '|' not in line or line.count('|') < 3:
                break  # Not a table line
            table_lines.append(line)
            i += 1
        
        lines_consumed = len(table_lines)
        
        if lines_consumed < 3:  # Need header + separator + at least one data row
            return lines[start_index], 1
        
        # Extract header
        header_line = table_lines[0]
        header_line = header_line.strip('|').strip()
        headers = [cell.strip() for cell in header_line.split('|')]
        
        # Skip separator line (index 1)
        
        # Extract data rows
        data_rows = []
        for row_line in table_lines[2:]:
            row_line = row_line.strip('|').strip()
            cells = [cell.strip() for cell in row_line.split('|')]
            
            # Ensure same number of cells as headers
            while len(cells) < len(headers):
                cells.append('')
            data_rows.append(cells[:len(headers)])
        
        # Generate HTML
        html_parts = ['<table>']
        html_parts.append('<thead>')
        html_parts.append('<tr>')
        for header in headers:
            html_parts.append(f'<th>{header}</th>')
        html_parts.append('</tr>')
        html_parts.append('</thead>')
        html_parts.append('<tbody>')
        for row in data_rows:
            html_parts.append('<tr>')
            for cell in row:
                html_parts.append(f'<td>{cell}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')
        html_parts.append('</table>')
        
        return '\n'.join(html_parts), lines_consumed
    
    def parse_markdown_table_with_count(self, lines, start_index):
        """Parse a markdown table and return HTML plus number of lines consumed"""
        table_lines = []
        
        # Collect all table lines
        i = start_index
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                break  # Empty line ends table
            if '|' not in line:
                break  # No pipe means end of table
            # Don't include lines that are clearly not table data
            if line.startswith('|---') and line.endswith('---|') and line.count('-') > 10:
                # This looks like a long separator, might not be a table
                break
            table_lines.append(line)
            i += 1
        
        lines_consumed = len(table_lines)
        
        if len(table_lines) < 3:  # Need header, separator, and at least one data row
            return lines[start_index], 1  # Return original line, consume only 1 line
        
        # Parse header - handle edge pipes properly
        header_line = table_lines[0]
        # Remove leading/trailing pipes if present
        if header_line.startswith('|'):
            header_line = header_line[1:]
        if header_line.endswith('|'):
            header_line = header_line[:-1]
        headers = [cell.strip() for cell in header_line.split('|')]
        
        # Verify this looks like a real table by checking the separator
        separator_line = table_lines[1]
        # More flexible separator validation - must contain dashes and/or pipes
        if not (('-' in separator_line or '|' in separator_line) and 
                re.match(r'^[\s\|\-\:]+$', separator_line.strip())):
            return lines[start_index], 1  # Not a valid table separator
        
        # Parse data rows (skip separator line at index 1)
        data_rows = []
        for row_line in table_lines[2:]:
            # Remove leading/trailing pipes if present
            if row_line.startswith('|'):
                row_line = row_line[1:]
            if row_line.endswith('|'):
                row_line = row_line[:-1]
            cells = [cell.strip() for cell in row_line.split('|')]
            
            # Ensure we have the same number of cells as headers
            while len(cells) < len(headers):
                cells.append('')
            data_rows.append(cells[:len(headers)])  # Truncate if too many cells
        
        # Generate HTML table only if we have valid data
        if not headers or not data_rows:
            return lines[start_index], 1
        
        html_parts = ['<table>']
        
        # Table header
        html_parts.append('<thead>')
        html_parts.append('<tr>')
        for header in headers:
            html_parts.append(f'<th>{header}</th>')
        html_parts.append('</tr>')
        html_parts.append('</thead>')
        
        # Table body
        html_parts.append('<tbody>')
        for row in data_rows:
            html_parts.append('<tr>')
            for cell in row:
                html_parts.append(f'<td>{cell}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')
        
        html_parts.append('</table>')
        
        return '\n'.join(html_parts), lines_consumed
    
    def parse_markdown_table(self, lines, start_index):
        """Parse a markdown table starting at start_index"""
        table_lines = []
        
        # Collect all table lines - be more careful about what constitutes a table line
        i = start_index
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                break  # Empty line ends table
            if '|' not in line:
                break  # No pipe means end of table
            # Skip lines that look like ASCII art
            if any(char in line for char in ['+']) or line.count('-') > line.count('|') * 2:
                break
            table_lines.append(line)
            i += 1
        
        if len(table_lines) < 2:
            return lines[start_index]  # Not a valid table, return original line
        
        # Parse header - handle edge pipes properly
        header_line = table_lines[0]
        # Remove leading/trailing pipes and split
        header_line = header_line.strip('|').strip()
        headers = [cell.strip() for cell in header_line.split('|')]
        
        # Skip separator line (table_lines[1]) and validate it
        if len(table_lines) < 3:
            return lines[start_index]  # Need at least header, separator, and one data row
        
        # Parse data rows
        data_rows = []
        for row_line in table_lines[2:]:
            # Remove leading/trailing pipes and split
            row_line = row_line.strip('|').strip()
            cells = [cell.strip() for cell in row_line.split('|')]
            
            # Ensure we have the same number of cells as headers
            while len(cells) < len(headers):
                cells.append('')
            data_rows.append(cells[:len(headers)])  # Truncate if too many cells
        
        # Generate HTML table only if we have valid data
        if not headers or not data_rows:
            return lines[start_index]
        
        html_parts = ['<table>']
        
        # Table header
        html_parts.append('<thead>')
        html_parts.append('<tr>')
        for header in headers:
            html_parts.append(f'<th>{header}</th>')
        html_parts.append('</tr>')
        html_parts.append('</thead>')
        
        # Table body
        html_parts.append('<tbody>')
        for row in data_rows:
            html_parts.append('<tr>')
            for cell in row:
                html_parts.append(f'<td>{cell}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')
        
        html_parts.append('</table>')
        
        return '\n'.join(html_parts)

def run_server(port=9876):
    """Run the HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, JUMPVisualizerHandler)
    
    print(f"Starting JUMP Discovery Visualizer server on port {port}")
    print(f"Visit: http://localhost:{port}/jump_discovery_visualizer.html")
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()

if __name__ == '__main__':
    import sys
    
    port = 9876
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number. Using default port 9876.")
    
    # Change to the directory containing the HTML file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    run_server(port)