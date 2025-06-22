import { useEffect, useState } from 'react';
import './Dashboard.css';

const frameworks = ['iso', 'nist', 'cis'];

const Dashboard = () => {
  const [selectedFramework, setSelectedFramework] = useState('iso');
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`http://localhost:8000/dashboard/${selectedFramework}`);
        const result = await res.json();
        setData(result);
      } catch (err) {
        console.error('Error fetching data:', err);
      }
    };

    fetchData();
  }, [selectedFramework]);

  const getLikelihoodLabel = (row) => {
    const labels = ['Very Low', 'Low', 'Medium', 'High', 'Very High'];
    return labels[row];
  };

  const getImpactLabel = (col) => {
    const labels = ['Very Low', 'Low', 'Medium', 'High', 'Very High'];
    return labels[col];
  };

  const getRiskLevel = (score) => {
    if (score >= 15) return 'High Risk';
    else if (score >= 8) return 'Medium Risk';
    else return 'Low Risk';
  };

  return (
    <div className="main-container">
      {/* Header */}
      <section className="dashboard-header">
        <h1 className="dashboard-tagline">
          Your risk snapshot, <b>SIMPLIFIED</b>.
        </h1>
      </section>

      {/* Framework Selector */}
      <section className="framework-selector-section">
        <div className="framework-selector">
          {frameworks.map((fw) => (
            <button
              key={fw}
              className={`segment-btn ${selectedFramework === fw ? 'active' : ''}`}
              onClick={() => setSelectedFramework(fw)}
            >
              {fw.toUpperCase()}
            </button>
          ))}
        </div>
      </section>

      {/* Risk Summary */}
      {data && (
        <>
          {/* Risk Summary */}
          <section className="section-container">
            <h2 className="section-heading">Summary</h2>
            <div className="summary-cards">
              <div className="card">Total Controls: {data.total_controls}</div>
              <div className="card" id="high">High Risks: {data.high}</div>
              <div className="card" id="medium">Medium Risks: {data.medium}</div>
              <div className="card" id="low">Low Risks: {data.low}</div>
              <div className="card average-risk">Average Risk: {data.avg.toFixed(2)}</div>
            </div>
          </section>


          {/* Risk Matrix Visualization */}
          <section className="section-container">
            <h2 className="section-heading">Risk Matrix Visualization</h2>

            <div className="matrix-container">
              {/* Matrix Legend */}
              <div className="matrix-legend">
                {/* Risk Level Headings */}
                <div className="risk-levels-container">
                  <h3 className="risk-heading high">High Risk (15-25)</h3>
                  <h3 className="risk-heading medium">Medium Risk (8-14)</h3>
                  <h3 className="risk-heading low">Low Risk (1-7)</h3>
                </div>
              </div>

              <div className="matrix-with-labels">
                {/* Y-axis Label */}
                <div className="y-axis-label">
                  <span>Likelihood</span>
                </div>

                {/* Y-axis Labels */}
                <div className="y-axis-labels">
                  {[4, 3, 2, 1, 0].map((row) => (
                    <div key={row} className="y-label">
                      {getLikelihoodLabel(row)}
                    </div>
                  ))}
                </div>

                {/* Matrix Grid Container */}
                <div className="matrix-grid-container">
                  {/* Matrix Grid */}
                  <div className="matrix-grid-labeled">
                    {[...Array(5)].map((_, row) => (
                      <div key={row} className="matrix-row">
                        {[...Array(5)].map((_, col) => {
                          const actualRow = 4 - row;
                          const key = `${actualRow + 1},${col + 1}`;
                          const score = (actualRow + 1) * (col + 1);
                          const count = data.matrix?.[key] || 0;

                          let color = '';
                          if (score >= 15) color = 'high';
                          else if (score >= 8) color = 'medium';
                          else color = 'low';

                          return (
                            <div
                              key={col}
                              className={`matrix-cell ${color}`}
                              title={`${getLikelihoodLabel(actualRow)} likelihood, ${getImpactLabel(col)} impact - ${getRiskLevel(score)} (Score: ${score}, Count: ${count})`}
                              aria-label={`Risk cell: ${getLikelihoodLabel(actualRow)} likelihood, ${getImpactLabel(col)} impact, ${count} items, ${getRiskLevel(score)}`}
                            >
                              <span className="cell-count">{count}</span>
                              <span className="cell-score">({score})</span>
                            </div>
                          );
                        })}
                      </div>
                    ))}
                  </div>

                  {/* X-axis Labels */}
                  <div className="x-axis-labels">
                    {[...Array(5)].map((_, col) => (
                      <div key={col} className="x-label">
                        {getImpactLabel(col)}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* X-axis Label */}
              <div className="x-axis-label">
                <span>Impact</span>
              </div>
            </div>
          </section>
        </>
      )}
      {/* Detailed Responses Table */}
      <section className="section-container">
        <h2 className="section-heading">Detailed Responses</h2>
        <div className="table-responsive">
          <table className="responses-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Risk Category</th>
                <th>Question</th>
                <th>Likelihood</th>
                <th>Impact</th>
                <th>Risk Score</th>
              </tr>
            </thead>
            <tbody>
              {data?.responses?.map((item) => {
                const score = item.likelihood_scale * item.impact_scale;
                let riskCategory = '';
                let categoryClass = '';

                if (score >= 15) {
                  riskCategory = 'High';
                  categoryClass = 'risk-high';
                } else if (score >= 8) {
                  riskCategory = 'Medium';
                  categoryClass = 'risk-medium';
                } else {
                  riskCategory = 'Low';
                  categoryClass = 'risk-low';
                }

                return (
                  <tr key={item.id} className="table-row">
                    <td className="table-cell">{item.id}</td>
                    <td className={`table-cell risk-category ${categoryClass}`}>
                      <span className="risk-badge">{riskCategory}</span>
                    </td>
                    <td className="table-cell question-text">{item.question}</td>
                    <td className="table-cell score-cell">{item.likelihood_scale}</td>
                    <td className="table-cell score-cell">{item.impact_scale}</td>
                    <td className="table-cell score-cell risk-score">{score}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

    </div>
  );
};

export default Dashboard;
