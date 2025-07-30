import React from 'react';
import { AlertCircle, WifiOff, RefreshCw } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      isOnline: navigator.onLine
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidMount() {
    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);
  }

  componentWillUnmount() {
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
  }

  handleOnline = () => {
    this.setState({ isOnline: true });
    // Auto-retry after coming online
    setTimeout(() => {
      this.handleReset();
    }, 1000);
  };

  handleOffline = () => {
    this.setState({ isOnline: false });
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError || !this.state.isOnline) {
      return (
        <div className="error-container">
          <div className="error-content">
            {!this.state.isOnline ? (
              <>
                <WifiOff size={48} className="error-icon" />
                <h2>You're Offline</h2>
                <p>Please check your internet connection</p>
              </>
            ) : (
              <>
                <AlertCircle size={48} className="error-icon" />
                <h2>Something went wrong</h2>
                <p>We're having trouble connecting to our servers</p>
              </>
            )}
            
            <button 
              onClick={this.handleReset}
              className="retry-button"
              disabled={!this.state.isOnline}
            >
              <RefreshCw size={20} />
              Try Again
            </button>
            
            {!this.state.isOnline && (
              <p className="offline-note">
                We'll automatically reconnect when you're back online
              </p>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary; 