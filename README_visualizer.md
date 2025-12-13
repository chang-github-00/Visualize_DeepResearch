# JUMP Discovery Visualizer

An interactive web-based visualization tool for exploring JUMP Cell Painting discovery research results.

## Features

- **Interactive Network Graph**: Explore research attempts as connected nodes radiating from a central "JUMP Research" hub
- **Gene-focused Visualization**: Each attempt node represents a specific gene hypothesis study
- **Comprehensive Evidence Display**: Click on nodes to view evidence figures and detailed research reports
- **Automatic Data Detection**: Dynamically scans and loads attempt folders from the JUMPDiscovery_results directory
- **Responsive Design**: Modern, scientific interface with dark theme inspired by the reference image

## Quick Start

1. **Start the server**:
   ```bash
   python3 server.py
   ```
   
2. **Open in browser**:
   Visit `http://localhost:9876/jump_discovery_visualizer.html`

3. **Explore the data**:
   - Click on the central "JUMP Research" node for an overview
   - Click on any gene node to view detailed research findings
   - Use mouse to drag nodes and zoom/pan the visualization
   - Click on evidence images to view them in full size

## File Structure

```
Visualize_DeepResearch/
├── jump_discovery_visualizer.html  # Main visualization interface
├── server.py                       # Python backend server
├── README_visualizer.md           # This documentation
└── JUMPDiscovery_results/         # Data directory (auto-detected)
    ├── attempt_10/                # Individual research attempts
    ├── attempt_11/
    └── ...
```

## How It Works

### Data Detection
The system automatically:
1. Scans the `JUMPDiscovery_results` directory for attempt folders
2. Extracts gene names from report filenames (pattern: `report_GENENAME_*.md`)
3. Finds comprehensive evidence figures (`*comprehensive*.png`)
4. Maps attempt IDs to gene names and metadata

### Network Visualization
- **Central Node**: "JUMP Research" hub (golden, larger)
- **Attempt Nodes**: Individual gene studies (color-coded by gene name)
- **Interactive Elements**: Click, drag, hover effects
- **Dynamic Layout**: Force-directed positioning with collision detection

### Evidence Display
When clicking on a gene node, the sidebar shows:
- Gene name and attempt details
- Comprehensive evidence figures (if available)
- Link to the full markdown research report
- Automatic image loading with fallbacks

## Controls

- **Reset View**: Return to default layout
- **Toggle Labels**: Show/hide node labels
- **Node Interaction**: Click to select, drag to reposition
- **Image Modal**: Click evidence images for full-size view

## Requirements

- Python 3.6+
- Modern web browser with JavaScript enabled
- Local file system access to JUMPDiscovery_results directory

## Data Format

The visualizer expects the following directory structure:

```
JUMPDiscovery_results/
├── attempt_N/
│   ├── report_GENENAME_*.md           # Main research report
│   ├── GENENAME_comprehensive*.png    # Evidence figures
│   ├── GENENAME_analysis.png          # Additional figures
│   └── ...
```

## API Endpoints

The Python server provides:
- `GET /api/attempts` - List all research attempts
- `GET /api/attempt/{id}` - Detailed information for specific attempt

## Customization

### Styling
Modify CSS variables in the `<style>` section to adjust:
- Color schemes
- Node sizes
- Animation speeds
- Layout parameters

### Data Processing
Edit `server.py` to customize:
- Gene name extraction patterns
- Figure detection logic
- Report parsing methods
- API response format

## Troubleshooting

**Port conflicts**: Use `python3 server.py 8080` to specify different port (default is 9876)

**Missing images**: Check file paths and permissions in JUMPDiscovery_results

**Gene names not detected**: Verify report filenames follow the pattern `report_GENENAME_*.md`

**Performance issues**: Large datasets may require adjusting force simulation parameters