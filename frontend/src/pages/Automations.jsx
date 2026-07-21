import React, { useState, useEffect, useCallback } from 'react';
import {
  Zap, Plus, Play, Pause, Trash2, Edit3, CheckCircle2,
  XCircle, Clock, AlertTriangle, Activity, BarChart3,
  ChevronRight, ChevronDown, FlaskConical, Settings,
  ArrowRight, Filter, RefreshCw, Eye
} from 'lucide-react';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import ConfirmDialog from '../components/Common/ConfirmDialog';
import { useToast } from '../context/ToastContext';
import * as auto from '../services/automation';
import api from '../services/api';

// ─── Constants & helpers ──────────────────────────────────────────────────

const STATUS_META = {
  success: { color: '#10b981', icon: CheckCircle2, label: 'Success' },
  failed:  { color: '#ef4444', icon: XCircle,      label: 'Failed'  },
  skipped: { color: '#f59e0b', icon: Clock,         label: 'Skipped' },
};

const TRIGGER_LABELS = Object.fromEntries(auto.TRIGGER_OPTIONS.map(t => [t.value, t.label]));

function StatCard({ label, value, icon: Icon, color = 'var(--primary)' }) {
  return (
    <div style={{
      background: 'var(--card-bg)', border: '1px solid var(--border)',
      borderRadius: 14, padding: '18px 20px',
      display: 'flex', alignItems: 'center', gap: 14
    }}>
      <div style={{
        width: 44, height: 44, borderRadius: 12, flexShrink: 0,
        background: `color-mix(in srgb, ${color} 15%, transparent)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center'
      }}>
        <Icon size={20} color={color} />
      </div>
      <div>
        <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--text)' }}>{value ?? 0}</div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{label}</div>
      </div>
    </div>
  );
}

// ─── Condition Row ────────────────────────────────────────────────────────

function ConditionRow({ condition, index, categories, accounts, onChange, onRemove }) {
  const field = condition.field || 'description';
  const operators = auto.OPERATOR_OPTIONS[field] || auto.OPERATOR_OPTIONS.description;
  const needsValue = !['is_empty', 'is_not_empty'].includes(condition.operator);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
      <select value={field} onChange={e => onChange(index, { ...condition, field: e.target.value, operator: 'contains', value: '' })}
        style={selectStyle}>
        {auto.FIELD_OPTIONS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
      </select>

      <select value={condition.operator || 'contains'} onChange={e => onChange(index, { ...condition, operator: e.target.value })}
        style={selectStyle}>
        {operators.map(op => <option key={op.value} value={op.value}>{op.label}</option>)}
      </select>

      {needsValue && field === 'type' && (
        <select value={condition.value || ''} onChange={e => onChange(index, { ...condition, value: e.target.value })} style={selectStyle}>
          <option value="">— select —</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
          <option value="transfer">Transfer</option>
        </select>
      )}
      {needsValue && field === 'category_id' && (
        <select value={condition.value || ''} onChange={e => onChange(index, { ...condition, value: parseInt(e.target.value) || '' })} style={selectStyle}>
          <option value="">— any —</option>
          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      )}
      {needsValue && field === 'account_id' && (
        <select value={condition.value || ''} onChange={e => onChange(index, { ...condition, value: parseInt(e.target.value) || '' })} style={selectStyle}>
          <option value="">— any —</option>
          {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
        </select>
      )}
      {needsValue && !['type', 'category_id', 'account_id'].includes(field) && (
        <input value={condition.value || ''} onChange={e => onChange(index, { ...condition, value: e.target.value })}
          placeholder="value…"
          style={{ ...inputStyle, width: 120 }} />
      )}
      <button onClick={() => onRemove(index)} style={iconBtnStyle}><Trash2 size={13} /></button>
    </div>
  );
}

// ─── Action Row ───────────────────────────────────────────────────────────

function ActionRow({ action, index, categories, accounts, goals, onChange, onRemove }) {
  const type = action.type || 'assign_category';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
      <select value={type} onChange={e => onChange(index, { type: e.target.value })} style={selectStyle}>
        {auto.ACTION_OPTIONS.map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
      </select>

      {type === 'assign_category' && (
        <select value={action.category_id || ''} onChange={e => onChange(index, { ...action, category_id: parseInt(e.target.value) || null })} style={selectStyle}>
          <option value="">— pick category —</option>
          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      )}
      {type === 'assign_account' && (
        <select value={action.account_id || ''} onChange={e => onChange(index, { ...action, account_id: parseInt(e.target.value) || null })} style={selectStyle}>
          <option value="">— pick account —</option>
          {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
        </select>
      )}
      {(type === 'notify' || type === 'create_reminder') && (
        <>
          <input value={action.title || ''} onChange={e => onChange(index, { ...action, title: e.target.value })}
            placeholder="Title" style={{ ...inputStyle, width: 130 }} />
          <input value={action.message || ''} onChange={e => onChange(index, { ...action, message: e.target.value })}
            placeholder="Message" style={{ ...inputStyle, width: 180 }} />
        </>
      )}
      {type === 'contribute_to_goal' && (
        <>
          <select value={action.goal_id || ''} onChange={e => onChange(index, { ...action, goal_id: parseInt(e.target.value) || null })} style={selectStyle}>
            <option value="">— pick goal —</option>
            {goals.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
          </select>
          <input value={action.percent || ''} onChange={e => onChange(index, { ...action, percent: parseFloat(e.target.value) || null })}
            placeholder="% of amount" type="number" min="0" max="100" style={{ ...inputStyle, width: 100 }} />
        </>
      )}
      <button onClick={() => onRemove(index)} style={iconBtnStyle}><Trash2 size={13} /></button>
    </div>
  );
}

// ─── Shared Styles ────────────────────────────────────────────────────────

const selectStyle = {
  padding: '6px 10px', borderRadius: 8, border: '1px solid var(--border)',
  background: 'var(--input-bg)', color: 'var(--text)', fontSize: 13, cursor: 'pointer'
};
const inputStyle = {
  padding: '6px 10px', borderRadius: 8, border: '1px solid var(--border)',
  background: 'var(--input-bg)', color: 'var(--text)', fontSize: 13
};
const iconBtnStyle = {
  background: 'rgba(239,68,68,0.1)', border: 'none', cursor: 'pointer',
  color: '#ef4444', padding: '5px 8px', borderRadius: 6,
  display: 'flex', alignItems: 'center'
};

// ─── Rule Builder Modal ───────────────────────────────────────────────────

function RuleModal({ rule, categories, accounts, goals, onSave, onClose }) {
  const [name, setName] = useState(rule?.name || '');
  const [desc, setDesc] = useState(rule?.description || '');
  const [trigger, setTrigger] = useState(rule?.trigger || 'on_transaction');
  const [logic, setLogic] = useState(rule?.condition_logic || 'AND');
  const [priority, setPriority] = useState(rule?.priority ?? 100);
  const [conditions, setConditions] = useState(rule?.conditions || []);
  const [actions, setActions] = useState(rule?.actions || []);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const { addToast } = useToast();

  const addCondition = () => setConditions(prev => [...prev, { field: 'description', operator: 'contains', value: '' }]);
  const removeCondition = (i) => setConditions(prev => prev.filter((_, idx) => idx !== i));
  const updateCondition = (i, c) => setConditions(prev => prev.map((x, idx) => idx === i ? c : x));

  const addAction = () => setActions(prev => [...prev, { type: 'assign_category' }]);
  const removeAction = (i) => setActions(prev => prev.filter((_, idx) => idx !== i));
  const updateAction = (i, a) => setActions(prev => prev.map((x, idx) => idx === i ? a : x));

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await auto.testRule({ conditions, actions, condition_logic: logic, limit: 10 });
      setTestResult(res.data);
    } catch {
      addToast('Test failed.', 'error');
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!name.trim()) { addToast('Rule name is required.', 'error'); return; }
    if (actions.length === 0) { addToast('Add at least one action.', 'error'); return; }
    setSaving(true);
    try {
      await onSave({ name, description: desc || null, trigger, condition_logic: logic, priority, conditions, actions });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 16
    }}>
      <div style={{
        background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 20,
        width: '100%', maxWidth: 700, maxHeight: '90vh', overflowY: 'auto',
        boxShadow: '0 32px 80px rgba(0,0,0,0.5)'
      }}>
        <div style={{ padding: '24px 28px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>
            {rule ? 'Edit Rule' : 'New Automation Rule'}
          </h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>✕</button>
        </div>

        <div style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: 22 }}>
          {/* Basic info */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <div>
              <label style={labelStyle}>Rule Name *</label>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Auto-categorize Uber"
                style={{ ...inputStyle, width: '100%', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={labelStyle}>Trigger</label>
              <select value={trigger} onChange={e => setTrigger(e.target.value)} style={{ ...selectStyle, width: '100%' }}>
                {auto.TRIGGER_OPTIONS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 14 }}>
            <div>
              <label style={labelStyle}>Description</label>
              <input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Optional description…"
                style={{ ...inputStyle, width: '100%', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={labelStyle}>Priority</label>
              <input type="number" value={priority} onChange={e => setPriority(parseInt(e.target.value) || 100)}
                style={{ ...inputStyle, width: 80 }} min={1} max={999} />
            </div>
          </div>

          {/* Conditions */}
          <div style={{ background: 'rgba(99,102,241,0.05)', borderRadius: 12, padding: 16, border: '1px solid rgba(99,102,241,0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontWeight: 700, fontSize: 14 }}>IF</span>
                <select value={logic} onChange={e => setLogic(e.target.value)} style={{ ...selectStyle, padding: '3px 8px', fontSize: 12 }}>
                  <option value="AND">ALL conditions match (AND)</option>
                  <option value="OR">ANY condition matches (OR)</option>
                </select>
              </div>
              <Button onClick={addCondition} variant="ghost" style={{ fontSize: 12, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 4 }}>
                <Plus size={12} /> Add Condition
              </Button>
            </div>
            {conditions.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: 13, fontStyle: 'italic' }}>
                No conditions — rule will match every transaction.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {conditions.map((c, i) => (
                  <ConditionRow key={i} condition={c} index={i} categories={categories} accounts={accounts}
                    onChange={updateCondition} onRemove={removeCondition} />
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div style={{ background: 'rgba(16,185,129,0.05)', borderRadius: 12, padding: 16, border: '1px solid rgba(16,185,129,0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontWeight: 700, fontSize: 14 }}>THEN</span>
              <Button onClick={addAction} variant="ghost" style={{ fontSize: 12, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 4 }}>
                <Plus size={12} /> Add Action
              </Button>
            </div>
            {actions.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: 13, fontStyle: 'italic' }}>Add at least one action.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {actions.map((a, i) => (
                  <ActionRow key={i} action={a} index={i} categories={categories} accounts={accounts} goals={goals}
                    onChange={updateAction} onRemove={removeAction} />
                ))}
              </div>
            )}
          </div>

          {/* Test panel */}
          <div style={{ background: 'rgba(245,158,11,0.05)', borderRadius: 12, padding: 16, border: '1px solid rgba(245,158,11,0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontWeight: 700, fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                <FlaskConical size={15} /> Rule Tester (dry run)
              </span>
              <Button onClick={handleTest} variant="ghost" disabled={testing}
                style={{ fontSize: 12, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 4 }}>
                {testing ? <RefreshCw size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={12} />}
                {testing ? 'Testing…' : 'Test Now'}
              </Button>
            </div>
            {testResult && (
              <div style={{ fontSize: 13 }}>
                <div style={{ color: testResult.matched_count > 0 ? '#10b981' : 'var(--text-muted)', marginBottom: 6, fontWeight: 600 }}>
                  {testResult.matched_count} transaction(s) would match.
                </div>
                {testResult.would_execute_actions.length > 0 && (
                  <div style={{ color: 'var(--text-muted)', marginBottom: 8 }}>
                    Actions: {testResult.would_execute_actions.join(', ')}
                  </div>
                )}
                {testResult.sample_transactions.slice(0, 3).map(tx => (
                  <div key={tx.id} style={{ padding: '6px 10px', background: 'var(--card-bg)', borderRadius: 8, marginBottom: 4, fontSize: 12, display: 'flex', justifyContent: 'space-between' }}>
                    <span>{tx.description || '(no description)'}</span>
                    <span style={{ fontWeight: 600 }}>₹{tx.amount?.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div style={{ padding: '16px 28px', borderTop: '1px solid var(--border)', display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button variant="primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : rule ? 'Update Rule' : 'Create Rule'}
          </Button>
        </div>
      </div>
    </div>
  );
}

const labelStyle = { fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 5 };

// ─── Rule Card ────────────────────────────────────────────────────────────

function RuleCard({ rule, onEdit, onToggle, onDelete, onRun }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div style={{
      background: 'var(--card-bg)', border: `1.5px solid ${rule.is_enabled ? 'var(--border)' : 'rgba(100,116,139,0.3)'}`,
      borderRadius: 14, overflow: 'hidden',
      opacity: rule.is_enabled ? 1 : 0.6,
      transition: 'opacity 0.2s'
    }}>
      <div style={{ padding: '14px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 0 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 9, flexShrink: 0,
            background: rule.is_enabled ? 'linear-gradient(135deg,var(--primary),var(--purple))' : 'var(--border)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Zap size={16} color={rule.is_enabled ? '#fff' : 'var(--text-muted)'} />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 8 }}>
              {rule.name}
              <span style={{ fontSize: 11, padding: '1px 6px', borderRadius: 4, background: 'rgba(99,102,241,0.12)', color: 'var(--primary)', fontWeight: 600 }}>
                {TRIGGER_LABELS[rule.trigger] || rule.trigger}
              </span>
            </div>
            {rule.description && (
              <div style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {rule.description}
              </div>
            )}
            <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 3 }}>
              Runs: {rule.run_count} • Priority: {rule.priority} • {rule.conditions.length} condition{rule.conditions.length !== 1 ? 's' : ''} → {rule.actions.length} action{rule.actions.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 5, flexShrink: 0 }}>
          {rule.trigger !== 'on_transaction' && (
            <button onClick={() => onRun(rule)} title="Run now"
              style={{ ...iconBtnStyle, background: 'rgba(16,185,129,0.1)', color: '#10b981' }}>
              <Play size={13} />
            </button>
          )}
          <button onClick={() => onEdit(rule)} title="Edit"
            style={{ ...iconBtnStyle, background: 'rgba(99,102,241,0.1)', color: 'var(--primary)' }}>
            <Edit3 size={13} />
          </button>
          <button onClick={() => onToggle(rule)} title={rule.is_enabled ? 'Disable' : 'Enable'}
            style={{ ...iconBtnStyle, background: rule.is_enabled ? 'rgba(245,158,11,0.1)' : 'rgba(16,185,129,0.1)', color: rule.is_enabled ? '#f59e0b' : '#10b981' }}>
            {rule.is_enabled ? <Pause size={13} /> : <Play size={13} />}
          </button>
          <button onClick={() => onDelete(rule)} title="Delete"
            style={{ ...iconBtnStyle }}>
            <Trash2 size={13} />
          </button>
          <button onClick={() => setExpanded(x => !x)} style={{ ...iconBtnStyle, background: 'var(--card-bg)', color: 'var(--text-muted)' }}>
            {expanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
          </button>
        </div>
      </div>

      {expanded && (
        <div style={{ borderTop: '1px solid var(--border)', padding: '12px 18px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase' }}>
              IF ({rule.condition_logic})
            </div>
            {rule.conditions.length === 0 ? (
              <div style={{ fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic' }}>Always matches</div>
            ) : (
              rule.conditions.map((c, i) => (
                <div key={i} style={{ fontSize: 12, color: 'var(--text)', marginBottom: 3 }}>
                  • {c.field} <span style={{ color: 'var(--text-muted)' }}>{c.operator}</span> <strong>{String(c.value)}</strong>
                </div>
              ))
            )}
          </div>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase' }}>THEN</div>
            {rule.actions.map((a, i) => (
              <div key={i} style={{ fontSize: 12, color: 'var(--text)', marginBottom: 3 }}>
                • {auto.ACTION_OPTIONS.find(x => x.value === a.type)?.label || a.type}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Execution Row ────────────────────────────────────────────────────────

function ExecRow({ exec }) {
  const meta = STATUS_META[exec.status] || STATUS_META.skipped;
  const Icon = meta.icon;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
      <Icon size={16} color={meta.color} style={{ flexShrink: 0 }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{exec.rule_name || `Rule #${exec.rule_id}`}</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{exec.result_summary}</div>
      </div>
      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div style={{ fontSize: 11, color: meta.color, fontWeight: 600 }}>{meta.label}</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{exec.duration_ms}ms</div>
        <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{exec.executed_at ? new Date(exec.executed_at).toLocaleString() : ''}</div>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────

export default function Automations() {
  const { addToast } = useToast();
  const showToast = (msg, type) => addToast(msg, type);

  const [rules, setRules] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [stats, setStats] = useState(null);
  const [categories, setCategories] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('rules'); // rules | history
  const [statusFilter, setStatusFilter] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [confirmDlg, setConfirmDlg] = useState({ open: false });

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [rRes, eRes, sRes, cRes, aRes, gRes] = await Promise.all([
        auto.listRules(),
        auto.listExecutions({ limit: 30 }),
        auto.getStats(),
        api.get('/categories'),
        api.get('/accounts'),
        api.get('/goals/'),
      ]);
      setRules(rRes.data);
      setExecutions(eRes.data);
      setStats(sRes.data);
      setCategories(cRes.data);
      setAccounts(aRes.data);
      setGoals(gRes.data);
    } catch {
      showToast('Failed to load automation data.', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, []);

  const loadExecFiltered = async (status) => {
    setStatusFilter(status);
    try {
      const res = await auto.listExecutions({ limit: 50, status: status || undefined });
      setExecutions(res.data);
    } catch { showToast('Failed to load executions.', 'error'); }
  };

  const handleSave = async (data) => {
    try {
      if (editingRule) {
        await auto.updateRule(editingRule.id, data);
        showToast('Rule updated!', 'success');
      } else {
        await auto.createRule(data);
        showToast('Rule created!', 'success');
      }
      setShowModal(false);
      setEditingRule(null);
      load();
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to save rule.', 'error');
    }
  };

  const handleToggle = async (rule) => {
    try {
      if (rule.is_enabled) {
        await auto.disableRule(rule.id);
        showToast(`"${rule.name}" disabled.`, 'info');
      } else {
        await auto.enableRule(rule.id);
        showToast(`"${rule.name}" enabled.`, 'success');
      }
      load();
    } catch {
      showToast('Failed to toggle rule.', 'error');
    }
  };

  const handleDelete = (rule) => {
    setConfirmDlg({
      open: true, danger: true,
      title: 'Delete Rule',
      message: `Permanently delete "${rule.name}"? Execution history will also be removed.`,
      onConfirm: async () => {
        try {
          await auto.deleteRule(rule.id);
          showToast('Rule deleted.', 'success');
          load();
        } catch { showToast('Failed to delete rule.', 'error'); }
        setConfirmDlg({ open: false });
      }
    });
  };

  const handleRun = async (rule) => {
    try {
      const res = await auto.manualRun(rule.id);
      showToast(res.data.message || 'Rule executed.', 'success');
      load();
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to run rule.', 'error');
    }
  };

  return (
    <div style={{ padding: '24px 28px', maxWidth: 1100, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 800, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 10 }}>
            <Zap size={26} color="var(--primary)" /> Automation Engine
          </h1>
          <p style={{ margin: '4px 0 0', color: 'var(--text-muted)', fontSize: 14 }}>
            Create smart rules that automate your financial workflows.
          </p>
        </div>
        <Button onClick={() => { setEditingRule(null); setShowModal(true); }} variant="primary"
          style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Plus size={16} /> New Rule
        </Button>
      </div>

      {/* Stats Row */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 14, marginBottom: 24 }}>
          <StatCard label="Total Rules" value={stats.total_rules} icon={Zap} color="var(--primary)" />
          <StatCard label="Active Rules" value={stats.active_rules} icon={Activity} color="#10b981" />
          <StatCard label="Total Runs" value={stats.total_executions} icon={BarChart3} color="var(--purple)" />
          <StatCard label="Successful" value={stats.successful_executions} icon={CheckCircle2} color="#10b981" />
          <StatCard label="Failed" value={stats.failed_executions} icon={XCircle} color="#ef4444" />
          <StatCard label="Today's Runs" value={stats.rules_run_today} icon={RefreshCw} color="#f59e0b" />
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: 'var(--card-bg)', borderRadius: 10, padding: 4, border: '1px solid var(--border)', width: 'fit-content' }}>
        {[{ id: 'rules', label: 'Rules', icon: Zap }, { id: 'history', label: 'History', icon: Activity }].map(tab => {
          const Icon = tab.icon;
          return (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
              padding: '8px 16px', borderRadius: 7, border: 'none', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600,
              background: activeTab === tab.id ? 'var(--primary)' : 'transparent',
              color: activeTab === tab.id ? '#fff' : 'var(--text-muted)', transition: 'all 0.15s'
            }}>
              <Icon size={14} />{tab.label}
            </button>
          );
        })}
      </div>

      {/* Rules Tab */}
      {activeTab === 'rules' && (
        loading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} style={{ height: 68, borderRadius: 14, background: 'var(--card-bg)', border: '1px solid var(--border)', marginBottom: 10 }} />
          ))
        ) : rules.length === 0 ? (
          <div style={{
            padding: '60px 20px', textAlign: 'center',
            background: 'var(--card-bg)', borderRadius: 16, border: '1px solid var(--border)'
          }}>
            <Zap size={48} style={{ opacity: 0.2, marginBottom: 16 }} />
            <h3 style={{ margin: '0 0 8px', color: 'var(--text)' }}>No automation rules yet</h3>
            <p style={{ margin: '0 0 20px', color: 'var(--text-muted)', fontSize: 14 }}>
              Create your first rule to automate categorization, notifications, and more.
            </p>
            <Button onClick={() => setShowModal(true)} variant="primary">
              <Plus size={14} style={{ marginRight: 6 }} /> Create First Rule
            </Button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {rules.map(rule => (
              <RuleCard key={rule.id} rule={rule}
                onEdit={r => { setEditingRule(r); setShowModal(true); }}
                onToggle={handleToggle}
                onDelete={handleDelete}
                onRun={handleRun}
              />
            ))}
          </div>
        )
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
            {['', 'success', 'failed', 'skipped'].map(s => (
              <button key={s} onClick={() => loadExecFiltered(s)} style={{
                padding: '5px 12px', borderRadius: 7, border: `1px solid ${statusFilter === s ? 'var(--primary)' : 'var(--border)'}`,
                background: statusFilter === s ? 'var(--primary)' : 'var(--card-bg)',
                color: statusFilter === s ? '#fff' : 'var(--text-muted)',
                fontSize: 12, fontWeight: 600, cursor: 'pointer'
              }}>
                {s || 'All'}
              </button>
            ))}
          </div>
          <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 14, padding: '4px 20px' }}>
            {executions.length === 0 ? (
              <div style={{ padding: '32px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
                <Activity size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
                <div>No execution history yet.</div>
              </div>
            ) : (
              executions.map(e => <ExecRow key={e.id} exec={e} />)
            )}
          </div>
        </div>
      )}

      {/* Rule Builder Modal */}
      {showModal && (
        <RuleModal
          rule={editingRule}
          categories={categories}
          accounts={accounts}
          goals={goals}
          onSave={handleSave}
          onClose={() => { setShowModal(false); setEditingRule(null); }}
        />
      )}

      {/* Confirm Dialog */}
      {confirmDlg.open && (
        <ConfirmDialog
          isOpen={confirmDlg.open}
          title={confirmDlg.title}
          message={confirmDlg.message}
          onConfirm={confirmDlg.onConfirm}
          onClose={() => setConfirmDlg({ open: false })}
          variant={confirmDlg.danger ? 'danger' : 'default'}
        />
      )}
    </div>
  );
}
