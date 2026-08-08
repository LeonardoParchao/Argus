<template>
  <div class="search-bar">
    <div class="search-inputs">
      <select 
        v-model="targetType" 
        class="target-type-select"
        @change="handleTypeChange"
      >
        <option value="name">Name</option>
        <option value="email">Email</option>
        <option value="address">Address</option>
        <option value="website">Website</option>
        <option value="business">Business</option>
      </select>
      
      <input
        v-model="targetValue"
        type="text"
        class="target-value-input"
        :placeholder="getPlaceholder()"
        @keyup.enter="handleSearch"
      />
      
      <button 
        @click="handleSearch" 
        class="search-button"
        :disabled="isLoading || !targetValue"
      >
        {{ isLoading ? 'Searching...' : 'Search' }}
      </button>
    </div>
    
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { search } from '../api';

const emit = defineEmits(['search']);

const targetType = ref('name');
const targetValue = ref('');
const isLoading = ref(false);
const error = ref<string | null>(null);

const getPlaceholder = () => {
  const placeholders: Record<string, string> = {
    name: 'Enter person name',
    email: 'Enter email address',
    address: 'Enter physical address',
    website: 'Enter domain or URL',
    business: 'Enter business name'
  };
  return placeholders[targetType.value] || 'Enter search value';
};

const handleTypeChange = () => {
  targetValue.value = '';
  error.value = null;
};

const handleSearch = async () => {
  if (!targetValue.value.trim()) {
    error.value = 'Please enter a search value';
    return;
  }

  isLoading.value = true;
  error.value = null;

  try {
    const response = await search(targetType.value, targetValue.value);
    emit('search', response.data);
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Search failed. Please try again.';
    console.error('Search error:', err);
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.search-bar {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.search-inputs {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.target-type-select {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  min-width: 150px;
  background-color: white;
  cursor: pointer;
}

.target-value-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.target-value-input:focus {
  outline: none;
  border-color: #3498db;
}

.search-button {
  padding: 0.75rem 1.5rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.search-button:hover:not(:disabled) {
  background-color: #2980b9;
}

.search-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.error-message {
  margin-top: 0.5rem;
  color: #e74c3c;
  font-size: 0.875rem;
}
</style>
