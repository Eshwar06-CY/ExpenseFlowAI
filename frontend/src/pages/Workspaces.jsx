import React, { useState, useEffect, useCallback } from 'react';
import {
  Users, Plus, Settings, Trash2, LogOut, Crown, Shield,
  Edit3, Eye, UserPlus, Check, X, Clock, Building2,
  ChevronRight, MoreVertical, Mail, Activity, MessageSquare,
  AlertTriangle, Copy, Search, Filter
} from 'lucide-react';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import ConfirmDialog from '../components/Common/ConfirmDialog';
import EmptyState from '../components/Common/EmptyState';
import { useToast } from '../context/ToastContext';
import * as collab from '../services/collaboration';

// ─── Role badges ──────────────────────────────────────────────────────────

const ROLE_META = {
  owner:  { label: 'Owner',  icon: Crown,  color: 'var(--gold)',    bg: 'rgba(255,193,7,0.12)'  },
  admin:  { label: 'Admin',  icon: Shield, color: 'var(--purple)',  bg: 'rgba(139,92,246,0.12)' },
  editor: { label: 'Editor', icon: Edit3,  color: 'var(--primary)', bg: 'rgba(99,102,241,0.12)' },
  viewer: { label: 'Viewer', icon: Eye,    color: 'var(--text-muted)', bg: 'rgba(100,116,139,0.12)' },
};

function RoleBadge({ role }) {
  const meta = ROLE_META[role] || ROLE_META.viewer;
  const Icon = meta.icon;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '2px 8px', borderRadius: 6,
      background: meta.bg, color: meta.color,
      fontSize: 11, fontWeight: 600, letterSpacing: '0.03em'
    }}>
      <Icon size={10} />
      {meta.label}
    </span>
  );
}

// ─── Avatar ───────────────────────────────────────────────────────────────

function Avatar({ name = '', size = 32 }) {
  const initials = name.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase() || '?';
  const colors = ['#6366f1','#8b5cf6','#ec4899','#10b981','#f59e0b','#3b82f6'];
  const color = colors[name.charCodeAt(0) % colors.length];
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      background: color, color: '#fff',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * 0.35, fontWeight: 700, flexShrink: 0
    }}>
      {initials}
    </div>
  );
}

// ─── Workspace Card ───────────────────────────────────────────────────────

function WorkspaceCard({ ws, myRole, isActive, onClick, onDelete, onLeave }) {
  const [showMenu, setShowMenu] = useState(false);
  return (
    <div
      onClick={onClick}
      style={{
        position: 'relative', cursor: 'pointer',
        padding: '18px 20px', borderRadius: 14,
        background: isActive
          ? 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.08))'
          : 'var(--card-bg)',
        border: `1.5px solid ${isActive ? 'var(--primary)' : 'var(--border)'}`,
        transition: 'all 0.2s ease',
        boxShadow: isActive ? '0 0 0 3px rgba(99,102,241,0.1)' : 'none'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: 'linear-gradient(135deg, var(--primary), var(--purple))',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Building2 size={18} color="#fff" />
          </div>
          <div>
            <div style={{ fontWeight: 700, color: 'var(--text)', fontSize: 15 }}>{ws.name}</div>
            {ws.description && (
              <div style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 2 }}>{ws.description}</div>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }} onClick={e => e.stopPropagation()}>
          <RoleBadge role={myRole} />
          <button
            onClick={() => setShowMenu(m => !m)}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-muted)', padding: 4, borderRadius: 6,
              display: 'flex', alignItems: 'center'
            }}
          >
            <MoreVertical size={16} />
          </button>
        </div>
      </div>

      {/* Dropdown menu */}
      {showMenu && (
        <div
          style={{
            position: 'absolute', top: 48, right: 12, zIndex: 50,
            background: 'var(--card-bg)', border: '1px solid var(--border)',
            borderRadius: 10, overflow: 'hidden', minWidth: 160,
            boxShadow: '0 8px 32px rgba(0,0,0,0.25)'
          }}
          onMouseLeave={() => setShowMenu(false)}
        >
          {myRole === 'owner' && (
            <button
              onClick={(e) => { e.stopPropagation(); setShowMenu(false); onDelete(ws); }}
              style={{ width: '100%', padding: '10px 14px', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, color: 'var(--danger)', fontSize: 13 }}
            >
              <Trash2 size={14} /> Delete workspace
            </button>
          )}
          {myRole !== 'owner' && (
            <button
              onClick={(e) => { e.stopPropagation(); setShowMenu(false); onLeave(ws); }}
              style={{ width: '100%', padding: '10px 14px', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, color: 'var(--warning)', fontSize: 13 }}
            >
              <LogOut size={14} /> Leave workspace
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Member Row ──────────────────────────────────────────────────────────

function MemberRow({ member, currentUserId, myRole, onUpdateRole, onRemove, onTransfer }) {
  const [editing, setEditing] = useState(false);
  const [newRole, setNewRole] = useState(member.role);
  const canManage = (myRole === 'owner' || myRole === 'admin') && member.role !== 'owner';
  const isMe = member.user_id === currentUserId;
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '12px 0', borderBottom: '1px solid var(--border)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Avatar name={member.full_name || member.email} size={36} />
        <div>
          <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 6 }}>
            {member.full_name || member.email}
            {isMe && <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>(you)</span>}
            {!member.is_accepted && (
              <span style={{ color: 'var(--warning)', fontSize: 11, display: 'flex', alignItems: 'center', gap: 3 }}>
                <Clock size={10} /> Pending
              </span>
            )}
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{member.email}</div>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {editing && canManage ? (
          <>
            <select
              value={newRole}
              onChange={e => setNewRole(e.target.value)}
              style={{
                padding: '4px 8px', borderRadius: 6, border: '1px solid var(--border)',
                background: 'var(--input-bg)', color: 'var(--text)', fontSize: 12
              }}
            >
              <option value="admin">Admin</option>
              <option value="editor">Editor</option>
              <option value="viewer">Viewer</option>
            </select>
            <button onClick={() => { onUpdateRole(member.user_id, newRole); setEditing(false); }}
              style={{ background: 'var(--success)', color: '#fff', border: 'none', padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 12 }}>
              Save
            </button>
            <button onClick={() => setEditing(false)}
              style={{ background: 'var(--card-bg)', color: 'var(--text-muted)', border: '1px solid var(--border)', padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 12 }}>
              Cancel
            </button>
          </>
        ) : (
          <>
            <RoleBadge role={member.role} />
            {canManage && (
              <>
                <button onClick={() => setEditing(true)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 4, borderRadius: 6 }}>
                  <Edit3 size={14} />
                </button>
                <button onClick={() => onRemove(member.user_id)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--danger)', padding: 4, borderRadius: 6 }}>
                  <Trash2 size={14} />
                </button>
              </>
            )}
            {myRole === 'owner' && member.role !== 'owner' && (
              <button onClick={() => onTransfer(member.user_id)}
                title="Transfer ownership"
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--gold)', padding: 4, borderRadius: 6 }}>
                <Crown size={14} />
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ─── Audit Log ────────────────────────────────────────────────────────────

const ACTION_ICONS = {
  created: '✨', updated: '✏️', deleted: '🗑️',
  invited: '📨', joined: '🎉', declined: '❌', removed: '🚫', left: '👋',
  role_changed: '🔄', ownership_transferred: '👑', commented: '💬',
  imported: '📥', exported: '📤'
};

function AuditEntry({ log }) {
  const date = new Date(log.created_at).toLocaleString();
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
      <div style={{ fontSize: 16, flexShrink: 0, marginTop: 1 }}>{ACTION_ICONS[log.action] || '📋'}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, color: 'var(--text)' }}>
          <span style={{ fontWeight: 600 }}>{log.user_name}</span>
          {' '}{log.description}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{date}</div>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────

export default function Workspaces() {
  const { addToast } = useToast();
  const showToast = (msg, type) => addToast(msg, type);
  const [workspaces, setWorkspaces] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeWs, setActiveWs] = useState(null);
  const [members, setMembers] = useState([]);
  const [auditLog, setAuditLog] = useState([]);
  const [activeTab, setActiveTab] = useState('members'); // 'members' | 'audit'

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [confirmDlg, setConfirmDlg] = useState({ open: false, title: '', message: '', onConfirm: null });

  // Forms
  const [wsName, setWsName] = useState('');
  const [wsDesc, setWsDesc] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('viewer');
  const [saving, setSaving] = useState(false);

  // Current user id from localStorage (decoded from stored user)
  const currentUser = (() => {
    try { return JSON.parse(localStorage.getItem('user') || '{}'); } catch { return {}; }
  })();
  const currentUserId = currentUser.id;

  const myRole = activeWs
    ? (members.find(m => m.user_id === currentUserId)?.role || 'viewer')
    : null;

  // ── Load workspaces & invitations ────────────────────────────────────
  const loadWorkspaces = useCallback(async () => {
    try {
      setLoading(true);
      const [wsRes, invRes] = await Promise.all([
        collab.listWorkspaces(),
        collab.listPendingInvitations()
      ]);
      setWorkspaces(wsRes.data);
      setInvitations(invRes.data);
      if (!activeWs && wsRes.data.length > 0) {
        setActiveWs(wsRes.data[0]);
      }
    } catch {
      showToast('Failed to load workspaces.', 'error');
    } finally {
      setLoading(false);
    }
  }, [activeWs, showToast]);

  // ── Load members & audit for active workspace ─────────────────────────
  const loadWorkspaceDetail = useCallback(async (ws) => {
    if (!ws) return;
    try {
      const [mRes, aRes] = await Promise.all([
        collab.listMembers(ws.id),
        collab.getAuditLog(ws.id, { limit: 30 })
      ]);
      setMembers(mRes.data);
      setAuditLog(aRes.data);
    } catch {
      // silently ignore
    }
  }, []);

  useEffect(() => { loadWorkspaces(); }, []);
  useEffect(() => { if (activeWs) loadWorkspaceDetail(activeWs); }, [activeWs]);

  // ── Create Workspace ──────────────────────────────────────────────────
  const handleCreate = async (e) => {
    e.preventDefault();
    if (!wsName.trim()) return;
    setSaving(true);
    try {
      const res = await collab.createWorkspace({ name: wsName.trim(), description: wsDesc.trim() || null });
      setWorkspaces(prev => [...prev, res.data]);
      setActiveWs(res.data);
      showToast(`Workspace "${res.data.name}" created!`, 'success');
      setShowCreateModal(false);
      setWsName(''); setWsDesc('');
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to create workspace.', 'error');
    } finally {
      setSaving(false);
    }
  };

  // ── Delete Workspace ─────────────────────────────────────────────────
  const handleDelete = (ws) => {
    setConfirmDlg({
      open: true, danger: true,
      title: 'Delete Workspace',
      message: `Permanently delete "${ws.name}" and all its data? This cannot be undone.`,
      onConfirm: async () => {
        try {
          await collab.deleteWorkspace(ws.id);
          const remaining = workspaces.filter(w => w.id !== ws.id);
          setWorkspaces(remaining);
          setActiveWs(remaining[0] || null);
          showToast('Workspace deleted.', 'success');
        } catch {
          showToast('Failed to delete workspace.', 'error');
        }
        setConfirmDlg({ open: false });
      }
    });
  };

  // ── Leave Workspace ───────────────────────────────────────────────────
  const handleLeave = (ws) => {
    setConfirmDlg({
      open: true,
      title: 'Leave Workspace',
      message: `Leave "${ws.name}"? You will lose access immediately.`,
      onConfirm: async () => {
        try {
          await collab.leaveWorkspace(ws.id);
          const remaining = workspaces.filter(w => w.id !== ws.id);
          setWorkspaces(remaining);
          setActiveWs(remaining[0] || null);
          showToast('You left the workspace.', 'success');
        } catch (err) {
          showToast(err?.response?.data?.detail || 'Failed to leave workspace.', 'error');
        }
        setConfirmDlg({ open: false });
      }
    });
  };

  // ── Invite member ─────────────────────────────────────────────────────
  const handleInvite = async (e) => {
    e.preventDefault();
    if (!inviteEmail.trim() || !activeWs) return;
    setSaving(true);
    try {
      await collab.inviteMember(activeWs.id, { email: inviteEmail.trim(), role: inviteRole });
      showToast(`Invitation sent to ${inviteEmail}`, 'success');
      setShowInviteModal(false);
      setInviteEmail('');
      loadWorkspaceDetail(activeWs);
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to send invite.', 'error');
    } finally {
      setSaving(false);
    }
  };

  // ── Update role ───────────────────────────────────────────────────────
  const handleUpdateRole = async (userId, role) => {
    try {
      await collab.updateMemberRole(activeWs.id, userId, { role });
      showToast('Role updated.', 'success');
      loadWorkspaceDetail(activeWs);
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to update role.', 'error');
    }
  };

  // ── Remove member ─────────────────────────────────────────────────────
  const handleRemove = (userId) => {
    const member = members.find(m => m.user_id === userId);
    setConfirmDlg({
      open: true, danger: true,
      title: 'Remove Member',
      message: `Remove ${member?.full_name || member?.email || 'this member'} from the workspace?`,
      onConfirm: async () => {
        try {
          await collab.removeMember(activeWs.id, userId);
          showToast('Member removed.', 'success');
          loadWorkspaceDetail(activeWs);
        } catch (err) {
          showToast(err?.response?.data?.detail || 'Failed to remove member.', 'error');
        }
        setConfirmDlg({ open: false });
      }
    });
  };

  // ── Transfer ownership ────────────────────────────────────────────────
  const handleTransfer = (userId) => {
    const member = members.find(m => m.user_id === userId);
    setConfirmDlg({
      open: true, danger: true,
      title: 'Transfer Ownership',
      message: `Transfer ownership to ${member?.full_name || member?.email}? You will become an admin.`,
      onConfirm: async () => {
        try {
          const res = await collab.transferOwnership(activeWs.id, userId);
          setActiveWs(res.data);
          showToast('Ownership transferred.', 'success');
          loadWorkspaceDetail(res.data);
        } catch (err) {
          showToast(err?.response?.data?.detail || 'Failed to transfer ownership.', 'error');
        }
        setConfirmDlg({ open: false });
      }
    });
  };

  // ── Accept / Decline invitation ───────────────────────────────────────
  const handleAcceptInvite = async (inv) => {
    try {
      await collab.acceptInvitation(inv.workspace_id);
      showToast('Invitation accepted!', 'success');
      loadWorkspaces();
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to accept invitation.', 'error');
    }
  };

  const handleDeclineInvite = async (inv) => {
    try {
      await collab.declineInvitation(inv.workspace_id);
      setInvitations(prev => prev.filter(i => i.id !== inv.id));
      showToast('Invitation declined.', 'info');
    } catch {
      showToast('Failed to decline invitation.', 'error');
    }
  };

  // ─────────────────────────────────────────────────────────────────────
  return (
    <div style={{ padding: '24px 28px', maxWidth: 1200, margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 800, color: 'var(--text)' }}>Workspaces</h1>
          <p style={{ margin: '4px 0 0', color: 'var(--text-muted)', fontSize: 14 }}>
            Collaborate with your team in isolated financial workspaces.
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} variant="primary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Plus size={16} /> New Workspace
        </Button>
      </div>

      {/* Pending Invitations Banner */}
      {invitations.length > 0 && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(245,158,11,0.12), rgba(217,119,6,0.06))',
          border: '1px solid rgba(245,158,11,0.35)',
          borderRadius: 12, padding: '14px 18px', marginBottom: 24
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, fontWeight: 700, color: 'var(--warning)' }}>
            <Mail size={16} /> {invitations.length} Pending Invitation{invitations.length > 1 ? 's' : ''}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {invitations.map(inv => (
              <div key={inv.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                <div style={{ fontSize: 14, color: 'var(--text)' }}>
                  Invited to <strong>{inv.workspace_id}</strong> as <RoleBadge role={inv.role} />
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <Button onClick={() => handleAcceptInvite(inv)} variant="primary" style={{ padding: '5px 12px', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Check size={13} /> Accept
                  </Button>
                  <Button onClick={() => handleDeclineInvite(inv)} variant="ghost" style={{ padding: '5px 12px', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <X size={13} /> Decline
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 20, alignItems: 'start' }}>
        {/* Left: Workspace List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} style={{ height: 72, borderRadius: 12, background: 'var(--card-bg)', border: '1px solid var(--border)', animation: 'pulse 1.5s ease-in-out infinite' }} />
            ))
          ) : workspaces.length === 0 ? (
            <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-muted)', background: 'var(--card-bg)', borderRadius: 12, border: '1px solid var(--border)' }}>
              <Building2 size={32} style={{ marginBottom: 10, opacity: 0.4 }} />
              <div style={{ fontSize: 13 }}>No workspaces yet.<br />Create your first one!</div>
            </div>
          ) : (
            workspaces.map(ws => {
              const myMember = ws._myRole || members.find(m => m.user_id === currentUserId);
              const roleStr = activeWs?.id === ws.id ? myRole : 'viewer';
              return (
                <WorkspaceCard
                  key={ws.id}
                  ws={ws}
                  myRole={roleStr}
                  isActive={activeWs?.id === ws.id}
                  onClick={() => setActiveWs(ws)}
                  onDelete={handleDelete}
                  onLeave={handleLeave}
                />
              );
            })
          )}
        </div>

        {/* Right: Detail Panel */}
        {activeWs ? (
          <div>
            {/* Workspace Header */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(99,102,241,0.12), rgba(139,92,246,0.06))',
              border: '1px solid var(--border)', borderRadius: 14,
              padding: '20px 24px', marginBottom: 16
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  <div style={{
                    width: 48, height: 48, borderRadius: 12,
                    background: 'linear-gradient(135deg, var(--primary), var(--purple))',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <Building2 size={22} color="#fff" />
                  </div>
                  <div>
                    <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, color: 'var(--text)' }}>{activeWs.name}</h2>
                    {activeWs.description && (
                      <p style={{ margin: '3px 0 0', color: 'var(--text-muted)', fontSize: 13 }}>{activeWs.description}</p>
                    )}
                  </div>
                </div>
                {(myRole === 'owner' || myRole === 'admin') && (
                  <Button
                    onClick={() => setShowInviteModal(true)}
                    variant="primary"
                    style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}
                  >
                    <UserPlus size={14} /> Invite Member
                  </Button>
                )}
              </div>
              <div style={{ display: 'flex', gap: 20, marginTop: 14 }}>
                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                  <span style={{ fontWeight: 700, color: 'var(--text)', fontSize: 18 }}>
                    {members.filter(m => m.is_accepted).length}
                  </span>
                  {' '}member{members.filter(m => m.is_accepted).length !== 1 ? 's' : ''}
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                  Your role: <RoleBadge role={myRole || 'viewer'} />
                </div>
              </div>
            </div>

            {/* Tab navigation */}
            <div style={{ display: 'flex', gap: 4, marginBottom: 16, background: 'var(--card-bg)', borderRadius: 10, padding: 4, border: '1px solid var(--border)' }}>
              {[
                { id: 'members', label: 'Members', icon: Users },
                { id: 'audit', label: 'Activity Log', icon: Activity }
              ].map(tab => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    style={{
                      flex: 1, padding: '8px 12px', borderRadius: 7, border: 'none', cursor: 'pointer',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontSize: 13, fontWeight: 600,
                      background: activeTab === tab.id ? 'var(--primary)' : 'transparent',
                      color: activeTab === tab.id ? '#fff' : 'var(--text-muted)',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <Icon size={14} /> {tab.label}
                  </button>
                );
              })}
            </div>

            {/* Members Tab */}
            {activeTab === 'members' && (
              <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 14, padding: '4px 20px' }}>
                {members.length === 0 ? (
                  <div style={{ padding: '32px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <Users size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
                    <div>No members yet.</div>
                  </div>
                ) : (
                  members.map(m => (
                    <MemberRow
                      key={m.id}
                      member={m}
                      currentUserId={currentUserId}
                      myRole={myRole}
                      onUpdateRole={handleUpdateRole}
                      onRemove={handleRemove}
                      onTransfer={handleTransfer}
                    />
                  ))
                )}
              </div>
            )}

            {/* Audit Log Tab */}
            {activeTab === 'audit' && (
              <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 14, padding: '4px 20px' }}>
                {auditLog.length === 0 ? (
                  <div style={{ padding: '32px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <Activity size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
                    <div>No activity recorded yet.</div>
                  </div>
                ) : (
                  auditLog.map(log => <AuditEntry key={log.id} log={log} />)
                )}
              </div>
            )}
          </div>
        ) : (
          !loading && (
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              padding: '60px 20px', background: 'var(--card-bg)', borderRadius: 14, border: '1px solid var(--border)', textAlign: 'center'
            }}>
              <Building2 size={48} style={{ opacity: 0.2, marginBottom: 16 }} />
              <h3 style={{ margin: '0 0 8px', color: 'var(--text)' }}>Select a workspace</h3>
              <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: 14 }}>
                Or create a new one to start collaborating.
              </p>
            </div>
          )
        )}
      </div>

      {/* Create Workspace Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div style={{
            background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 18,
            padding: '28px 32px', width: '100%', maxWidth: 440,
            boxShadow: '0 24px 64px rgba(0,0,0,0.4)'
          }}>
            <h2 style={{ margin: '0 0 20px', fontSize: 20, fontWeight: 800 }}>Create Workspace</h2>
            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Workspace Name *</label>
                <input
                  value={wsName} onChange={e => setWsName(e.target.value)}
                  placeholder="e.g. Family Budget, Business Q4..."
                  required
                  style={{
                    width: '100%', padding: '10px 12px', borderRadius: 8, boxSizing: 'border-box',
                    border: '1px solid var(--border)', background: 'var(--input-bg)', color: 'var(--text)', fontSize: 14
                  }}
                />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Description</label>
                <textarea
                  value={wsDesc} onChange={e => setWsDesc(e.target.value)}
                  placeholder="Optional description..."
                  rows={2}
                  style={{
                    width: '100%', padding: '10px 12px', borderRadius: 8, boxSizing: 'border-box',
                    border: '1px solid var(--border)', background: 'var(--input-bg)', color: 'var(--text)', fontSize: 14,
                    resize: 'vertical'
                  }}
                />
              </div>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 8 }}>
                <Button type="button" variant="ghost" onClick={() => setShowCreateModal(false)}>Cancel</Button>
                <Button type="submit" variant="primary" disabled={saving}>
                  {saving ? 'Creating…' : 'Create Workspace'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div style={{
            background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 18,
            padding: '28px 32px', width: '100%', maxWidth: 420,
            boxShadow: '0 24px 64px rgba(0,0,0,0.4)'
          }}>
            <h2 style={{ margin: '0 0 6px', fontSize: 20, fontWeight: 800 }}>Invite Member</h2>
            <p style={{ margin: '0 0 20px', color: 'var(--text-muted)', fontSize: 13 }}>
              Invite someone to <strong>{activeWs?.name}</strong>.
            </p>
            <form onSubmit={handleInvite} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Email Address *</label>
                <input
                  type="email" value={inviteEmail} onChange={e => setInviteEmail(e.target.value)}
                  placeholder="colleague@example.com"
                  required
                  style={{
                    width: '100%', padding: '10px 12px', borderRadius: 8, boxSizing: 'border-box',
                    border: '1px solid var(--border)', background: 'var(--input-bg)', color: 'var(--text)', fontSize: 14
                  }}
                />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Role</label>
                <select
                  value={inviteRole} onChange={e => setInviteRole(e.target.value)}
                  style={{
                    width: '100%', padding: '10px 12px', borderRadius: 8, boxSizing: 'border-box',
                    border: '1px solid var(--border)', background: 'var(--input-bg)', color: 'var(--text)', fontSize: 14
                  }}
                >
                  <option value="viewer">Viewer — can view only</option>
                  <option value="editor">Editor — can edit transactions, budgets etc.</option>
                  <option value="admin">Admin — can invite & manage members</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 8 }}>
                <Button type="button" variant="ghost" onClick={() => setShowInviteModal(false)}>Cancel</Button>
                <Button type="submit" variant="primary" disabled={saving}>
                  {saving ? 'Sending…' : 'Send Invitation'}
                </Button>
              </div>
            </form>
          </div>
        </div>
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
