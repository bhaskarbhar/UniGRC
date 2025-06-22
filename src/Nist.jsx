import { useState, useEffect } from 'react';
import './Nist.css';
import nistData from './assets/NIST.json';

const Nist = () => {
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState({});
  const [selectedLikelihood, setSelectedLikelihood] = useState(null);
  const [selectedImpact, setSelectedImpact] = useState(null);
  const [isSaved, setIsSaved] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');
  const [showAlert, setShowAlert] = useState(false);

  // Show alert for 3 seconds
  const showAlertMessage = (message) => {
    setAlertMessage(message);
    setShowAlert(true);
    setTimeout(() => setShowAlert(false), 3000);
  };

  useEffect(() => {
    setQuestions(nistData.questions);
  }, []);

  useEffect(() => {
    const currentId = questions[currentIndex]?.id;
    const saved = responses[currentId] || {};
    setSelectedLikelihood(saved.likelihood || null);
    setSelectedImpact(saved.impact || null);
    setIsSaved(!!(saved.likelihood && saved.impact));
  }, [currentIndex, questions, responses]);

  const handleSave = async () => {
    const currentId = questions[currentIndex].id;
    const currentQuestionText = questions[currentIndex].question;

    // Update local state
    setResponses({
      ...responses,
      [currentId]: {
        question: currentQuestionText,
        likelihood: selectedLikelihood,
        impact: selectedImpact,
      },
    });
    setIsSaved(true);

    // Send data to backend API
    try {
      const response = await fetch('http://127.0.0.1:8000/save-response/iso', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: String(currentId),
          question: currentQuestionText,
          likelihood_scale: selectedLikelihood,
          impact_scale: selectedImpact,
        }),
      });

      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'Failed to save');

      console.log('Response saved:', result);
      showAlertMessage('Question saved successfully!');
    } catch (err) {
      console.error('Save error:', err.message);
    }
  };

  const handlePrev = () => {
    if (isSaved && currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleNext = () => {
    if (isSaved && currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  if (questions.length === 0) return <div>Loading...</div>;

  const currentQuestion = questions[currentIndex];

  return (
    <div className="nist-container">
      {showAlert && (
        <div className="alert-box">
          {alertMessage}
        </div>
      )}
      <div className="left-section">
        <h1>Think Twice<br />Choose One…</h1>

        <div className="question-row">
          <button
            className="navigation-arrow"
            onClick={handlePrev}
            disabled={!isSaved || currentIndex === 0}
          >
            &lt;
          </button>

          <p className="question">{currentQuestion.question}</p>

          <button
            className="navigation-arrow"
            onClick={handleNext}
            disabled={!isSaved || currentIndex === questions.length - 1}
          >
            &gt;
          </button>
        </div>

        <div className="scale">
          <div className="scale-section">
            <div className="label">Likelihood</div>
            <div className="options">
              {currentQuestion.likelihood_scale.map(num => (
                <label key={`likelihood-${num}`}>
                  <input
                    type="radio"
                    name="likelihood"
                    checked={selectedLikelihood === num}
                    onChange={() => {
                      setSelectedLikelihood(num);
                      setIsSaved(false);
                    }}
                  />
                  <span>{num}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="scale-section">
            <div className="label">Impact</div>
            <div className="options">
              {currentQuestion.impact_scale.map(num => (
                <label key={`impact-${num}`}>
                  <input
                    type="radio"
                    name="impact"
                    checked={selectedImpact === num}
                    onChange={() => {
                      setSelectedImpact(num);
                      setIsSaved(false);
                    }}
                  />
                  <span>{num}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="button-row">
          <button
            className="save-btn"
            onClick={handleSave}
            disabled={!selectedLikelihood || !selectedImpact}
          >
            Save
          </button>

          <button
            className="clear-btn"
            onClick={() => {
              setResponses({});
              setSelectedLikelihood(null);
              setSelectedImpact(null);
              setIsSaved(false);
              setCurrentIndex(0);
              showAlertMessage('All responses cleared!');
            }}
          >
            Clear All
          </button>

          <button
            className="choose-btn"
            onClick={() => {
              setResponses({});
              setSelectedLikelihood(null);
              setSelectedImpact(null);
              setIsSaved(false);
              setCurrentIndex(0);
              window.location.href = '/framework';
            }}
          >
            Choose Again
          </button>
        </div>
      </div>

      <div className="right-section">
        <h2>NIST CSF :</h2>
        <p>20 questions mapped to<br />Identify, Protect, Detect, Respond, Recover.</p>
      </div>
    </div>
  );
};

export default Nist;
