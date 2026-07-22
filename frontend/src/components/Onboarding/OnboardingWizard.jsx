import React, { useState } from 'react';
import { Sparkles, Landmark, ArrowDownLeft, ArrowUpRight, Target, ArrowRight } from 'lucide-react';
import api from '../../services/api';
import Card from '../Common/Card';
import Button from '../Common/Button';

export default function OnboardingWizard({ onComplete, onSkip }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Step 1: Account
  const [accountName, setAccountName] = useState('My Everyday Cash');
  const [accountType, setAccountType] = useState('cash');
  const [accountBalance, setAccountBalance] = useState('100');

  // Step 2: Income
  const [incomeDesc, setIncomeDesc] = useState('Monthly Allowance');
  const [incomeAmount, setIncomeAmount] = useState('150');

  // Step 3: Expense
  const [expenseDesc, setExpenseDesc] = useState('Bought Snacks');
  const [expenseAmount, setExpenseAmount] = useState('20');

  // Step 4: Savings Goal
  const [goalName, setGoalName] = useState('New Video Game');
  const [goalTarget, setGoalTarget] = useState('60');

  // Created IDs to link transactions
  const [createdAccountId, setCreatedAccountId] = useState(null);

  const handleNext = async () => {
    setError('');
    setLoading(true);

    try {
      if (step === 1) {
        // Create first Account
        if (!accountName.trim()) throw new Error('Please name your pocket or account.');
        const balanceVal = parseFloat(accountBalance) || 0;

        const res = await api.post('/accounts/', {
          name: accountName,
          type: accountType,
          balance: balanceVal,
          currency: 'USD',
        });
        setCreatedAccountId(res.data.id);
        setStep(2);
      } else if (step === 2) {
        // Create first Income
        const amountVal = parseFloat(incomeAmount) || 0;
        if (amountVal <= 0) throw new Error('Please enter a positive income amount.');

        await api.post('/transactions/', {
          type: 'income',
          amount: amountVal,
          description: incomeDesc,
          date: new Date().toISOString(),
          account_id: createdAccountId,
          category_id: null,
        });
        setStep(3);
      } else if (step === 3) {
        // Create first Expense
        const amountVal = parseFloat(expenseAmount) || 0;
        if (amountVal <= 0) throw new Error('Please enter a positive spending amount.');

        await api.post('/transactions/', {
          type: 'expense',
          amount: amountVal,
          description: expenseDesc,
          date: new Date().toISOString(),
          account_id: createdAccountId,
          category_id: null,
        });
        setStep(4);
      } else if (step === 4) {
        // Create savings goal
        const targetVal = parseFloat(goalTarget) || 0;
        if (targetVal <= 0) throw new Error('Please enter a positive goal budget target.');

        await api.post('/goals/', {
          name: goalName,
          target_amount: targetVal,
          current_amount: 0,
          target_date: null,
        });

        // Set status in localStorage and complete
        localStorage.setItem('ef_onboarding_completed', 'true');
        onComplete();
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'An error occurred during this step.');
    } finally {
      setLoading(false);
    }
  };

  const skipSetup = () => {
    localStorage.setItem('ef_onboarding_skipped', 'true');
    onSkip();
  };

  const stepsLabel = [
    'Where is your money?',
    'Record some income',
    'Record some expenses',
    'Set a saving target',
  ];

  return (
    <div className="onboarding-wizard-container fixed inset-0 z-50 flex items-center justify-center p-4 bg-dark-950/80 backdrop-blur-md">
      <div className="absolute inset-0 bg-gradient-to-tr from-brand-600/5 to-violet-500/5" />

      <div className="w-full max-w-lg z-10 animate-scale-up">
        {/* Welcome Info Box */}
        <div className="text-center mb-6">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-500 items-center justify-center font-bold text-white shadow-lg shadow-brand-500/20 mb-3 border border-brand-400/20">
            <Sparkles className="w-6 h-6 animate-pulse" />
          </div>
          <h2 className="text-2xl font-extrabold text-dark-50 tracking-tight font-sans">
            Let's Setup Your Pocket!
          </h2>
          <p className="text-[13px] text-dark-400 mt-1">
            Get up and running in under two minutes with our quick checklist.
          </p>
        </div>

        <Card isGlass={true} className="p-6 relative overflow-hidden">
          {/* Progress Indicator */}
          <div className="mb-6">
            <div className="flex justify-between items-center text-[10px] uppercase font-extrabold text-brand-400 tracking-wider mb-2">
              <span>Step {step} of 4</span>
              <span>{stepsLabel[step - 1]}</span>
            </div>
            <div className="w-full bg-dark-900 rounded-full h-1.5 overflow-hidden border border-dark-850">
              <div
                className="bg-gradient-to-r from-brand-500 to-indigo-500 h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${step * 25}%` }}
              />
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold">
              {error}
            </div>
          )}

          {/* Setup wizard inputs */}
          <div className="space-y-4 min-h-[160px] flex flex-col justify-center">
            {step === 1 && (
              <div className="space-y-4">
                <div className="flex items-center gap-3 p-3 bg-brand-600/5 rounded-xl border border-brand-500/10">
                  <Landmark className="w-6 h-6 text-brand-400 shrink-0" />
                  <p className="text-xs text-dark-350 leading-relaxed font-semibold">
                    First, let's create a pocket. This is where you keep your cash, card, or bank savings.
                  </p>
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-dark-400 uppercase tracking-wider mb-1.5">
                    What is this pocket called?
                  </label>
                  <input
                    type="text"
                    value={accountName}
                    onChange={(e) => setAccountName(e.target.value)}
                    placeholder="e.g. Cash Wallet or Bank Account"
                    className="w-full bg-dark-950 border border-dark-850 rounded-xl px-4 py-2.5 text-sm text-dark-200 placeholder-dark-600 outline-none focus:border-brand-500 transition-all font-semibold"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[11px] font-bold text-dark-400 uppercase tracking-wider mb-1.5">
                      Pocket Type
                    </label>
                    <select
                      value={accountType}
                      onChange={(e) => setAccountType(e.target.value)}
                      className="w-full bg-dark-950 border border-dark-850 rounded-xl px-3 py-2.5 text-sm text-dark-200 outline-none focus:border-brand-500 transition-all font-semibold"
                    >
                      <option value="cash">Cash Wallet</option>
                      <option value="bank">Bank Account</option>
                      <option value="credit">Credit Card</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[11px] font-bold text-dark-400 uppercase tracking-wider mb-1.5">
                      Starting Money (USD)
                    </label>
                    <input
                      type="number"
                      value={accountBalance}
                      onChange={(e) => setAccountBalance(e.target.value)}
                      placeholder="0"
                      className="w-full bg-dark-950 border border-dark-850 rounded-xl px-4 py-2.5 text-sm text-dark-200 placeholder-dark-600 outline-none focus:border-brand-500 transition-all font-mono font-semibold"
                    />
                  </div>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4">
                <div className="flex items-center gap-3 p-3 bg-emerald-600/5 rounded-xl border border-emerald-500/10">
                  <ArrowDownLeft className="w-6 h-6 text-emerald-400 shrink-0" />
                  <p className="text-xs text-dark-350 leading-relaxed font-semibold">
                    Awesome! Now let's record some money coming in. It could be allowance, salary, or a gift.
                  </p>
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-dark-400 uppercase tracking-wider mb-1.5">
                    What did you get paid for?
                  </label>
                  <input
                    type="text"
                    value={incomeDesc}
                    onChange={(e) => setIncomeDesc(e.target.value)}
                    placeholder="e.g. Monthly Allowance, Birthday Gift"
                    className="w-full bg-dark-950 border border-dark-850 rounded-xl px-4 py-2.5 text-sm text-dark-200 placeholder-dark-600 outline-none focus:border-brand-500 transition-all font-semibold"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-dark-400 uppercase tracking-wider mb-1.5">
                    Amount received (USD)
                  </label>
                  <input
                    type="number"
                    value={incomeAmount}
                    onChange={(e) => setIncomeAmount(e.target.value)}
                    placeholder="0"
                    className="w-full bg-dark-950 border border-dark-850 rounded-xl px-4 py-2.5 text-sm text-dark-200 placeholder-dark-600 outline-none focus:border-brand-500 transition-all font-mono font-semibold"
                  />
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-4">
                <div className="flex items-center gap-3 p-3 bg-rose-600/5 rounded-xl border border-rose-500/10">
                  <ArrowUpRight className="w-6 h-6 text-rose-400 shrink-0" />
                  <p className="text-xs text-dark-350 leading-relaxed font-semibold">
                    Let's record some money spent, like buying a snack, booking transport, or shopping.
                  </p>
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-dark-400 uppercase tracking-wider mb-1.5">
                    What did you spend money on?
                  </label>
                  <input
                    type="text"
                    value={expenseDesc}
                    onChange={(e) => setExpenseDesc(e.target.value)}
                    placeholder="e.g. Bought Snacks, Bus Ticket"
                    className="w-full bg-dark-950 border border-dark-850 rounded-xl px-4 py-2.5 text-sm text-dark-200 placeholder-dark-600 outline-none focus:border-brand-500 transition-all font-semibold"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-dark-400 uppercase tracking-wider mb-1.5">
                    Amount spent (USD)
                  </label>
                  <input
                    type="number"
                    value={expenseAmount}
                    onChange={(e) => setExpenseAmount(e.target.value)}
                    placeholder="0"
                    className="w-full bg-dark-950 border border-dark-850 rounded-xl px-4 py-2.5 text-sm text-dark-200 placeholder-dark-600 outline-none focus:border-brand-500 transition-all font-mono font-semibold"
                  />
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="space-y-4">
                <div className="flex items-center gap-3 p-3 bg-violet-600/5 rounded-xl border border-violet-500/10">
                  <Target className="w-6 h-6 text-violet-400 shrink-0" />
                  <p className="text-xs text-dark-350 leading-relaxed font-semibold">
                    Lastly, set a target to save money for. This keeps you focused and motivated!
                  </p>
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-dark-400 uppercase tracking-wider mb-1.5">
                    What are you saving for?
                  </label>
                  <input
                    type="text"
                    value={goalName}
                    onChange={(e) => setGoalName(e.target.value)}
                    placeholder="e.g. New Bicycle, Travel Trip"
                    className="w-full bg-dark-950 border border-dark-850 rounded-xl px-4 py-2.5 text-sm text-dark-200 placeholder-dark-600 outline-none focus:border-brand-500 transition-all font-semibold"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-dark-400 uppercase tracking-wider mb-1.5">
                    Target budget amount (USD)
                  </label>
                  <input
                    type="number"
                    value={goalTarget}
                    onChange={(e) => setGoalTarget(e.target.value)}
                    placeholder="0"
                    className="w-full bg-dark-950 border border-dark-850 rounded-xl px-4 py-2.5 text-sm text-dark-200 placeholder-dark-600 outline-none focus:border-brand-500 transition-all font-mono font-semibold"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Action buttons */}
          <div className="mt-8 pt-4 border-t border-dark-850 flex items-center justify-between">
            <button
              onClick={skipSetup}
              disabled={loading}
              className="text-[11px] font-bold uppercase tracking-wider text-dark-500 hover:text-dark-300 transition-colors"
            >
              Skip Setup
            </button>

            <Button
              onClick={handleNext}
              disabled={loading}
              className="flex items-center gap-1.5 text-xs font-bold"
            >
              {loading ? 'Processing...' : step === 4 ? 'Complete Onboarding' : 'Next Step'}
              {!loading && step < 4 && <ArrowRight size={14} />}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
