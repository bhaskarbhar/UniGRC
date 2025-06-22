import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App.jsx';
import Framework from './Framework.jsx';
import Iso from './Iso.jsx';
import Nist from './Nist.jsx';
import Cis from './Cis.jsx';
import Dashboard from './Dashboard.jsx';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/framework" element={<Framework />} />
        <Route path="/iso27001" element={<Iso />} />
        <Route path="/nist_csf" element={<Nist />} />
        <Route path="/cis_controls" element={<Cis />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
