import React, { useState } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

function App() {
  const [token, setToken] = useState(localStorage.getItem('clarity_token'));
  const [userName, setUserName] = useState(localStorage.getItem('clarity_name'));

  const handleLogin = (newToken, name) => {
    localStorage.setItem('clarity_token', newToken);
    localStorage.setItem('clarity_name', name);
    setToken(newToken);
    setUserName(name);
  };

  const handleLogout = () => {
    localStorage.removeItem('clarity_token');
    localStorage.removeItem('clarity_name');
    setToken(null);
    setUserName(null);
  };

  return (
    <div>
      {token ? (
        <Dashboard token={token} userName={userName} onLogout={handleLogout} />
      ) : (
        <Login onLogin={handleLogin} />
      )}
    </div>
  );
}

export default App;