import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import database
from typing import Dict
import json


def build_cytoscape_json() -> Dict:
    """
    Fetch nodes and edges from SQLite.
    Map to Cytoscape.js elements format: { data: { id: '...', label: '...' } }.
    """
    # Initialize database if needed
    database.init_db()
    
    # Get graph data from database
    graph_data = database.get_graph_data()
    
    # Format for Cytoscape.js
    cytoscape_elements = {
        "nodes": graph_data["nodes"],
        "edges": graph_data["edges"]
    }
    
    return cytoscape_elements


def generate_interactive_html() -> str:
    """
    Generate a standalone HTML file embedding Cytoscape.js for CLI usage.
    """
    # Get graph data
    graph_data = build_cytoscape_json()
    
    # Generate HTML with embedded Cytoscape.js
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>Argus OSINT Graph</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        #cy {{
            width: 100%;
            height: 800px;
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 4px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .stats {{
            text-align: center;
            margin-bottom: 20px;
            color: #666;
        }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
</head>
<body>
    <div class="header">
        <h1>Argus OSINT Graph Visualization</h1>
    </div>
    <div class="stats">
        <span id="nodeCount">0</span> nodes | <span id="edgeCount">0</span> edges
    </div>
    <div id="cy"></div>
    <script>
        // Graph data from database
        const graphData = {json.dumps(graph_data)};

        // Update stats
        document.getElementById('nodeCount').textContent = graphData.nodes.length;
        document.getElementById('edgeCount').textContent = graphData.edges.length;

        // Initialize Cytoscape
        const cy = cytoscape({{
            container: document.getElementById('cy'),
            elements: {{
                nodes: graphData.nodes,
                edges: graphData.edges
            }},
            style: [
                {{
                    selector: 'node',
                    style: {{
                        'background-color': '#666',
                        'label': 'data(label)',
                        'font-size': '12px',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'width': '30px',
                        'height': '30px',
                        'border-width': 2,
                        'border-color': '#333'
                    }}
                }},
                {{
                    selector: 'node[type="name"]',
                    style: {{
                        'background-color': '#3498db',
                        'border-color': '#2980b9'
                    }}
                }},
                {{
                    selector: 'node[type="email"]',
                    style: {{
                        'background-color': '#e74c3c',
                        'border-color': '#c0392b'
                    }}
                }},
                {{
                    selector: 'node[type="address"]',
                    style: {{
                        'background-color': '#2ecc71',
                        'border-color': '#27ae60'
                    }}
                }},
                {{
                    selector: 'node[type="website"]',
                    style: {{
                        'background-color': '#9b59b6',
                        'border-color': '#8e44ad'
                    }}
                }},
                {{
                    selector: 'node[type="business"]',
                    style: {{
                        'background-color': '#f39c12',
                        'border-color': '#d68910'
                    }}
                }},
                {{
                    selector: 'node[type="service"]',
                    style: {{
                        'background-color': '#1abc9c',
                        'border-color': '#16a085'
                    }}
                }},
                {{
                    selector: 'edge',
                    style: {{
                        'width': 2,
                        'line-color': '#ccc',
                        'target-arrow-color': '#ccc',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier'
                    }}
                }},
                {{
                    selector: 'edge[label]',
                    style: {{
                        'label': 'data(label)',
                        'font-size': '10px',
                        'text-rotation': 'autorotate',
                        'text-margin-y': -10
                    }}
                }},
                {{
                    selector: 'node:selected',
                    style: {{
                        'border-width': 4,
                        'border-color': '#ff0000'
                    }}
                }}
            ],
            layout: {{
                name: 'cose',
                animate: false,
                nodeRepulsion: 1000,
                nodeOverlap: 20,
                idealEdgeLength: 100,
                edgeElasticity: 100,
                nestingFactor: 5,
                gravity: 80,
                numIter: 1000,
                initialTemp: 200,
                coolingFactor: 0.95,
                minTemp: 1.0
            }}
        }});

        // Add click event to show node details
        cy.on('tap', 'node', function(evt) {{
            const node = evt.target;
            const data = node.data();
            console.log('Node clicked:', data);
            
            // Create a simple alert with node details
            const details = `Type: ${{data.type}}\\nValue: ${{data.value}}\\nSource: ${{data.source || 'N/A'}}`;
            alert(details);
        }});

        // Enable zoom and pan
        cy.minZoom(0.1);
        cy.maxZoom(5);
    </script>
</body>
</html>"""
    
    return html_template
