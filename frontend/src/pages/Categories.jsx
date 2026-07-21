import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Edit3, X, AlertCircle, CheckCircle2, ShieldAlert, Sparkles } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';

// Available Lucide icons map for visual rendering in categories list
const ICON_GLYPHS = {
  Briefcase: '💼',
  Laptop: '💻',
  TrendingUp: '📈',
  Utensils: '🍴',
  Home: '🏠',
  Car: '🚗',
  Film: '🎬',
  Zap: '⚡',
  ShoppingBag: '🛍️',
  HeartPulse: '❤️',
  Gift: '🎁',
  BookOpen: '📖',
  Globe: '🌐',
  Smile: '😊',
};

const COLOR_PRESETS = [
  '#10B981', // green
  '#3B82F6', // blue
  '#8B5CF6', // purple
  '#EF4444', // red
  '#F59E0B', // amber
  '#06B6D4', // cyan
  '#EC4899', // pink
  '#14B8A6', // teal
  '#6366F1', // indigo
  '#F43F5E', // rose
];

const Categories = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);

  // Form State
  const [name, setName] = useState('');
  const [type, setType] = useState('expense');
  const [icon, setIcon] = useState('ShoppingBag');
  const [color, setColor] = useState('#6366F1');

  const fetchCategories = async () => {
    try {
      setLoading(true);
      const res = await api.get('/categories');
      setCategories(res.data);
    } catch (err) {
      setError('Failed to fetch categories.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  const openCreateModal = () => {
    setEditingCategory(null);
    setName('');
    setType('expense');
    setIcon('ShoppingBag');
    setColor('#6366F1');
    setError('');
    setIsModalOpen(true);
  };

  const openEditModal = (cat) => {
    if (!cat.user_id) {
      alert('Default system categories cannot be modified.');
      return;
    }
    setEditingCategory(cat);
    setName(cat.name);
    setType(cat.type);
    setIcon(cat.icon || 'ShoppingBag');
    setColor(cat.color || '#6366F1');
    setError('');
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const payload = {
      name,
      type,
      icon,
      color,
    };

    try {
      if (editingCategory) {
        await api.put(`/categories/${editingCategory.id}`, payload);
        setSuccess('Category updated successfully.');
      } else {
        await api.post('/categories/', payload);
        setSuccess('Category created successfully.');
      }
      setIsModalOpen(false);
      fetchCategories();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save category.');
    }
  };

  const handleDelete = async (categoryId) => {
    if (!window.confirm('Are you sure you want to delete this custom category?')) return;
    setError('');
    setSuccess('');

    try {
      await api.delete(`/categories/${categoryId}`);
      setSuccess('Category deleted successfully.');
      fetchCategories();
    } catch (err) {
      setError('Failed to delete category.');
    }
  };

  const handleSeed = async () => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');
      await api.post('/categories/seed');
      setSuccess('Seeded standard default templates successfully!');
      fetchCategories();
    } catch (err) {
      setError('Seeding failed.');
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Top action block */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-dark-50 tracking-tight">Categories Setup</h2>
          <p className="text-dark-400 text-sm mt-1">Configure transaction tags, indicators, and color groupings.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={handleSeed} className="flex items-center gap-1.5 py-2">
            <Sparkles className="w-4 h-4 text-brand-400" /> Seed defaults
          </Button>
          <Button onClick={openCreateModal} className="flex items-center gap-2 py-2">
            <Plus className="w-4 h-4" /> Add Category
          </Button>
        </div>
      </div>

      {success && (
        <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-medium flex items-center gap-2 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4" /> {success}
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium flex items-center gap-2 animate-fadeIn">
          <AlertCircle className="w-4 h-4" /> {error}
        </div>
      )}

      {/* Grid of Categories */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-pulse">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="bg-dark-900/50 border border-dark-850 h-20 rounded-xl"></div>
          ))}
        </div>
      ) : categories.length === 0 ? (
        <div className="text-center py-16 rounded-xl bg-dark-900/20 border border-dark-850">
          <ShieldAlert className="w-12 h-12 text-dark-500 mx-auto mb-4" />
          <h3 className="text-base font-semibold text-dark-250">No Categories Found</h3>
          <p className="text-xs text-dark-450 mt-1 max-w-md mx-auto leading-relaxed">
            Click seed defaults to populate standard banking and home ledger categories, or create custom tags.
          </p>
          <Button onClick={handleSeed} variant="primary" className="mt-4 py-2">
            Seed Standard Templates
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {categories.map((cat) => {
            const isSystem = !cat.user_id;
            return (
              <div
                key={cat.id}
                className="bg-dark-900/40 border border-dark-850 hover:border-dark-750 p-4 rounded-xl flex items-center justify-between group transition-all duration-200"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center text-lg shrink-0"
                    style={{ backgroundColor: `${cat.color || '#6366F1'}15`, border: `1px solid ${cat.color || '#6366F1'}30` }}
                  >
                    <span style={{ color: cat.color || '#6366F1' }}>
                      {ICON_GLYPHS[cat.icon] || '🏷️'}
                    </span>
                  </div>
                  <div className="min-w-0">
                    <h4 className="text-sm font-bold text-dark-100 truncate">{cat.name}</h4>
                    <span className="text-[10px] text-dark-400 capitalize block mt-0.5">{cat.type}</span>
                  </div>
                </div>

                <div className="flex gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                  {!isSystem ? (
                    <>
                      <button
                        onClick={() => openEditModal(cat)}
                        className="p-1 rounded hover:bg-dark-800 text-dark-400 hover:text-dark-200"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(cat.id)}
                        className="p-1 rounded hover:bg-red-500/10 text-dark-400 hover:text-red-400"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </>
                  ) : (
                    <span className="text-[9px] text-dark-500 font-semibold uppercase px-1.5 py-0.5 bg-dark-950 border border-dark-850 rounded">
                      System
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Category Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-dark-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-dark-900 border border-dark-800 rounded-xl overflow-hidden shadow-2xl animate-scaleUp">
            <div className="flex justify-between items-center p-5 border-b border-dark-850">
              <h3 className="text-lg font-bold text-dark-50">
                {editingCategory ? 'Edit Category' : 'Create Category'}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-dark-400 hover:text-dark-150">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Category Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Subscriptions, Groceries"
                  className="w-full bg-dark-950 border border-dark-850 rounded-lg px-4 py-2 text-sm text-dark-200 placeholder-dark-500 outline-none focus:border-brand-500 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Type</label>
                <select
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  className="w-full bg-dark-950 border border-dark-850 rounded-lg px-3 py-2 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all"
                >
                  <option value="expense">Expense Tag</option>
                  <option value="income">Income Tag</option>
                  <option value="both">Mutual (Both)</option>
                </select>
              </div>

              {/* Icon Selector grid */}
              <div>
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Select Icon Representation</label>
                <div className="grid grid-cols-7 gap-2 max-h-32 overflow-y-auto p-1 bg-dark-950 border border-dark-850 rounded-lg">
                  {Object.keys(ICON_GLYPHS).map((glyphKey) => (
                    <button
                      key={glyphKey}
                      type="button"
                      onClick={() => setIcon(glyphKey)}
                      className={`h-9 rounded flex items-center justify-center text-lg transition-all ${
                        icon === glyphKey ? 'bg-brand-500/25 border border-brand-500/50 scale-105' : 'hover:bg-dark-900 border border-transparent'
                      }`}
                    >
                      {ICON_GLYPHS[glyphKey]}
                    </button>
                  ))}
                </div>
              </div>

              {/* Color Presets */}
              <div>
                <label className="block text-xs font-semibold text-dark-400 uppercase tracking-wider mb-2">Select Color</label>
                <div className="flex gap-2.5 flex-wrap">
                  {COLOR_PRESETS.map((col) => (
                    <button
                      key={col}
                      type="button"
                      onClick={() => setColor(col)}
                      className={`w-7 h-7 rounded-full border transition-all ${
                        color === col ? 'border-white scale-110 shadow-lg' : 'border-transparent hover:scale-105'
                      }`}
                      style={{ backgroundColor: col }}
                    ></button>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-dark-850 flex justify-end gap-3">
                <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  {editingCategory ? 'Save Changes' : 'Create Category'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Categories;
export { ICON_GLYPHS };
