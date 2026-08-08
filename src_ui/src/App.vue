<template>
  <div class="app-container">
    <header class="app-header">
      <h1>Argus OSINT Platform</h1>
    </header>
    
    <main class="app-main">
      <div class="search-section">
        <SearchBar @search="handleSearch" />
      </div>
      
      <div class="content-section">
        <div class="graph-section">
          <GraphView 
            @node-selected="handleNodeSelected"
            :search-results="searchResults"
          />
        </div>
        
        <div class="profile-section">
          <ProfilePanel 
            :selected-entity="selectedEntity"
            @save-profile="handleSaveProfile"
          />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import SearchBar from './components/SearchBar.vue';
import GraphView from './components/GraphView.vue';
import ProfilePanel from './components/ProfilePanel.vue';

interface SearchResult {
  target_type: string;
  target_value: string;
  search_results: any;
  entities_created: any[];
  relationships_created: any[];
}

interface Entity {
  id: string;
  type: string;
  value: string;
  source?: string;
}

const searchResults = ref<SearchResult | null>(null);
const selectedEntity = ref<Entity | null>(null);

const handleSearch = (results: SearchResult) => {
  searchResults.value = results;
};

const handleNodeSelected = (entity: Entity) => {
  selectedEntity.value = entity;
};

const handleSaveProfile = (profileData: any) => {
  console.log('Saving profile:', profileData);
  // Profile saving logic will be handled in ProfilePanel component
};
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
}

.app-header {
  background-color: #2c3e50;
  color: white;
  padding: 1rem 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.app-header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 1rem;
  overflow: hidden;
}

.search-section {
  margin-bottom: 1rem;
}

.content-section {
  flex: 1;
  display: flex;
  gap: 1rem;
  overflow: hidden;
}

.graph-section {
  flex: 2;
  min-width: 0;
}

.profile-section {
  flex: 1;
  min-width: 300px;
  max-width: 400px;
}
</style>
