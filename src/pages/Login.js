import React, { useState } from 'react';
import axios from 'axios';

const API = 'https://clarity-app-production.up.railway.app';

function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const res = await axios.post(`${API}/login`, formData);
      onLogin(res.data.access_token, res.data.name);
    } catch (err) {
      setError('Invalid email or password');
    }
    setLoading(false);
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Clarity</h1>
        <p style={styles.subtitle}>Personal Finance Intelligence</p>

        <input
          style={styles.input}
          type="email"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
        />
        <input
          style={styles.input}
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && handleLogin()}
        />

        {error && <p style={styles.error}>{error}</p>}

        <button
          style={styles.button}
          onClick={handleLogin}
          disabled={loading}
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
  card: {
    background: 'white',
    padding: '48px',
    borderRadius: '16px',
    width: '100%',
    maxWidth: '400px',
    boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  title: {
    fontSize: '32px',
    fontWeight: '700',
    color: '#1A1A2E',
    textAlign: 'center',
  },
  subtitle: {
    color: '#666',
    textAlign: 'center',
    marginBottom: '8px',
  },
  input: {
    padding: '14px 16px',
    borderRadius: '8px',
    border: '1px solid #E2E8F0',
    fontSize: '16px',
    outline: 'none',
    width: '100%',
  },
  button: {
    padding: '14px',
    background: '#4F46E5',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    marginTop: '8px',
  },
  error: {
    color: '#E53E3E',
    fontSize: '14px',
    textAlign: 'center',
  }
};

export default Login;