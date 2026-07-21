/**
 * Automation Engine API service
 */
import api from './api';

// ─── Rules ────────────────────────────────────────────────────────────────
export const listRules = () => api.get('/automation/rules');
export const createRule = (data) => api.post('/automation/rules', data);
export const getRule = (id) => api.get(`/automation/rules/${id}`);
export const updateRule = (id, data) => api.patch(`/automation/rules/${id}`, data);
export const deleteRule = (id) => api.delete(`/automation/rules/${id}`);
export const enableRule = (id) => api.post(`/automation/rules/${id}/enable`);
export const disableRule = (id) => api.post(`/automation/rules/${id}/disable`);
export const manualRun = (id) => api.post(`/automation/rules/${id}/run`);

// ─── Tester ───────────────────────────────────────────────────────────────
export const testRule = (payload) => api.post('/automation/test', payload);

// ─── History ──────────────────────────────────────────────────────────────
export const listExecutions = (params = {}) => api.get('/automation/executions', { params });

// ─── Stats ────────────────────────────────────────────────────────────────
export const getStats = () => api.get('/automation/stats');

// ─── Metadata helpers (for UI dropdowns) ─────────────────────────────────

export const TRIGGER_OPTIONS = [
  { value: 'on_transaction', label: 'On Transaction Created' },
  { value: 'daily',          label: 'Daily (1 AM)' },
  { value: 'weekly',         label: 'Weekly (Mon 2 AM)' },
  { value: 'monthly',        label: 'Monthly (1st, 3 AM)' },
  { value: 'on_bill_due',    label: 'On Bill Due' },
  { value: 'on_goal_completed', label: 'On Goal Completed' },
];

export const FIELD_OPTIONS = [
  { value: 'description', label: 'Description / Merchant' },
  { value: 'amount',      label: 'Amount' },
  { value: 'type',        label: 'Transaction Type' },
  { value: 'category_id', label: 'Category' },
  { value: 'account_id',  label: 'Account' },
  { value: 'is_reviewed', label: 'Is Reviewed' },
  { value: 'is_archived', label: 'Is Archived' },
];

export const OPERATOR_OPTIONS = {
  description: [
    { value: 'contains',     label: 'contains' },
    { value: 'not_contains', label: 'does not contain' },
    { value: 'starts_with',  label: 'starts with' },
    { value: 'ends_with',    label: 'ends with' },
    { value: 'eq',           label: 'equals' },
    { value: 'neq',          label: 'not equals' },
    { value: 'is_empty',     label: 'is empty' },
    { value: 'is_not_empty', label: 'is not empty' },
  ],
  amount: [
    { value: 'gt',  label: '> greater than' },
    { value: 'gte', label: '>= at least' },
    { value: 'lt',  label: '< less than' },
    { value: 'lte', label: '<= at most' },
    { value: 'eq',  label: '= equals' },
    { value: 'neq', label: '≠ not equals' },
  ],
  type: [
    { value: 'eq',  label: 'equals' },
    { value: 'neq', label: 'not equals' },
  ],
  category_id: [
    { value: 'eq',  label: 'is' },
    { value: 'neq', label: 'is not' },
  ],
  account_id: [
    { value: 'eq',  label: 'is' },
    { value: 'neq', label: 'is not' },
  ],
  is_reviewed: [{ value: 'eq', label: 'equals' }],
  is_archived: [{ value: 'eq', label: 'equals' }],
};

export const ACTION_OPTIONS = [
  { value: 'assign_category',    label: 'Assign Category' },
  { value: 'assign_account',     label: 'Assign Account' },
  { value: 'notify',             label: 'Send Notification' },
  { value: 'contribute_to_goal', label: 'Contribute to Goal' },
  { value: 'mark_reviewed',      label: 'Mark as Reviewed' },
  { value: 'archive',            label: 'Archive Transaction' },
  { value: 'create_reminder',    label: 'Create Reminder' },
];
