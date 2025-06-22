import './Framework.css';
import { useNavigate } from 'react-router-dom';
function Framework(){
  const navigate = useNavigate();
  return (
    <div className="framework-container">
      <h1>One Goal.<br />Three Frameworks.<br />Your Choice...</h1>
      <div className="frameworks">
        <div className="framework-card" onClick={() => navigate('/iso27001')}>
          <h2>ISO 27001</h2>
          <p>
            Ideal for organizations seeking international recognition and structured security compliance.
          </p>
        </div>
        <div className="framework-card" onClick={() => navigate('/nist_csf')}>
          <h2>NIST CSF</h2>
          <p>
            Best suited for aligning cybersecurity with business objectives, especially in U.S.-based industries.
          </p>
        </div>
        <div className="framework-card" onClick={() => navigate('/cis_controls')}>
          <h2>CIS Controls</h2>
          <p>
            Great for quick, actionable security improvements with a prioritized approach.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Framework;