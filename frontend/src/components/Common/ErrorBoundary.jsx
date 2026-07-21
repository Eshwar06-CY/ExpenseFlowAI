import React, { Component } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import Button from './Button';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an unhandled exception:', error, errorInfo);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-dark-950 p-6 relative select-none">
          <div className="absolute top-1/4 left-1/4 w-[450px] h-[450px] bg-red-500/5 rounded-full blur-3xl"></div>
          
          <div className="text-center z-10 space-y-6 max-w-md w-full bg-dark-900 border border-dark-850 p-8 rounded-3xl shadow-2xl">
            <div className="inline-flex p-4 bg-red-600/10 border border-red-500/20 text-red-400 rounded-2xl mb-2 animate-pulse">
              <AlertTriangle className="w-12 h-12" />
            </div>
            
            <div className="space-y-2">
              <h1 className="text-2xl font-extrabold text-dark-50 tracking-tight">Application Error</h1>
              <p className="text-dark-400 text-sm leading-relaxed">
                An unexpected interface or data error has occurred. Your workspace data remains safe in the database ledger.
              </p>
            </div>

            {this.state.error && (
              <div className="text-left text-xs bg-dark-950 border border-dark-800 p-4 rounded-xl font-mono text-red-400/90 overflow-x-auto max-h-48 whitespace-pre-wrap">
                {this.state.error.toString()}
              </div>
            )}
            
            <Button
              variant="primary"
              onClick={this.handleReload}
              className="w-full flex items-center justify-center gap-2 font-semibold"
            >
              <RefreshCw className="w-4 h-4" /> Reload Workspace
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
