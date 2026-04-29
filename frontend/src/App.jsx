import { useState } from 'react';
import UploadPage from './pages/UploadPage';
import ReviewPage from './pages/ReviewPage';
import DashboardPage from './pages/DashboardPage';
import AdminPage from './pages/AdminPage';

export default function App() {
  const [page, setPage] = useState('upload'); // 'upload' | 'review' | 'dashboard' | 'admin'
  const [result, setResult] = useState(null);

  const handleResult = (data) => {
    setResult(data);
    setPage('review');
  };

  const handleApproved = () => {
    setResult(null);
    setPage('dashboard');
  };

  if (page === 'review' && result) {
    return (
      <ReviewPage
        result={result}
        onBack={() => { setResult(null); setPage('upload'); }}
        onApproved={handleApproved}
      />
    );
  }

  if (page === 'dashboard') {
    return <DashboardPage onUpload={() => setPage('upload')} onAdmin={() => setPage('admin')} />;
  }

  if (page === 'admin') {
    return <AdminPage onBack={() => setPage('upload')} />;
  }

  return <UploadPage onResult={handleResult} onDashboard={() => setPage('dashboard')} onAdmin={() => setPage('admin')} />;
}
