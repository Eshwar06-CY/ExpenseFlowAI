import React, { useState, useEffect } from 'react';
import { Search, Download, Eye, Calendar, ShieldCheck } from 'lucide-react';
import api from '../../services/api';

const DigestHistory = ({ onViewDetails, onDownloadPdf }) => {
  const [items, setItems] = useState([]);
  const [digestType, setDigestType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchDigests = async () => {
    try {
      setLoading(true);
      const res = await api.get('/digests', {
        params: {
          digest_type: digestType !== 'all' ? digestType : undefined,
          limit: 50
        }
      });
      setItems(res.data.items || []);
    } catch (err) {
      console.warn('Failed to fetch digest history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDigests();
  }, [digestType]);

  const filteredItems = items.filter((item) => {
    if (!searchQuery) return true;
    return item.summary.toLowerCase().includes(searchQuery.toLowerCase());
  });

  return (
    <div className="space-y-4">
      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-dark-900 p-4 rounded-2xl border border-dark-800">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-dark-400" />
          <input
            type="text"
            placeholder="Search digests..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-dark-950 border border-dark-800 rounded-xl pl-9 pr-4 py-1.5 text-xs text-white placeholder-dark-500 outline-none focus:border-indigo-500"
          />
        </div>

        <select
          value={digestType}
          onChange={(e) => setDigestType(e.target.value)}
          className="bg-dark-950 border border-dark-800 rounded-xl px-3 py-1.5 text-xs text-dark-200 outline-none focus:border-indigo-500"
        >
          <option value="all">All Period Types</option>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
          <option value="yearly">Yearly</option>
        </select>
      </div>

      {/* History Table */}
      <div className="overflow-x-auto rounded-2xl border border-dark-800 bg-dark-900">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-dark-950 border-b border-dark-800 text-dark-400 font-bold uppercase tracking-wider">
              <th className="p-3.5">Generated Date</th>
              <th className="p-3.5">Type</th>
              <th className="p-3.5">Summary Preview</th>
              <th className="p-3.5">Health Score</th>
              <th className="p-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-850">
            {loading ? (
              <tr>
                <td colSpan={5} className="p-8 text-center text-dark-400 animate-pulse">
                  Loading historical digests...
                </td>
              </tr>
            ) : filteredItems.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-8 text-center text-dark-400">
                  No digests found matching criteria.
                </td>
              </tr>
            ) : (
              filteredItems.map((item) => (
                <tr key={item.id} className="hover:bg-dark-850/50 transition-all">
                  <td className="p-3.5 font-medium text-white whitespace-nowrap">
                    {item.generated_at ? new Date(item.generated_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td className="p-3.5 capitalize font-semibold text-indigo-400 whitespace-nowrap">
                    {item.digest_type}
                  </td>
                  <td className="p-3.5 text-dark-300 max-w-xs truncate">
                    {item.summary}
                  </td>
                  <td className="p-3.5 whitespace-nowrap">
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20">
                      {item.health_score} / 100
                    </span>
                  </td>
                  <td className="p-3.5 text-right space-x-2 whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => onViewDetails(item.id)}
                      className="p-1.5 rounded-lg bg-dark-950 hover:bg-dark-800 text-indigo-400 hover:text-indigo-300 border border-dark-800"
                      title="View Details"
                    >
                      <Eye size={14} />
                    </button>

                    {item.has_pdf && (
                      <button
                        type="button"
                        onClick={() => onDownloadPdf(item.id)}
                        className="p-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white"
                        title="Download PDF"
                      >
                        <Download size={14} />
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DigestHistory;
