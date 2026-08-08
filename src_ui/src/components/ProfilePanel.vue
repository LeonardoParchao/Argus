<template>
  <div class="profile-panel">
    <div class="panel-header">
      <h2>Profile Panel</h2>
    </div>
    
    <div class="panel-content">
      <!-- Selected Entity Details -->
      <div v-if="selectedEntity" class="entity-details">
        <h3>Selected Entity</h3>
        <div class="entity-info">
          <div class="info-row">
            <span class="label">Type:</span>
            <span class="value">{{ selectedEntity.type }}</span>
          </div>
          <div class="info-row">
            <span class="label">Value:</span>
            <span class="value">{{ selectedEntity.value }}</span>
          </div>
          <div class="info-row">
            <span class="label">Source:</span>
            <span class="value">{{ selectedEntity.source || 'N/A' }}</span>
          </div>
        </div>
      </div>
      
      <div v-else class="no-selection">
        <p>Select an entity from the graph to view details</p>
      </div>
      
      <!-- Profile Creation Form -->
      <div v-if="selectedEntity" class="profile-form">
        <h3>Create Profile</h3>
        <div class="form-group">
          <label for="profileName">Profile Name</label>
          <input
            id="profileName"
            v-model="profileName"
            type="text"
            class="form-input"
            placeholder="Enter profile name"
          />
        </div>
        
        <div class="form-group">
          <label for="profileNotes">Notes</label>
          <textarea
            id="profileNotes"
            v-model="profileNotes"
            class="form-textarea"
            placeholder="Add notes about this profile"
            rows="4"
          ></textarea>
        </div>
        
        <button 
          @click="handleSaveProfile" 
          class="save-button"
          :disabled="!profileName || isSaving"
        >
          {{ isSaving ? 'Saving...' : 'Save to Profile' }}
        </button>
      </div>
      
      <!-- Existing Profiles -->
      <div class="existing-profiles">
        <h3>Existing Profiles</h3>
        <div v-if="loadingProfiles" class="loading-text">
          Loading profiles...
        </div>
        <div v-else-if="profiles.length === 0" class="no-profiles">
          No profiles found
        </div>
        <div v-else class="profile-list">
          <div 
            v-for="profile in profiles" 
            :key="profile.id"
            class="profile-item"
          >
            <div class="profile-name">{{ profile.name }}</div>
            <div class="profile-notes">{{ profile.notes || 'No notes' }}</div>
            <button 
              @click="linkToProfile(profile.id)"
              class="link-button"
              :disabled="!selectedEntity"
            >
              Link Entity
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getProfiles, saveProfile, linkEntityToProfile } from '../api';

interface Entity {
  id: string;
  type: string;
  value: string;
  source?: string;
}

interface Profile {
  id: string;
  name: string;
  notes: string | null;
  created_at: string;
}

const props = defineProps<{
  selectedEntity: Entity | null;
}>();

const emit = defineEmits(['save-profile']);

const profileName = ref('');
const profileNotes = ref('');
const isSaving = ref(false);
const profiles = ref<Profile[]>([]);
const loadingProfiles = ref(false);

const loadProfiles = async () => {
  loadingProfiles.value = true;
  try {
    const response = await getProfiles();
    profiles.value = response.data.profiles;
  } catch (error) {
    console.error('Failed to load profiles:', error);
  } finally {
    loadingProfiles.value = false;
  }
};

const handleSaveProfile = async () => {
  if (!profileName.value.trim() || !props.selectedEntity) {
    return;
  }

  isSaving.value = true;
  try {
    const response = await saveProfile({
      name: profileName.value,
      notes: profileNotes.value || undefined,
      entity_ids: [props.selectedEntity.id]
    });
    
    emit('save-profile', response.data);
    
    // Reset form
    profileName.value = '';
    profileNotes.value = '';
    
    // Reload profiles
    await loadProfiles();
  } catch (error) {
    console.error('Failed to save profile:', error);
  } finally {
    isSaving.value = false;
  }
};

const linkToProfile = async (profileId: string) => {
  if (!props.selectedEntity) return;

  try {
    await linkEntityToProfile(profileId, props.selectedEntity.id);
    alert('Entity linked to profile successfully');
  } catch (error) {
    console.error('Failed to link entity:', error);
    alert('Failed to link entity to profile');
  }
};

onMounted(() => {
  loadProfiles();
});
</script>

<style scoped>
.profile-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  padding: 1rem;
  border-bottom: 1px solid #eee;
}

.panel-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #2c3e50;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.entity-details {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.entity-details h3 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  font-size: 1rem;
  color: #2c3e50;
}

.entity-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
}

.label {
  font-weight: 600;
  color: #555;
}

.value {
  color: #333;
  word-break: break-word;
  text-align: right;
}

.no-selection {
  text-align: center;
  color: #999;
  padding: 2rem;
  font-style: italic;
}

.profile-form {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.profile-form h3 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  font-size: 1rem;
  color: #2c3e50;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 600;
  color: #555;
  font-size: 0.875rem;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.875rem;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #3498db;
}

.save-button {
  width: 100%;
  padding: 0.75rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.save-button:hover:not(:disabled) {
  background-color: #2980b9;
}

.save-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.existing-profiles {
  margin-top: 1.5rem;
}

.existing-profiles h3 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  font-size: 1rem;
  color: #2c3e50;
}

.loading-text,
.no-profiles {
  text-align: center;
  color: #999;
  padding: 1rem;
}

.profile-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.profile-item {
  padding: 0.75rem;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.profile-name {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.profile-notes {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.5rem;
  font-style: italic;
}

.link-button {
  padding: 0.5rem 1rem;
  background-color: #2ecc71;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: background-color 0.2s;
}

.link-button:hover:not(:disabled) {
  background-color: #27ae60;
}

.link-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}
</style>
