import React, { useState, useEffect } from 'react';
import { Dashboard } from './components/Dashboard';
import type { SystemHealth } from './types';

export const App: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);

  const fetchHealth = async () => {
    setLoadingHealth(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/health');
      if (response.ok) {
        const data: SystemHealth = await response.json();
        setHealth(data);
      }
    } catch (err) {
      console.warn('Backend currently unreachable. Is FastAPI running on port 8000?', err);
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Dashboard
        health={health}
        onRefreshHealth={fetchHealth}
        loadingHealth={loadingHealth}
      />
    </div>
  );
};

export default App;
