import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, ArrowUpRight, ArrowDownLeft, Sliders, Menu } from 'lucide-react';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import Footer from './Footer';
import CommandPalette from '../Common/CommandPalette';

const mobileNavItems = [
  { name: 'Home', to: '/dashboard', icon: LayoutDashboard },
  { name: 'Expenses', to: '/dashboard/expenses', icon: ArrowUpRight },
  { name: 'Income', to: '/dashboard/income', icon: ArrowDownLeft },
  { name: 'Budgets', to: '/dashboard/budgets', icon: Sliders },
  { name: 'More', to: null, icon: Menu },
];

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [cmdPaletteOpen, setCmdPaletteOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  // Global Cmd+K / Ctrl+K keyboard shortcut listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCmdPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="min-h-screen flex bg-dark-950 text-dark-100 transition-colors duration-300 font-sans antialiased relative">
      {/* Glow Backdrop Spotlights */}
      <div className="absolute w-[450px] h-[450px] rounded-full bg-brand-500/[0.02] blur-[120px] top-0 left-0 pointer-events-none" />
      <div className="absolute w-[450px] h-[450px] rounded-full bg-savings/[0.015] blur-[120px] bottom-0 right-0 pointer-events-none" />

      {/* Desktop Sidebar */}
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      {/* Mobile Sidebar overlay with enhanced blur */}
      {sidebarOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/75 backdrop-blur-md z-40 lg:hidden confirm-backdrop-enter"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 z-50 lg:hidden sidebar-enter">
            <Sidebar mobile onClose={() => setSidebarOpen(false)} />
          </div>
        </>
      )}

      {/* Main workspace container */}
      <div className="flex-1 lg:pl-64 flex flex-col min-h-screen pb-20 lg:pb-0">
        {/* Sticky Header */}
        <Navbar onMenuClick={() => setSidebarOpen(true)} />

        {/* Dynamic workspace context */}
        <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-7xl w-full mx-auto overflow-y-auto relative z-10 edl-animate-fade">
          <Outlet />
        </main>

        {/* Desktop Footer */}
        <div className="hidden lg:block mt-auto">
          <Footer />
        </div>
      </div>

      {/* Mobile Bottom Dock (Floating design layout) */}
      <nav className="fixed bottom-4 left-4 right-4 z-50 lg:hidden rounded-2xl bg-dark-900/90 backdrop-blur-xl border border-dark-800/80 shadow-edl-depth px-2 py-1.5">
        <div className="flex items-center justify-around">
          {mobileNavItems.map((item) => {
            const Icon = item.icon;
            if (item.to === null) {
              return (
                <button
                  key={item.name}
                  onClick={() => setSidebarOpen(true)}
                  className="flex flex-col items-center gap-1 px-3 py-1.5 text-dark-400 hover:text-white transition-colors"
                >
                  <Icon className="w-4.5 h-4.5" />
                  <span className="text-[9px] font-bold tracking-wide">{item.name}</span>
                </button>
              );
            }
            return (
              <NavLink
                key={item.name}
                to={item.to}
                end={item.to === '/dashboard'}
                className={({ isActive }) =>
                  `flex flex-col items-center gap-1 px-3 py-1.5 rounded-xl transition-all ${
                    isActive 
                      ? 'text-brand-400 bg-brand-500/[0.06] border border-brand-500/10' 
                      : 'text-dark-400 hover:text-dark-200 border border-transparent'
                  }`
                }
              >
                <Icon className="w-4.5 h-4.5" />
                <span className="text-[9px] font-bold tracking-wide">{item.name}</span>
              </NavLink>
            );
          })}
        </div>
      </nav>

      {/* Global Command Palette Cmd+K / Ctrl+K Modal */}
      <CommandPalette isOpen={cmdPaletteOpen} onClose={() => setCmdPaletteOpen(false)} />
    </div>
  );
};

export default Layout;
