import axios from 'axios';

const API_BASE = '/api';

export async function search(target_type: string, target_value: string) {
  return axios.post(`${API_BASE}/search`, {
    target_type,
    target_value
  });
}

export async function getGraph() {
  return axios.get(`${API_BASE}/graph`);
}

export async function saveProfile(data: { name: string; notes?: string; entity_ids?: string[] }) {
  return axios.post(`${API_BASE}/profiles`, data);
}

export async function getProfiles() {
  return axios.get(`${API_BASE}/profiles`);
}

export async function getProfile(profileId: string) {
  return axios.get(`${API_BASE}/profiles/${profileId}`);
}

export async function linkEntityToProfile(profileId: string, entityId: string) {
  return axios.post(`${API_BASE}/profiles/${profileId}/entities`, {
    entity_id: entityId
  });
}

export async function getEntity(entityId: string) {
  return axios.get(`${API_BASE}/entities/${entityId}`);
}
