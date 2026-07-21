import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, Check, AlertTriangle, ArrowRight, ArrowLeft, Save, Trash2, Layers, RotateCw, FileSpreadsheet, Plus, HelpCircle } from 'lucide-react';
import api from '../services/api';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';
import { useToast } from '../context/ToastContext';

const ImportWizard = () => {
  const navigate = useNavigate();
  const { addToast } = useToast();
  
  // Wizard flow state
  const [step, setStep] = useState(1); // 1: Upload, 2: Map Columns, 3: Review & Validate, 4: Complete
  const [loading, setLoading] = useState(false);
  const [accounts, setAccounts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [templates, setTemplates] = useState([]);
  
  // Upload inputs
  const [selectedAccount, setSelectedAccount] = useState('');
  const [file, setFile] = useState(null);
  
  // Preview outputs (from backend /upload)
  const [headers, setHeaders] = useState([]);
  const [rawRows, setRawRows] = useState([]);
  
  // Column mappings
  const [mapping, setMapping] = useState({
    date_col: '',
    amount_col: '',
    desc_col: '',
    cat_col: '',
    acc_col: '',
    ref_col: ''
  });
  const [templateName, setTemplateName] = useState('');
  const [showSaveTemplate, setShowSaveTemplate] = useState(false);

  // Analysis result (from backend /analyze)
  const [analyzedRows, setAnalyzedRows] = useState([]);
  const [duplicateCount, setDuplicateCount] = useState(0);
  const [errorCount, setErrorCount] = useState(0);
  const [duplicateAction, setDuplicateAction] = useState('skip'); // skip, replace, merge, anyway

  // Import completion stats
  const [importSummary, setImportSummary] = useState(null);

  useEffect(() => {
    fetchMetadata();
  }, []);

  const fetchMetadata = async () => {
    try {
      const [accRes, catRes, tempRes] = await Promise.all([
        api.get('/accounts'),
        api.get('/categories'),
        api.get('/import/templates')
      ]);
      setAccounts(accRes.data);
      setCategories(catRes.data);
      setTemplates(tempRes.data);
      if (accRes.data.length > 0) {
        setSelectedAccount(accRes.data[0].id.toString());
      }
    } catch (err) {
      addToast('Failed to load import metadata.', 'error');
    }
  };

  // Step 1: Upload File
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      addToast('Please select a CSV or Excel file to upload.', 'warning');
      return;
    }
    if (!selectedAccount) {
      addToast('Please choose an Account to import into.', 'warning');
      return;
    }

    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await api.post('/import/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setHeaders(res.data.headers);
      setRawRows(res.data.rows);
      
      // Auto-match common columns
      const autoMap = { ...mapping };
      res.data.headers.forEach(h => {
        const hl = h.toLowerCase().trim();
        if (hl.includes('date') || hl === 'time') autoMap.date_col = h;
        if (hl.includes('amount') || hl.includes('value')) autoMap.amount_col = h;
        if (hl.includes('desc') || hl === 'name' || hl === 'memo') autoMap.desc_col = h;
        if (hl.includes('cat') || hl === 'tag') autoMap.cat_col = h;
        if (hl.includes('acc') || hl === 'bank') autoMap.acc_col = h;
        if (hl.includes('ref') || hl === 'id') autoMap.ref_col = h;
      });
      setMapping(autoMap);
      
      setStep(2);
      addToast('File uploaded successfully. Map your columns.', 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to parse file preview.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Saved Templates Actions
  const handleApplyTemplate = (tpl) => {
    setMapping({
      date_col: headers.includes(tpl.date_col) ? tpl.date_col : '',
      amount_col: headers.includes(tpl.amount_col) ? tpl.amount_col : '',
      desc_col: headers.includes(tpl.desc_col) ? tpl.desc_col : '',
      cat_col: headers.includes(tpl.cat_col) ? tpl.cat_col : '',
      acc_col: headers.includes(tpl.acc_col) ? tpl.acc_col : '',
      ref_col: headers.includes(tpl.ref_col) ? tpl.ref_col : ''
    });
    addToast(`Template "${tpl.name}" applied.`, 'success');
  };

  const handleSaveTemplate = async () => {
    if (!templateName) {
      addToast('Enter a name for the mapping template.', 'warning');
      return;
    }
    try {
      setLoading(true);
      const res = await api.post('/import/templates', {
        name: templateName,
        ...mapping
      });
      setTemplates([...templates, res.data]);
      setTemplateName('');
      setShowSaveTemplate(false);
      addToast('Mapping template saved.', 'success');
    } catch (err) {
      addToast('Failed to save template.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTemplate = async (id, e) => {
    e.stopPropagation();
    try {
      await api.delete(`/import/templates/${id}`);
      setTemplates(templates.filter(t => t.id !== id));
      addToast('Mapping template deleted.', 'success');
    } catch (err) {
      addToast('Failed to delete template.', 'error');
    }
  };

  // Step 2: Analyze Mapped Columns
  const handleAnalyze = async () => {
    if (!mapping.date_col || !mapping.amount_col || !mapping.desc_col) {
      addToast('Date, Amount, and Description mapping columns are required.', 'warning');
      return;
    }
    try {
      setLoading(true);
      const res = await api.post('/import/analyze', {
        rows: rawRows,
        mapping: mapping,
        account_id: parseInt(selectedAccount)
      });
      setAnalyzedRows(res.data.rows);
      setDuplicateCount(res.data.duplicate_count);
      setErrorCount(res.data.error_count);
      setStep(3);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Analysis failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Handle Row Fields Modification on Review Grid
  const handleRowChange = (index, field, value) => {
    const updated = [...analyzedRows];
    updated[index][field] = value;
    setAnalyzedRows(updated);
  };

  const handleExecuteImport = async () => {
    // Check if any errors remaining
    const rowsWithErrors = analyzedRows.filter(r => r.validation_error);
    if (rowsWithErrors.length > 0) {
      addToast('Please resolve validation errors before importing.', 'warning');
      return;
    }

    try {
      setLoading(true);
      // Construct exact execute payload
      const rowsPayload = analyzedRows.map(r => ({
        date: r.date,
        amount: Math.abs(r.amount),
        description: r.description,
        category_id: r.category_id || null,
        account_id: parseInt(selectedAccount),
        type: r.amount >= 0 ? 'income' : 'expense',
        is_duplicate: r.is_duplicate
      }));

      const res = await api.post('/import/execute', {
        filename: file.name,
        rows: rowsPayload,
        duplicate_action: duplicateAction
      });

      setImportSummary(res.data);
      setStep(4);
      addToast('Import completed successfully!', 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to complete import process.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12 animate-fade-in">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-extrabold text-dark-50 tracking-tight flex items-center gap-2">
          <Layers className="w-8 h-8 text-brand-500" /> Statement Import Wizard
        </h2>
        <p className="text-xs text-dark-400 mt-1">Easily map, clean, validate, and upload your transaction statements.</p>
      </div>

      {/* Progress Wizard Track */}
      <div className="bg-dark-900 border border-dark-850 p-4 rounded-2xl flex justify-between items-center text-xs">
        {[
          { num: 1, label: 'Upload Statement' },
          { num: 2, label: 'Map Columns' },
          { num: 3, label: 'Review & Validate' },
          { num: 4, label: 'Completed' }
        ].map((s) => (
          <div key={s.num} className="flex items-center gap-2">
            <span className={`w-6 h-6 rounded-full flex items-center justify-center font-bold transition-all ${
              step === s.num
                ? 'bg-brand-500 text-white ring-4 ring-brand-500/10'
                : step > s.num
                ? 'bg-green-500/10 border border-green-500/30 text-green-450'
                : 'bg-dark-950 border border-dark-800 text-dark-500'
            }`}>
              {step > s.num ? <Check className="w-3.5 h-3.5" /> : s.num}
            </span>
            <span className={`font-semibold ${step === s.num ? 'text-dark-50' : 'text-dark-400'}`}>{s.label}</span>
            {s.num < 4 && <span className="text-dark-700 font-bold mx-2">➔</span>}
          </div>
        ))}
      </div>

      {/* Step 1: Upload File & Pick Account */}
      {step === 1 && (
        <Card title="Upload Bank Statement File" subtitle="Select CSV or Excel (.xlsx) file and target account">
          <div className="space-y-6 max-w-lg">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-dark-300">Target Workspace Account</label>
              <select
                value={selectedAccount}
                onChange={(e) => setSelectedAccount(e.target.value)}
                className="w-full bg-dark-950 border border-dark-800 rounded-xl px-3 py-2.5 text-xs text-dark-200 focus:border-brand-500 outline-none"
              >
                {accounts.map(a => (
                  <option key={a.id} value={a.id}>{a.name} (${a.balance.toLocaleString()})</option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-dark-300">Upload CSV / Excel Sheet</label>
              <div className="border-2 border-dashed border-dark-800 hover:border-brand-500/50 rounded-2xl p-8 transition-all bg-dark-950/40 relative cursor-pointer group text-center">
                <input
                  type="file"
                  accept=".csv, .xlsx"
                  onChange={handleFileChange}
                  className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                />
                <div className="space-y-2.5">
                  <div className="p-3 bg-dark-900 border border-dark-800 text-brand-400 rounded-2xl inline-block group-hover:scale-110 transition-transform">
                    <FileSpreadsheet className="w-8 h-8" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-dark-200">
                      {file ? file.name : "Drag your statement file here, or browse"}
                    </p>
                    <p className="text-[10px] text-dark-500 mt-1">Supports standard CSV or Excel Spreadsheet files up to 10MB</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-2">
              <Button
                variant="primary"
                onClick={handleUpload}
                disabled={loading || !file}
                className="w-full py-2.5 text-xs flex justify-center items-center gap-1.5"
              >
                {loading ? <RotateCw className="w-4 h-4 animate-spin" /> : <>Next: Parse Columns <ArrowRight className="w-4 h-4" /></>}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Step 2: Map Columns */}
      {step === 2 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Columns selectors */}
          <div className="lg:col-span-2 space-y-6">
            <Card title="Map Statement Columns" subtitle="Select which file headers correspond to each transaction attribute">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {Object.keys(mapping).map((key) => {
                  const label = key.replace('_col', '').replace('cat', 'category').replace('acc', 'account').replace('desc', 'description').toUpperCase();
                  const isRequired = ['date_col', 'amount_col', 'desc_col'].includes(key);
                  return (
                    <div key={key} className="space-y-1.5">
                      <label className="text-xs font-bold text-dark-300 flex items-center gap-1">
                        {label} {isRequired && <span className="text-red-500">*</span>}
                      </label>
                      <select
                        value={mapping[key]}
                        onChange={(e) => setMapping({ ...mapping, [key]: e.target.value })}
                        className="w-full bg-dark-950 border border-dark-800 rounded-xl px-3 py-2 text-xs text-dark-200 focus:border-brand-500 outline-none"
                      >
                        <option value="">-- Ignore / Skip Column --</option>
                        {headers.map(h => (
                          <option key={h} value={h}>{h}</option>
                        ))}
                      </select>
                    </div>
                  );
                })}
              </div>

              {/* Save template */}
              <div className="border-t border-dark-850 mt-6 pt-6 space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-dark-400">Frequently use this statement format? Save mapping template.</span>
                  {!showSaveTemplate ? (
                    <Button variant="secondary" size="xs" onClick={() => setShowSaveTemplate(true)} className="flex items-center gap-1.5 py-1.5 px-3">
                      <Plus className="w-3.5 h-3.5" /> Save Mapping Template
                    </Button>
                  ) : (
                    <div className="flex gap-2 items-center">
                      <input
                        type="text"
                        placeholder="Template Name (e.g. Chase CSV)"
                        value={templateName}
                        onChange={(e) => setTemplateName(e.target.value)}
                        className="bg-dark-950 border border-dark-800 rounded-lg px-2.5 py-1 text-xs text-dark-200 outline-none focus:border-brand-500"
                      />
                      <Button variant="primary" size="xs" onClick={handleSaveTemplate} className="flex items-center gap-1 py-1 px-2.5">
                        <Save className="w-3 h-3" /> Save
                      </Button>
                      <Button variant="secondary" size="xs" onClick={() => setShowSaveTemplate(false)} className="py-1 px-2.5">Cancel</Button>
                    </div>
                  )}
                </div>
              </div>
            </Card>

            <div className="flex justify-between items-center mt-6">
              <Button variant="secondary" onClick={() => setStep(1)} className="flex items-center gap-1.5 text-xs py-2">
                <ArrowLeft className="w-4 h-4" /> Previous
              </Button>
              <Button variant="primary" onClick={handleAnalyze} disabled={loading} className="flex items-center gap-1.5 text-xs py-2">
                {loading ? <RotateCw className="w-4 h-4 animate-spin" /> : <>Next: Review & Validate <ArrowRight className="w-4 h-4" /></>}
              </Button>
            </div>
          </div>

          {/* Saved Templates Panel */}
          <div className="space-y-6">
            <Card title="Saved Templates" subtitle="Choose template configuration">
              {templates.length === 0 ? (
                <div className="py-8 text-center text-xs text-dark-500 italic">
                  No saved mapping configurations found.
                </div>
              ) : (
                <div className="space-y-2">
                  {templates.map(tpl => (
                    <div
                      key={tpl.id}
                      onClick={() => handleApplyTemplate(tpl)}
                      className="p-3 bg-dark-900 border border-dark-850 hover:border-brand-500/30 rounded-xl flex items-center justify-between text-xs cursor-pointer transition-all hover:bg-dark-900/60"
                    >
                      <div className="space-y-1">
                        <p className="font-bold text-dark-200">{tpl.name}</p>
                        <p className="text-[10px] text-dark-500 font-mono">Date: {tpl.date_col} • Amt: {tpl.amount_col}</p>
                      </div>
                      <button
                        onClick={(e) => handleDeleteTemplate(tpl.id, e)}
                        className="p-1 hover:bg-red-500/10 text-red-500/80 hover:text-red-400 rounded-md transition-all"
                        title="Delete template"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>
      )}

      {/* Step 3: Review & Validate Grid */}
      {step === 3 && (
        <Card title="Review Statement Data" subtitle="Analyze parsing rules, override categories, and resolve duplicate items">
          <div className="space-y-6">
            {/* Duplicates Options banner */}
            {duplicateCount > 0 && (
              <div className="p-4 bg-amber-500/10 border border-amber-500/25 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs">
                <div className="flex gap-2.5 items-start">
                  <ShieldAlert className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-bold text-amber-400">Duplicate Transactions Detected</h4>
                    <p className="text-dark-350 mt-0.5 leading-relaxed">
                      We detected <strong>{duplicateCount}</strong> entries matching existing ledger items. Choose duplicate resolution:
                    </p>
                  </div>
                </div>
                <div>
                  <select
                    value={duplicateAction}
                    onChange={(e) => setDuplicateAction(e.target.value)}
                    className="bg-dark-950 border border-dark-800 rounded-xl px-3 py-2.5 text-xs text-dark-200 outline-none focus:border-brand-500 font-bold"
                  >
                    <option value="skip">Skip duplicates (Recommended)</option>
                    <option value="replace">Overwrite & Replace</option>
                    <option value="merge">Merge columns</option>
                    <option value="anyway">Import anyway</option>
                  </select>
                </div>
              </div>
            )}

            {/* Validation errors banner */}
            {errorCount > 0 && (
              <div className="p-4 bg-red-500/10 border border-red-500/25 rounded-2xl flex gap-2.5 items-start text-xs">
                <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold text-red-400">Validation Errors Check Required</h4>
                  <p className="text-dark-350 mt-0.5 leading-relaxed">
                    Found {errorCount} issues (e.g. invalid dates, text in amount column). Row importing will skip failed items.
                  </p>
                </div>
              </div>
            )}

            {/* Editable spreadsheet table */}
            <div className="overflow-x-auto border border-dark-850 rounded-2xl">
              <table className="w-full text-left border-collapse text-xs text-dark-300">
                <thead>
                  <tr className="bg-dark-900 border-b border-dark-850 text-dark-500 uppercase font-semibold">
                    <th className="p-3">Status</th>
                    <th className="p-3">Parsed Date</th>
                    <th className="p-3">Description</th>
                    <th className="p-3 text-right">Amount</th>
                    <th className="p-3">Category Override</th>
                    <th className="p-3">Validation Message</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-850">
                  {analyzedRows.map((row, idx) => (
                    <tr
                      key={idx}
                      className={`hover:bg-dark-900/30 transition-colors ${
                        row.validation_error 
                          ? 'bg-red-500/5' 
                          : row.is_duplicate 
                          ? 'bg-amber-500/5' 
                          : ''
                      }`}
                    >
                      <td className="p-3">
                        {row.validation_error ? (
                          <span className="text-red-400 font-bold">Failed</span>
                        ) : row.is_duplicate ? (
                          <span className="text-amber-400 font-bold">Duplicate</span>
                        ) : (
                          <span className="text-green-450 font-bold flex items-center gap-1"><Check className="w-3.5 h-3.5" /> Parsed</span>
                        )}
                      </td>
                      <td className="p-3 font-mono">
                        {row.date ? new Date(row.date).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="p-3">
                        <input
                          type="text"
                          value={row.description || ''}
                          onChange={(e) => handleRowChange(idx, 'description', e.target.value)}
                          className="bg-transparent border-b border-transparent focus:border-brand-500 focus:bg-dark-950 px-2 py-1 rounded text-dark-200 outline-none w-full"
                        />
                      </td>
                      <td className="p-3 text-right font-mono font-bold">
                        <input
                          type="number"
                          value={row.amount || ''}
                          onChange={(e) => handleRowChange(idx, 'amount', parseFloat(e.target.value))}
                          className="bg-transparent border-b border-transparent focus:border-brand-500 focus:bg-dark-950 px-2 py-1 rounded text-dark-200 text-right outline-none w-24"
                        />
                      </td>
                      <td className="p-3">
                        <select
                          value={row.category_id || row.suggested_category_id || ''}
                          onChange={(e) => handleRowChange(idx, 'category_id', parseInt(e.target.value))}
                          className="bg-dark-950 border border-dark-800 rounded-lg px-2 py-1 text-xs text-dark-200 focus:border-brand-500 outline-none"
                        >
                          <option value="">-- No Category --</option>
                          {categories.map(c => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                          ))}
                        </select>
                        {row.suggested_category_id && !row.category_id && (
                          <span className="text-[10px] text-brand-400 block mt-1">Suggested</span>
                        )}
                      </td>
                      <td className="p-3 text-dark-500">
                        {row.validation_error || (row.is_duplicate ? `Duplicate entry detected.` : 'Ready')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex justify-between items-center pt-4">
              <Button variant="secondary" onClick={() => setStep(2)} className="flex items-center gap-1.5 text-xs py-2">
                <ArrowLeft className="w-4 h-4" /> Previous
              </Button>
              <Button
                variant="primary"
                onClick={handleExecuteImport}
                disabled={loading}
                className="flex items-center gap-1.5 text-xs py-2 bg-green-600 hover:bg-green-500 border-green-700 text-white"
              >
                {loading ? <RotateCw className="w-4 h-4 animate-spin" /> : <>Finalize Upload <Check className="w-4 h-4" /></>}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Step 4: Import Complete Summary */}
      {step === 4 && importSummary && (
        <Card title="Import Completed Summary" subtitle="Review batch results details">
          <div className="text-center py-8 space-y-6 max-w-md mx-auto">
            <div className="w-16 h-16 bg-green-500/10 border border-green-500/30 text-green-550 rounded-full flex items-center justify-center mx-auto scale-110">
              <Check className="w-8 h-8" />
            </div>
            
            <div className="space-y-1">
              <h3 className="text-xl font-bold text-dark-50">Statement Upload Finalized!</h3>
              <p className="text-xs text-dark-400">Your bank transactions were processed inside ExpenseFlow ledger.</p>
            </div>

            <div className="bg-dark-900 border border-dark-850 p-4 rounded-2xl grid grid-cols-3 gap-2.5 text-xs text-left">
              <div>
                <p className="text-[10px] uppercase font-bold text-dark-500">Imported</p>
                <p className="text-lg font-black text-green-400 mt-1">{importSummary.rows_imported}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase font-bold text-dark-500">Duplicates Skipped</p>
                <p className="text-lg font-black text-amber-500 mt-1">{importSummary.rows_skipped}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase font-bold text-dark-500">Failed / Errors</p>
                <p className="text-lg font-black text-red-500 mt-1">{importSummary.rows_failed}</p>
              </div>
            </div>

            <div className="flex gap-4">
              <Button
                variant="secondary"
                onClick={() => {
                  setStep(1);
                  setFile(null);
                  setRawRows([]);
                  setHeaders([]);
                }}
                className="flex-1 py-2 text-xs"
              >
                Import Another Statement
              </Button>
              <Button
                variant="primary"
                onClick={() => navigate('/dashboard')}
                className="flex-1 py-2 text-xs"
              >
                Go to Dashboard
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default ImportWizard;
