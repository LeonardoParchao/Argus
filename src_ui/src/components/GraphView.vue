<template>
  <div class="graph-view">
    <div class="graph-header">
      <h2>Relationship Graph</h2>
      <button @click="refreshGraph" class="refresh-button">Refresh</button>
    </div>
    <div ref="cyContainer" class="cytoscape-container"></div>
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">Loading graph...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import cytoscape from 'cytoscape';
import { getGraph } from '../api';

const emit = defineEmits(['node-selected']);

const cyContainer = ref<HTMLElement | null>(null);
const loading = ref(false);
let cy: any = null;

const refreshGraph = async () => {
  loading.value = true;
  try {
    const response = await getGraph();
    const graphData = response.data;
    initializeCytoscape(graphData);
  } catch (error) {
    console.error('Failed to load graph:', error);
  } finally {
    loading.value = false;
  }
};

const initializeCytoscape = (graphData: any) => {
  if (!cyContainer.value) return;

  if (cy) {
    cy.destroy();
  }

  cy = cytoscape({
    container: cyContainer.value,
    elements: {
      nodes: graphData.nodes || [],
      edges: graphData.edges || []
    },
    style: [
      {
        selector: 'node',
        style: {
          'background-color': '#666',
          'label': 'data(label)',
          'font-size': '12px',
          'text-valign': 'center',
          'text-halign': 'center',
          'width': '30px',
          'height': '30px',
          'border-width': 2,
          'border-color': '#333',
          'text-wrap': 'wrap',
          'text-max-width': '80px'
        }
      },
      {
        selector: 'node[type="name"]',
        style: {
          'background-color': '#3498db',
          'border-color': '#2980b9'
        }
      },
      {
        selector: 'node[type="email"]',
        style: {
          'background-color': '#e74c3c',
          'border-color': '#c0392b'
        }
      },
      {
        selector: 'node[type="address"]',
        style: {
          'background-color': '#2ecc71',
          'border-color': '#27ae60'
        }
      },
      {
        selector: 'node[type="website"]',
        style: {
          'background-color': '#9b59b6',
          'border-color': '#8e44ad'
        }
      },
      {
        selector: 'node[type="business"]',
        style: {
          'background-color': '#f39c12',
          'border-color': '#d68910'
        }
      },
      {
        selector: 'node[type="service"]',
        style: {
          'background-color': '#1abc9c',
          'border-color': '#16a085'
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 2,
          'line-color': '#ccc',
          'target-arrow-color': '#ccc',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier'
        }
      },
      {
        selector: 'edge[label]',
        style: {
          'label': 'data(label)',
          'font-size': '10px',
          'text-rotation': 'autorotate',
          'text-margin-y': -10,
          'text-background-color': '#fff',
          'text-background-opacity': 0.8,
          'text-background-padding': '2px'
        }
      },
      {
        selector: 'node:selected',
        style: {
          'border-width': 4,
          'border-color': '#ff0000'
        }
      },
      {
        selector: 'edge:selected',
        style: {
          'line-color': '#ff0000',
          'target-arrow-color': '#ff0000'
        }
      }
    ],
    layout: {
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
    }
  });

  // Add click event to emit selected node
  cy.on('tap', 'node', (evt: any) => {
    const node = evt.target;
    const data = node.data();
    emit('node-selected', {
      id: data.id,
      type: data.type,
      value: data.value,
      source: data.source
    });
  });

  // Enable zoom and pan
  cy.minZoom(0.1);
  cy.maxZoom(5);
};

onMounted(() => {
  refreshGraph();
});

onUnmounted(() => {
  if (cy) {
    cy.destroy();
  }
});
</script>

<style scoped>
.graph-view {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #eee;
}

.graph-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #2c3e50;
}

.refresh-button {
  padding: 0.5rem 1rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.refresh-button:hover {
  background-color: #2980b9;
}

.cytoscape-container {
  flex: 1;
  width: 100%;
  min-height: 400px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.loading-spinner {
  padding: 1rem 2rem;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
</style>
