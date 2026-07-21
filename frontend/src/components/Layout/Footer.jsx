import React from 'react';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-dark-950/40 border-t border-dark-900/60 mt-auto py-8 px-6 md:px-8">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        {/* Brand Section */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-tr from-brand-600 to-violet-500 flex items-center justify-center font-bold text-white text-xs shadow-md shadow-brand-500/10">
              E
            </div>
            <span className="font-semibold text-sm text-dark-50 tracking-tight">ExpenseFlow AI</span>
          </div>
          <p className="text-xs text-dark-400">Track smarter. Save better. Powered by modern engineering.</p>
        </div>

        {/* Links Section */}
        <div className="flex flex-wrap gap-x-8 gap-y-4 text-xs font-medium text-dark-400">
          <a href="#" className="hover:text-brand-400 transition-colors">Documentation</a>
          <a href="#" className="hover:text-brand-400 transition-colors">Privacy Policy</a>
          <a href="#" className="hover:text-brand-400 transition-colors">Terms of Service</a>
          <span className="flex items-center gap-1 text-green-400">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
            System Operational
          </span>
        </div>

        {/* Copyright info */}
        <div className="text-xs text-dark-500 md:text-right">
          &copy; {currentYear} ExpenseFlow AI. All rights reserved.
        </div>
      </div>
    </footer>
  );
};

export default Footer;
