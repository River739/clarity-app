import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const API = 'https://clarity-app-production.up.railway.app';

const COLORS = ['#4F46E5', '#7C3AED', '#EC4899', '#F59E0B', '#10B981', '#3B82F6', '#EF4444', '#8B5CF6'];

function Dashboard({ token, userName, onLogout }) {
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [selectedBank, setSelectedBank] = useState('All');
  const [banks, setBanks] = useState([]);
  const [liveAlert, setLiveAlert] = useState(null);
  const wsRef = useRef(null);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchData();
    connectWebSocket();
    return () => wsRef.current?.close();
  }, []);

  const fetchData = async () => {
    try {
      const [txRes, summaryRes] = await Promise.all([
        axios.get(`${API}/transactions`, { headers }),
        axios.get(`${API}/summary`, { headers })
      ]);
      setTransactions(txRes.data.transactions);
      setSummary(summaryRes.data);
      setBanks(['All', ...txRes.data.transactions
        .map(t => t.bank)
        .filter((v, i, a) => a.indexOf(v) === i)]);
    } catch (err) {
      console.error(err);
    }
  };

  const connectWebSocket = () => {
    const ws = new WebSocket(`wss://clarity-app-production.up.railway.app/ws/${token}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event === 'new_transaction') {
        setTransactions(prev => [data.data, ...prev]);
        setLiveAlert(`New transaction: ₹${data.data.amount} at ${data.data.merchant}`);
        setTimeout(() => setLiveAlert(null), 4000);
        fetchData();
      }
    };

    ws.onclose = () => {
      setTimeout(connectWebSocket, 3000);
    };
  };

  const filteredTransactions = selectedBank === 'All'
    ? transactions
    : transactions.filter(t => t.bank === selectedBank);

  const categoryData = summary ? Object.entries(summary.spending_by_category).map(([name, value]) => ({
    name, value: Math.round(value)
  })) : [];

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.logo}>Clarity</h1>
          <p style={styles.welcome}>Welcome back, {userName}</p>
        </div>
        <button style={styles.logoutBtn} onClick={onLogout}>Logout</button>
      </div>

      {/* Live Alert */}
      {liveAlert && (
        <div style={styles.alert}>
          🔔 {liveAlert}
        </div>
      )}

      {/* Summary Cards */}
      {summary && (
        <div style={styles.cards}>
          <div style={styles.card}>
            <p style={styles.cardLabel}>Total Spent</p>
            <p style={styles.cardValue}>₹{summary.total_spent.toLocaleString()}</p>
          </div>
          <div style={styles.card}>
            <p style={styles.cardLabel}>Transactions</p>
            <p style={styles.cardValue}>{summary.total_transactions}</p>
          </div>
          <div style={styles.card}>
            <p style={styles.cardLabel}>Banks</p>
            <p style={styles.cardValue}>{summary.banks.join(', ') || 'None'}</p>
          </div>
          <div style={styles.card}>
            <p style={styles.cardLabel}>Top Category</p>
            <p style={styles.cardValue}>
              {categoryData.length > 0
                ? categoryData.sort((a, b) => b.value - a.value)[0].name
                : 'N/A'}
            </p>
          </div>
        </div>
      )}

      {/* Charts */}
      {categoryData.length > 0 && (
        <div style={styles.charts}>
          <div style={styles.chartBox}>
            <h3 style={styles.chartTitle}>Spending by Category</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={categoryData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80}>
                  {categoryData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `₹${value}`} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div style={styles.chartBox}>
            <h3 style={styles.chartTitle}>Category Breakdown</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={categoryData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip formatter={(value) => `₹${value}`} />
                <Bar dataKey="value" fill="#4F46E5" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Bank Filter */}
      <div style={styles.filterRow}>
        <h3 style={styles.sectionTitle}>Transactions</h3>
        <div style={styles.bankFilters}>
          {banks.map(bank => (
            <button
              key={bank}
              style={{
                ...styles.filterBtn,
                background: selectedBank === bank ? '#4F46E5' : 'white',
                color: selectedBank === bank ? 'white' : '#4F46E5',
              }}
              onClick={() => setSelectedBank(bank)}
            >
              {bank}
            </button>
          ))}
        </div>
      </div>

      {/* Transaction List */}
      <div style={styles.txList}>
        {filteredTransactions.length === 0 ? (
          <p style={styles.empty}>No transactions yet. Send a UPI SMS to get started.</p>
        ) : (
          filteredTransactions.map(t => (
            <div key={t.id} style={styles.txItem}>
              <div style={styles.txLeft}>
                <p style={styles.txMerchant}>{t.merchant || 'Unknown'}</p>
                <p style={styles.txMeta}>{t.bank} • {t.category} • {new Date(t.timestamp).toLocaleDateString()}</p>
              </div>
              <p style={{
                ...styles.txAmount,
                color: t.type === 'debit' ? '#EF4444' : '#10B981'
              }}>
                {t.type === 'debit' ? '-' : '+'}₹{t.amount?.toLocaleString()}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

const styles = {
  container: { maxWidth: '1100px', margin: '0 auto', padding: '24px' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' },
  logo: { fontSize: '28px', fontWeight: '700', color: '#4F46E5' },
  welcome: { color: '#666', fontSize: '14px' },
  logoutBtn: { padding: '8px 16px', background: 'transparent', border: '1px solid #E2E8F0', borderRadius: '8px', cursor: 'pointer' },
  alert: { background: '#4F46E5', color: 'white', padding: '12px 16px', borderRadius: '8px', marginBottom: '16px', fontWeight: '500' },
  cards: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' },
  card: { background: 'white', padding: '20px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' },
  cardLabel: { color: '#666', fontSize: '13px', marginBottom: '8px' },
  cardValue: { fontSize: '22px', fontWeight: '700', color: '#1A1A2E' },
  charts: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' },
  chartBox: { background: 'white', padding: '20px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' },
  chartTitle: { fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#1A1A2E' },
  filterRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' },
  sectionTitle: { fontSize: '18px', fontWeight: '600' },
  bankFilters: { display: 'flex', gap: '8px' },
  filterBtn: { padding: '6px 14px', border: '1px solid #4F46E5', borderRadius: '20px', cursor: 'pointer', fontSize: '13px', fontWeight: '500' },
  txList: { background: 'white', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', overflow: 'hidden' },
  txItem: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid #F1F5F9' },
  txLeft: {},
  txMerchant: { fontWeight: '600', marginBottom: '4px' },
  txMeta: { fontSize: '12px', color: '#999' },
  txAmount: { fontWeight: '700', fontSize: '18px' },
  empty: { padding: '40px', textAlign: 'center', color: '#999' },
};

export default Dashboard;