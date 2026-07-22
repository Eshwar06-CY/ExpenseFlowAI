import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  ArrowRight, Shield, Wallet, Sparkles, TrendingUp, 
  Layers, CheckCircle, Database, Cpu, Activity
} from 'lucide-react';
import Card from '../components/Common/Card';
import Button from '../components/Common/Button';

const Landing = () => {
  const navigate = useNavigate();
  const [billingPeriod, setBillingPeriod] = useState('monthly'); // 'monthly' | 'annually'

  const features = [
    {
      title: "Automated Rules",
      description: "Automatically categorize transactions and keep your records tidy with smart user-defined rules.",
      icon: Sparkles
    },
    {
      title: "Real-time Tracking",
      description: "Instantly stream income and expenses through clear interactive ledgers.",
      icon: Activity
    },
    {
      title: "Multi-Currency Pockets",
      description: "Record balances in USD, EUR, GBP, or INR with live exchange conversions automatically.",
      icon: Wallet
    },
    {
      title: "Secure Workspaces",
      description: "Secure workspace environments driven by standard JWT authorizations and encrypted parameters.",
      icon: Shield
    }
  ];

  const pricing = [
    {
      name: "Starter",
      price: billingPeriod === 'monthly' ? '$0' : '$0',
      description: "Perfect for personal expense tracking",
      features: [
        "Up to 100 transactions/mo",
        "Single workspace ledger",
        "Basic manual categories",
        "Weekly email summaries"
      ],
      cta: "Start Free",
      popular: false
    },
    {
      name: "Pro",
      price: billingPeriod === 'monthly' ? '$29' : '$19',
      description: "Perfect for freelancers and small teams",
      features: [
        "Unlimited monthly transactions",
        "Automated categorization rules",
        "API developer access keys",
        "Multi-currency conversion support",
        "Real-time expense anomaly alerts"
      ],
      cta: "Get Pro Started",
      popular: true
    },
    {
      name: "Enterprise",
      price: "Custom",
      description: "For scaling institutions & businesses",
      features: [
        "Multiple tenant workspaces",
        "Dedicated database clusters",
        "SAML SSO & custom RBAC permissions",
        "Dedicated account manager",
        "Custom rule building templates"
      ],
      cta: "Contact Sales",
      popular: false
    }
  ];

  const roadmap = [
    { phase: "Phase 1", title: "Core Foundation", desc: "Decoupled FastAPI backend and React Vite project architecture.", done: true },
    { phase: "Phase 2", title: "Database & Authentication", desc: "Alembic migrations, JWT logins, and secure user registries.", done: true },
    { phase: "Phase 3", title: "Ledger CRUD APIs", desc: "FastAPI CRUD endpoints for transactions, income streams, and categories.", done: true },
    { phase: "Phase 4", title: "Forecasting & Budgets", desc: "Advanced scenario simulation tools and automated rule engine structures.", done: true }
  ];

  return (
    <div className="min-h-screen bg-dark-950 text-dark-100 flex flex-col font-sans relative overflow-x-hidden">
      {/* Background glow animations */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-brand-500/10 rounded-full blur-3xl"></div>
      <div className="absolute top-[30%] right-[-10%] w-[600px] h-[600px] bg-violet-600/5 rounded-full blur-3xl"></div>

      {/* Floating Public Navigation */}
      <nav className="glass-nav h-20 w-full fixed top-0 left-0 z-50 px-6 md:px-12 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <img src="/branding/gemini-svg.svg" alt="ExpenseFlow AI Logo" className="h-9 object-contain" />
        </div>

        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-dark-300">
          <a href="#features" className="hover:text-brand-400 transition-colors">Features</a>
          <a href="#pricing" className="hover:text-brand-400 transition-colors">Pricing</a>
          <a href="#roadmap" className="hover:text-brand-400 transition-colors">Roadmap</a>
        </div>

        <div className="flex items-center gap-4">
          <Link to="/login" className="text-sm font-medium text-dark-300 hover:text-white transition-colors">
            Log In
          </Link>
          <Button variant="primary" size="sm" onClick={() => navigate('/register')} className="flex items-center gap-1.5 font-semibold">
            Get Started <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-40 pb-20 px-6 md:px-12 max-w-7xl mx-auto flex flex-col items-center text-center relative z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-semibold uppercase tracking-wider mb-6">
          <Sparkles className="w-3.5 h-3.5 animate-pulse" /> Phase 1 Foundation Active
        </div>

        <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight text-dark-50 leading-tight max-w-4xl font-sans">
          Track smarter.<br />
          <span className="bg-gradient-to-r from-brand-400 via-violet-400 to-indigo-300 bg-clip-text text-transparent">
            Save better.
          </span>
        </h1>

        <p className="text-dark-400 text-base md:text-xl max-w-2xl mt-6 leading-relaxed">
          A beautiful, calm personal finance manager that makes tracking your money effortless. Set targets, create automatic rules, and see where your money goes.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4 mt-10">
          <Button variant="primary" size="lg" onClick={() => navigate('/register')} className="flex items-center gap-2 px-8 font-semibold">
            Create Free Pocket <ArrowRight className="w-5 h-5" />
          </Button>
          <Button variant="secondary" size="lg" onClick={() => navigate('/login')} className="px-8 font-semibold">
            Access Dashboard
          </Button>
        </div>

        {/* Dashboard Frame Mockup */}
        <div className="w-full mt-20 rounded-2xl border border-dark-800 bg-dark-950/60 p-3 md:p-4 shadow-2xl relative">
          <div className="absolute top-[-2%] left-[50%] -translate-x-1/2 w-[80%] h-[1px] bg-gradient-to-r from-transparent via-brand-500 to-transparent"></div>
          <div className="rounded-xl border border-dark-850 overflow-hidden bg-dark-900/40">
            {/* Mock Dashboard preview header */}
            <div className="h-10 bg-dark-950/80 border-b border-dark-850 flex items-center px-4 justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500/60"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/60"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-green-500/60"></span>
              </div>
              <div className="text-[10px] text-dark-500 font-mono">https://app.expenseflow.ai/dashboard</div>
              <div className="w-6"></div>
            </div>
            
            {/* Mock stats layout */}
            <div className="p-6 grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
              <div className="p-4 rounded-lg bg-dark-950 border border-dark-850">
                <span className="text-[10px] text-dark-500 font-semibold uppercase tracking-wider block">Total Balance</span>
                <span className="text-xl font-bold text-dark-50 block mt-1">$12,480.00</span>
                <span className="text-[10px] text-green-400 font-medium block mt-1.5">+12.5% vs last month</span>
              </div>
              <div className="p-4 rounded-lg bg-dark-950 border border-dark-850">
                <span className="text-[10px] text-dark-500 font-semibold uppercase tracking-wider block">Monthly Expenses</span>
                <span className="text-xl font-bold text-dark-50 block mt-1">$3,240.50</span>
                <span className="text-[10px] text-red-400 font-medium block mt-1.5">+4.2% vs last month</span>
              </div>
              <div className="p-4 rounded-lg bg-dark-950 border border-dark-850">
                <span className="text-[10px] text-dark-500 font-semibold uppercase tracking-wider block">Smart Budget Advisor</span>
                <span className="text-xs font-medium text-brand-300 block mt-1">1 automatic rule action completed.</span>
                <span className="text-[10px] text-dark-400 block mt-1.5">Shortcuts active.</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-6 md:px-12 max-w-7xl mx-auto w-full relative z-10 border-t border-dark-900/60">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-dark-50">Designed for Scalable Operations</h2>
          <p className="text-dark-400 text-sm mt-3">All standard modules are engineered on structured layers to optimize stability and clean architecture.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feat) => {
            const Icon = feat.icon;
            return (
              <Card key={feat.title} className="hover-lift p-6 border border-dark-850">
                <div className="w-10 h-10 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 mb-5">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-dark-100">{feat.title}</h3>
                <p className="text-xs text-dark-450 leading-relaxed mt-2">{feat.description}</p>
              </Card>
            );
          })}
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-24 px-6 md:px-12 max-w-7xl mx-auto w-full relative z-10 border-t border-dark-900/60">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-dark-50">Predictable Ledger Pricing</h2>
          <p className="text-dark-400 text-sm mt-3">Start with our foundational package and scale as your ledger ingestion grows.</p>

          {/* Toggle */}
          <div className="inline-flex items-center gap-1 bg-dark-900 border border-dark-800 rounded-full p-1 mt-8">
            <button 
              onClick={() => setBillingPeriod('monthly')}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
                billingPeriod === 'monthly' ? 'bg-brand-600 text-white shadow-md shadow-brand-600/10' : 'text-dark-400 hover:text-dark-200'
              }`}
            >
              Monthly
            </button>
            <button 
              onClick={() => setBillingPeriod('annually')}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
                billingPeriod === 'annually' ? 'bg-brand-600 text-white shadow-md shadow-brand-600/10' : 'text-dark-400 hover:text-dark-200'
              }`}
            >
              Annually (Save 30%)
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
          {pricing.map((plan) => (
            <div 
              key={plan.name} 
              className={`rounded-2xl p-8 bg-dark-900/50 border relative flex flex-col justify-between ${
                plan.popular 
                  ? 'border-brand-500 shadow-xl shadow-brand-500/5' 
                  : 'border-dark-850'
              }`}
            >
              {plan.popular && (
                <div className="absolute top-[-12px] right-6 px-3 py-1 rounded-full bg-brand-600 text-white text-[10px] font-bold uppercase tracking-wider">
                  Popular Option
                </div>
              )}
              
              <div>
                <h3 className="text-lg font-bold text-dark-50">{plan.name}</h3>
                <p className="text-xs text-dark-400 mt-1">{plan.description}</p>

                <div className="my-6 flex items-baseline">
                  <span className="text-4xl font-extrabold text-dark-50 font-sans tracking-tight">{plan.price}</span>
                  {plan.price !== 'Custom' && (
                    <span className="text-xs text-dark-400 ml-2">/ month{billingPeriod === 'annually' && ' (billed annually)'}</span>
                  )}
                </div>

                <ul className="space-y-3.5 border-t border-dark-850 pt-6">
                  {plan.features.map((feat) => (
                    <li key={feat} className="flex items-start gap-2.5 text-xs text-dark-300">
                      <CheckCircle className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mt-8">
                <Button 
                  onClick={() => navigate('/register')} 
                  variant={plan.popular ? 'primary' : 'outline'} 
                  className="w-full font-semibold py-2.5"
                >
                  {plan.cta}
                </Button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Roadmap Section */}
      <section id="roadmap" className="py-24 px-6 md:px-12 max-w-7xl mx-auto w-full relative z-10 border-t border-dark-900/60 mb-12">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-dark-50">SaaS Roadmap Timeline</h2>
          <p className="text-dark-400 text-sm mt-3">Follow our phased engineering architecture layout to see where we are headed.</p>
        </div>

        <div className="max-w-3xl mx-auto relative border-l border-dark-800 ml-4 md:ml-auto">
          {roadmap.map((item, index) => (
            <div key={item.phase} className="mb-10 pl-6 relative">
              {/* Timeline circle node */}
              <div className={`absolute left-[-9px] top-1.5 w-4 h-4 rounded-full border-4 ${
                item.done 
                  ? 'bg-brand-500 border-dark-950 ring-2 ring-brand-500/20' 
                  : 'bg-dark-800 border-dark-950'
              }`}></div>
              
              <div className="p-5 rounded-xl bg-dark-900/40 border border-dark-850">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-brand-400 tracking-wider uppercase">{item.phase}</span>
                  {item.done && (
                    <span className="px-1.5 py-0.5 rounded bg-green-500/10 border border-green-500/20 text-green-400 text-[8px] font-semibold uppercase">
                      Complete
                    </span>
                  )}
                </div>
                <h3 className="text-base font-bold text-dark-100 mt-1">{item.title}</h3>
                <p className="text-xs text-dark-400 mt-1.5 leading-relaxed">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Call to Action Banner */}
      <section className="mx-6 md:mx-12 max-w-7xl md:w-full md:mx-auto mb-24 rounded-2xl bg-gradient-to-r from-brand-900/40 to-violet-950/20 border border-brand-500/10 p-12 text-center relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-brand-500/15 rounded-full blur-3xl"></div>
        <div className="relative z-10 space-y-6">
          <h2 className="text-3xl font-extrabold text-dark-50 tracking-tight">Ready to optimize your financial ledger?</h2>
          <p className="text-dark-400 text-sm max-w-md mx-auto">Deploy a free local development database workspace or sign up to use the Pro dashboard.</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button variant="primary" size="lg" onClick={() => navigate('/register')} className="px-8 font-semibold">
              Get Started Free
            </Button>
            <Link to="/login" className="text-sm font-semibold text-dark-300 hover:text-white transition-colors">
              Talk to an advisor &rarr;
            </Link>
          </div>
        </div>
      </section>

      {/* Landing Footer */}
      <footer className="bg-dark-950 border-t border-dark-900 py-12 px-6 md:px-12 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-brand-600 to-violet-500 flex items-center justify-center font-bold text-white text-sm shadow-md shadow-brand-500/10">
              E
            </div>
            <span className="font-semibold text-sm text-dark-50 tracking-tight">ExpenseFlow AI</span>
          </div>
          <div className="text-xs text-dark-500">
            &copy; {new Date().getFullYear()} ExpenseFlow AI. All rights reserved. Built with Vite, React, and FastAPI.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
