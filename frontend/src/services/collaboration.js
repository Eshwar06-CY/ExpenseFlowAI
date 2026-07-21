/**
 * Collaboration API service — Workspaces, Members, Comments, Audit Log
 */
import api from './api';

// ─── Workspaces ────────────────────────────────────────────────────────────

export const listWorkspaces = () => api.get('/workspaces/');
export const createWorkspace = (data) => api.post('/workspaces/', data);
export const getWorkspace = (id) => api.get(`/workspaces/${id}`);
export const updateWorkspace = (id, data) => api.patch(`/workspaces/${id}`, data);
export const deleteWorkspace = (id) => api.delete(`/workspaces/${id}`);

// ─── Members ───────────────────────────────────────────────────────────────

export const listMembers = (workspaceId) => api.get(`/workspaces/${workspaceId}/members`);
export const inviteMember = (workspaceId, data) => api.post(`/workspaces/${workspaceId}/members/invite`, data);
export const acceptInvitation = (workspaceId) => api.post(`/workspaces/${workspaceId}/members/accept`);
export const declineInvitation = (workspaceId) => api.post(`/workspaces/${workspaceId}/members/decline`);
export const updateMemberRole = (workspaceId, userId, data) => api.patch(`/workspaces/${workspaceId}/members/${userId}`, data);
export const removeMember = (workspaceId, userId) => api.delete(`/workspaces/${workspaceId}/members/${userId}`);
export const leaveWorkspace = (workspaceId) => api.post(`/workspaces/${workspaceId}/leave`);
export const transferOwnership = (workspaceId, newOwnerId) => api.post(`/workspaces/${workspaceId}/transfer/${newOwnerId}`);

// ─── Invitations ───────────────────────────────────────────────────────────

export const listPendingInvitations = () => api.get('/workspaces/invitations');

// ─── Comments ──────────────────────────────────────────────────────────────

export const getComments = (workspaceId, entityType, entityId) =>
  api.get(`/workspaces/${workspaceId}/comments`, { params: { entity_type: entityType, entity_id: entityId } });

export const addComment = (workspaceId, data) => api.post(`/workspaces/${workspaceId}/comments`, data);

export const deleteComment = (workspaceId, commentId) => api.delete(`/workspaces/${workspaceId}/comments/${commentId}`);

// ─── Audit Log ─────────────────────────────────────────────────────────────

export const getAuditLog = (workspaceId, params = {}) =>
  api.get(`/workspaces/${workspaceId}/audit-log`, { params });
