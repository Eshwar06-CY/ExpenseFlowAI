import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  ArrowRight, Shield, Wallet, Sparkles, TrendingUp,
  Layers, CheckCircle, Database, Cpu, Activity, Zap,
  Play, Lock, RefreshCw, BarChart3, HelpCircle, FileText, Globe
} from 'lucide-react';
import Button from '../components/Common/Button';
import ThreeCanvas from '../components/Motion/ThreeCanvas';
import TiltCard from '../components/Motion/TiltCard';
import MagneticButton from '../components/Motion/MagneticButton';
import AIOrb from '../components/Motion/AIOrb';
import ExplanationPanel from '../components/XAI/ExplanationPanel';
import WhyButton from '../components/XAI/WhyButton';

const Landing = () => {
  const navigate = useNavigate();
  const [billingPeriod, setBillingPeriod] = useState('monthly');

  // Scene 5: Streaming AI State
  const [streamText, setStreamText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const sampleAnswer = "Based on your 30-day forecast and current net monthly surplus of ₹38,500, a ₹1.2 Lakh Europe trip is feasible if scheduled in Q4. Your emergency reserve will remain intact at 4.2 months.";

  const handleStartStream = () => {
    setStreamText('');
    setIsStreaming(true);
    let i = 0;
    const interval = setInterval(() => {
      if (i < sampleAnswer.length) {
        setStreamText((prev) => prev + sampleAnswer.charAt(i));
        i++;
      } else {
        clearInterval(interval);
        setIsStreaming(false);
      }
    }, 25);
  };

  // Scene 6: Digital Twin Simulation State
  const [simScenario, setSimScenario] = useState('bonus'); // 'bonus' | 'laptop' | 'salary'
  const simOutputs = {
    bonus: { delta: '+₹50,000', health: '94/100', text: 'Bonus increases emergency reserve by 1.2 months.' },
    laptop: { delta: '-₹1,20,000', health: '82/100', text: 'Laptop purchase temporary reduces net liquid cash.' },
    salary: { delta: '+₹25,000/mo', health: '96/100', text: 'Salary increase accelerates emergency fund goal by 4 months.' },
  };

  // Scene 9: XAI Preview State
  const [xaiModalOpen, setXaiModalOpen] = useState(false);

  return (
    <div className="min-h-screen bg-dark-950 text-dark-100 flex flex-col font-sans relative overflow-x-hidden">
      {/* 3D WebGL Canvas Backdrop */}
      <ThreeCanvas />

      {/* Floating Public Navigation Header */}
      <nav className="glass-nav h-20 w-full fixed top-0 left-0 z-50 px-6 md:px-12 flex items-center justify-between border-b border-dark-900/60 bg-dark-950/70 backdrop-blur-xl">
        <div className="flex items-center gap-2">
          <img src="/branding/gemini-svg.svg" alt="ExpenseFlow AI Logo" className="h-9 object-contain" />
        </div>

        <div className="hidden md:flex items-center gap-8 text-xs font-bold text-dark-300 uppercase tracking-wider">
          <a href="#chaos" className="hover:text-indigo-400 transition-colors">Experience</a>
          <a href="#simulator" className="hover:text-indigo-400 transition-colors">Digital Twin</a>
          <a href="#ecosystem" className="hover:text-indigo-400 transition-colors">Ecosystem</a>
          <a href="#pricing" className="hover:text-indigo-400 transition-colors">Pricing</a>
        </div>

        <div className="flex items-center gap-4">
          <Link to="/login" className="text-xs font-bold text-dark-300 hover:text-white transition-colors uppercase tracking-wider">
            Log In
          </Link>
          <MagneticButton onClick={() => navigate('/register')} icon={<ArrowRight size={14} />}>
            Launch App
          </MagneticButton>
        </div>
      </nav>

      {/* ─── SCENE 1: CINEMATIC HERO & SIGNATURE AI ORB ───────────────────── */}
      <section className="pt-36 pb-24 px-6 md:px-12 max-w-7xl mx-auto flex flex-col items-center text-center relative z-10 space-y-8">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-bold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5 animate-pulse" />
          <span>The Future of Personal Finance</span>
        </div>

        {/* Signature AI Orb */}
        <AIOrb size={240} className="my-2" />

        <h1 className="text-4xl md:text-6xl lg:text-7xl font-black tracking-tight text-white leading-tight max-w-4xl">
          Your AI Financial<br />
          <span className="bg-gradient-to-r from-indigo-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
            Operating System.
          </span>
        </h1>

        <p className="text-dark-300 text-sm md:text-lg max-w-2xl leading-relaxed">
          Stop managing money manually. ExpenseFlowAI automatically interprets predictions, simulates decisions in a virtual Digital Twin, and executes verified strategy roadmaps.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4 pt-4">
          <MagneticButton onClick={() => navigate('/register')} icon={<ArrowRight size={16} />}>
            Start Free Experience
          </MagneticButton>
          <button
            type="button"
            onClick={() => {
              const el = document.getElementById('chaos');
              if (el) el.scrollIntoView({ behavior: 'smooth' });
            }}
            className="px-6 py-3 rounded-2xl bg-dark-900 hover:bg-dark-850 text-white text-xs font-bold border border-dark-800 flex items-center space-x-2 transition-all"
          >
            <Play size={14} className="text-indigo-400" />
            <span>Watch Experience</span>
          </button>
        </div>
      </section>

      {/* ─── SCENE 2 & 3: FINANCIAL CHAOS FREEZE & AI TAKES CONTROL ───────── */}
      <section id="chaos" className="py-24 px-6 md:px-12 max-w-7xl mx-auto space-y-12 relative z-10">
        <div className="text-center space-y-3">
          <span className="text-xs font-bold uppercase tracking-widest text-indigo-400">Scene 02 & 03</span>
          <h2 className="text-3xl md:text-5xl font-black text-white">One AI. Every Financial Decision.</h2>
          <p className="text-dark-400 text-xs md:text-sm max-w-xl mx-auto">
            Financial chaos absorbs into clean structure as FinanceEngine calculates verified metrics.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <TiltCard className="p-6 space-y-4 border-l-4 border-l-rose-500">
            <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider bg-rose-500/10 px-2 py-0.5 rounded">Before ExpenseFlow</span>
            <h3 className="text-base font-bold text-white">Financial Chaos</h3>
            <p className="text-xs text-dark-300">Untracked bill due dates, silent budget overruns, and uncertain savings timelines cause financial anxiety.</p>
          </TiltCard>

          <TiltCard className="p-6 space-y-4 border-l-4 border-l-indigo-500">
            <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider bg-indigo-500/10 px-2 py-0.5 rounded">AI In Control</span>
            <h3 className="text-base font-bold text-white">Automated Intelligence</h3>
            <p className="text-xs text-dark-300">AI memory tracks user habits while FinanceEngine runs 30-day forecasts and anomaly detectors 24/7.</p>
          </TiltCard>

          <TiltCard className="p-6 space-y-4 border-l-4 border-l-emerald-500">
            <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider bg-emerald-500/10 px-2 py-0.5 rounded">Proven Result</span>
            <h3 className="text-base font-bold text-white">Command & Clarity</h3>
            <p className="text-xs text-dark-300">Health scores increase by +14 points as cashflow surpluses are automatically allocated toward emergency reserves.</p>
          </TiltCard>
        </div>
      </section>

      {/* ─── SCENE 4 & 5: STREAMING AI DEMO ───────────────────────────────── */}
      <section className="py-24 px-6 md:px-12 max-w-5xl mx-auto space-y-8 relative z-10">
        <div className="text-center space-y-3">
          <span className="text-xs font-bold uppercase tracking-widest text-indigo-400">Scene 05 • Real-Time AI</span>
          <h2 className="text-3xl md:text-4xl font-black text-white">Live Streaming AI Conversation</h2>
          <p className="text-dark-400 text-xs md:text-sm">Test real-time token streaming directly from Ollama local models.</p>
        </div>

        <div className="p-6 rounded-3xl bg-dark-900 border border-dark-800 space-y-4 shadow-2xl">
          <div className="flex items-center justify-between border-b border-dark-850 pb-4">
            <div className="flex items-center space-x-2">
              <span className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Sparkles size={16} />
              </span>
              <span className="text-xs font-bold text-white">Prompt: "Can I afford a ₹1.2 Lakh Europe trip?"</span>
            </div>
            <button
              type="button"
              onClick={handleStartStream}
              disabled={isStreaming}
              className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center space-x-1.5"
            >
              <RefreshCw size={12} className={isStreaming ? 'animate-spin' : ''} />
              <span>{isStreaming ? 'Streaming...' : 'Run Demo Stream'}</span>
            </button>
          </div>

          <div className="p-4 rounded-2xl bg-dark-950 border border-dark-850 min-h-[100px] text-xs text-dark-200 leading-relaxed font-mono">
            {streamText || "Click 'Run Demo Stream' above to witness token-by-token real-time streaming..."}
            {isStreaming && <span className="inline-block w-2 h-4 bg-indigo-400 ml-1 animate-pulse" />}
          </div>
        </div>
      </section>

      {/* ─── SCENE 6: DIGITAL TWIN SIMULATOR ───────────────────────────────── */}
      <section id="simulator" className="py-24 px-6 md:px-12 max-w-7xl mx-auto space-y-8 relative z-10">
        <div className="text-center space-y-3">
          <span className="text-xs font-bold uppercase tracking-widest text-indigo-400">Scene 06 • Digital Twin</span>
          <h2 className="text-3xl md:text-5xl font-black text-white">Safely Test What-If Financial Decisions</h2>
          <p className="text-dark-400 text-xs md:text-sm">Simulate major financial changes without touching live account balances.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { id: 'bonus', title: '₹50,000 Bonus', subtitle: 'Lump-sum windfall' },
            { id: 'laptop', title: 'Buy ₹1.2L Laptop', subtitle: 'One-off capital expenditure' },
            { id: 'salary', title: '+₹25,000 Salary Increase', subtitle: 'Permanent monthly income delta' }
          ].map((scen) => (
            <button
              key={scen.id}
              type="button"
              onClick={() => setSimScenario(scen.id)}
              className={`p-5 rounded-2xl border text-left transition-all ${
                simScenario === scen.id
                  ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-xl'
                  : 'bg-dark-900 border-dark-800 text-dark-300 hover:border-dark-700'
              }`}
            >
              <p className="text-sm font-bold text-white">{scen.title}</p>
              <p className="text-xs text-dark-400 mt-1">{scen.subtitle}</p>
            </button>
          ))}
        </div>

        {/* Simulation Output Card */}
        <div className="p-6 rounded-3xl bg-dark-900 border border-dark-800 flex flex-col md:flex-row items-center justify-between gap-6 shadow-2xl">
          <div className="space-y-2">
            <span className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
              Simulated Health Score: {simOutputs[simScenario].health}
            </span>
            <h3 className="text-xl font-bold text-white">Impact Delta: {simOutputs[simScenario].delta}</h3>
            <p className="text-xs text-dark-300 max-w-xl">{simOutputs[simScenario].text}</p>
          </div>

          <Button variant="primary" onClick={() => navigate('/register')} icon={<ArrowRight size={14} />}>
            Open Full Twin Simulator
          </Button>
        </div>
      </section>

      {/* ─── SCENE 8 & 9: EXPLAINABLE AI PREVIEW ───────────────────────────── */}
      <section className="py-24 px-6 md:px-12 max-w-5xl mx-auto space-y-8 relative z-10">
        <div className="text-center space-y-3">
          <span className="text-xs font-bold uppercase tracking-widest text-indigo-400">Scene 09 • Explainable AI</span>
          <h2 className="text-3xl md:text-4xl font-black text-white">Complete AI Transparency & Trust</h2>
          <p className="text-dark-400 text-xs md:text-sm">Click "Why?" on any recommendation to view verified metrics and data sources.</p>
        </div>

        <div className="p-6 rounded-3xl bg-dark-900 border border-dark-800 space-y-4 shadow-2xl flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold uppercase text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
              Budget Warning
            </span>
            <h3 className="text-sm font-bold text-white mt-1">Reduce Dining Expenses by ₹3,500/month</h3>
            <p className="text-xs text-dark-400">Dining category exceeded limit by 18% in the last 3 weeks.</p>
          </div>

          <WhyButton onClick={() => setXaiModalOpen(true)} label="Why?" />
        </div>

        <ExplanationPanel
          feature="budget"
          targetId="dining_limit"
          isOpen={xaiModalOpen}
          onClose={() => setXaiModalOpen(false)}
        />
      </section>

      {/* ─── SCENE 11: ECOSYSTEM GRAPH ────────────────────────────────────── */}
      <section id="ecosystem" className="py-24 px-6 md:px-12 max-w-7xl mx-auto space-y-8 relative z-10">
        <div className="text-center space-y-3">
          <span className="text-xs font-bold uppercase tracking-widest text-indigo-400">Scene 11 • Ecosystem</span>
          <h2 className="text-3xl md:text-5xl font-black text-white">ExpenseFlowAI Product Ecosystem</h2>
          <p className="text-dark-400 text-xs md:text-sm">12 fully integrated modules powered by Google Gemini 2.5 Flash intelligence.</p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            'FinanceEngine Core', 'Forecast Engine', 'Strategy Planner', 'Digital Twin',
            'Streaming AI Chat', 'Smart Notifications', 'AI Digest Reports', 'Explainable AI',
            'AI Memory System', 'Personalization Center', 'Automations Engine', 'Workspaces'
          ].map((item, idx) => (
            <div key={idx} className="p-4 rounded-2xl bg-dark-900 border border-dark-800 text-xs font-bold text-white flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-indigo-500" />
              <span>{item}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ─── SCENE 12: FINAL CINEMATIC CTA ─────────────────────────────────── */}
      <section className="py-32 px-6 md:px-12 max-w-5xl mx-auto text-center space-y-8 relative z-10 border-t border-dark-850">
        <img src="/branding/gemini-svg.svg" alt="ExpenseFlow Logo" className="h-12 mx-auto object-contain" />
        <h2 className="text-4xl md:text-6xl font-black text-white tracking-tight">
          Stop Managing Money.<br />
          <span className="bg-gradient-to-r from-indigo-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
            Start Directing It.
          </span>
        </h2>
        <p className="text-xs md:text-sm text-dark-400 max-w-xl mx-auto">
          Experience the flagship AI Financial Operating System built with React, FastAPI, SQLAlchemy, and Google Gemini 2.5 Flash.
        </p>
        <div className="pt-4">
          <MagneticButton onClick={() => navigate('/register')} icon={<ArrowRight size={16} />}>
            Launch Free Application
          </MagneticButton>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-dark-900 text-center text-xs text-dark-500">
        © 2026 ExpenseFlowAI. All rights reserved. Built with React, FastAPI, and Ollama.
      </footer>
    </div>
  );
};

export default Landing;
