import React, { useState, useRef } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [cvFile, setCvFile] = useState(null);
  const [cvText, setCvText] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [targetCompany, setTargetCompany] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [companyIntelligence, setCompanyIntelligence] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setCvFile(file);
    setLoading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/api/upload-cv`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload CV');
      }

      const result = await response.json();
      setCvText(result.cv_text);
      setUploadProgress(100);
      setActiveTab('analyze');
    } catch (error) {
      console.error('Error uploading CV:', error);
      alert('Error uploading CV: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const analyzeCV = async () => {
    if (!cvText.trim()) {
      alert('Please upload a CV first');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze-cv`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          cv_text: cvText,
          target_role: targetRole,
          target_company: targetCompany,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to analyze CV');
      }

      const result = await response.json();
      setAnalysis(result);
      setActiveTab('results');
    } catch (error) {
      console.error('Error analyzing CV:', error);
      alert('Error analyzing CV: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const researchCompany = async () => {
    if (!targetCompany.trim()) {
      alert('Please enter a company name');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/company-research`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company_name: targetCompany,
          role_type: targetRole,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to research company');
      }

      const result = await response.json();
      setCompanyIntelligence(result);
    } catch (error) {
      console.error('Error researching company:', error);
      alert('Error researching company: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const renderCVAnalysis = () => {
    if (!analysis) return null;

    const { cv_improvements, skills_analysis, company_insights } = analysis;

    return (
      <div className="analysis-container">
        <div className="analysis-header">
          <h2>🤖 Multi-AI Analysis Results</h2>
          <div className="confidence-score">
            <span>Confidence Score: </span>
            <div className="score-bar">
              <div 
                className="score-fill" 
                style={{ width: `${analysis.confidence_score}%` }}
              ></div>
            </div>
            <span>{analysis.confidence_score}%</span>
          </div>
        </div>

        {/* CV Improvements Section */}
        <div className="analysis-section">
          <h3>📝 CV Optimization (GPT-4 Creative Analysis)</h3>
          <div className="analysis-grid">
            <div className="analysis-card">
              <h4>Overall Score</h4>
              <div className="score-display">
                {cv_improvements?.overall_score || 'N/A'}/100
              </div>
            </div>
            <div className="analysis-card">
              <h4>✅ Key Strengths</h4>
              <ul>
                {cv_improvements?.strengths?.map((strength, index) => (
                  <li key={index}>{strength}</li>
                )) || <li>Analysis in progress...</li>}
              </ul>
            </div>
            <div className="analysis-card">
              <h4>🚀 Critical Improvements</h4>
              <ul>
                {cv_improvements?.critical_improvements?.map((improvement, index) => (
                  <li key={index}>{improvement}</li>
                )) || <li>Analysis in progress...</li>}
              </ul>
            </div>
            <div className="analysis-card">
              <h4>🎯 ATS Optimization</h4>
              <div className="ats-keywords">
                {cv_improvements?.ats_optimization || 'Analyzing keywords...'}
              </div>
            </div>
          </div>
        </div>

        {/* Skills Analysis Section */}
        <div className="analysis-section">
          <h3>🔧 Skills Gap Analysis (GPT-4 Technical Analysis)</h3>
          <div className="skills-grid">
            <div className="skills-card">
              <h4>Current Skills</h4>
              <div className="skills-list">
                {skills_analysis?.current_skills && typeof skills_analysis.current_skills === 'object' 
                  ? Object.entries(skills_analysis.current_skills).map(([category, skills]) => (
                      <div key={category} className="skill-category">
                        <strong>{category}:</strong>
                        <span>{Array.isArray(skills) ? skills.join(', ') : skills}</span>
                      </div>
                    ))
                  : <p>Analyzing current skills...</p>
                }
              </div>
            </div>
            <div className="skills-card priority">
              <h4>🎯 Learning Priorities</h4>
              <ul>
                {skills_analysis?.learning_priorities?.map((priority, index) => (
                  <li key={index}>{priority}</li>
                )) || <li>Analyzing priorities...</li>}
              </ul>
            </div>
            <div className="skills-card">
              <h4>📈 Emerging Skills 2025</h4>
              <ul>
                {skills_analysis?.emerging_skills?.map((skill, index) => (
                  <li key={index}>{skill}</li>
                )) || <li>Researching trends...</li>}
              </ul>
            </div>
          </div>
        </div>

        {/* Company Intelligence */}
        {company_insights && (
          <div className="analysis-section">
            <h3>🏢 Company Intelligence</h3>
            <div className="company-grid">
              <div className="company-card">
                <h4>Work Culture</h4>
                <p>{company_insights.culture_analysis?.work_culture || 'Analyzing...'}</p>
              </div>
              <div className="company-card">
                <h4>Interview Style</h4>
                <p>{company_insights.culture_analysis?.interview_style || 'Researching...'}</p>
              </div>
              <div className="company-card">
                <h4>Application Tips</h4>
                <p>{company_insights.culture_analysis?.application_tips || 'Generating tips...'}</p>
              </div>
            </div>
          </div>
        )}

        {/* AI Ensemble Insights */}
        <div className="analysis-section ensemble">
          <h3>🧠 AI Ensemble Recommendations</h3>
          <div className="recommendations-grid">
            <div className="recommendation-card">
              <h4>Priority Actions</h4>
              <ul>
                {analysis.recommendations?.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderUploadTab = () => (
    <div className="upload-section">
      <div className="upload-hero">
        <h1>🚀 AI-Powered Job Preparation</h1>
        <p>Multi-AI orchestration meets real-time company intelligence</p>
      </div>
      
      <div className="upload-container">
        <div className="upload-area" onClick={() => fileInputRef.current?.click()}>
          <div className="upload-icon">📄</div>
          <h3>Upload Your CV</h3>
          <p>PDF or text files supported</p>
          <button className="upload-btn">Choose File</button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.doc,.docx"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
        </div>
        
        {cvFile && (
          <div className="file-info">
            <span>📋 {cvFile.name}</span>
            {uploadProgress < 100 && (
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );

  const renderAnalyzeTab = () => (
    <div className="analyze-section">
      <h2>🎯 Configure Your Analysis</h2>
      
      <div className="input-grid">
        <div className="input-group">
          <label>Target Role</label>
          <input
            type="text"
            placeholder="e.g., Senior Software Engineer"
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
          />
        </div>
        
        <div className="input-group">
          <label>Target Company</label>
          <input
            type="text"
            placeholder="e.g., Google, Microsoft, Apple"
            value={targetCompany}
            onChange={(e) => setTargetCompany(e.target.value)}
          />
        </div>
      </div>
      
      <div className="action-buttons">
        <button 
          className="primary-btn"
          onClick={analyzeCV}
          disabled={loading || !cvText}
        >
          {loading ? '🔄 Analyzing...' : '🤖 Run Multi-AI Analysis'}
        </button>
        
        <button 
          className="secondary-btn"
          onClick={researchCompany}
          disabled={loading || !targetCompany.trim()}
        >
          {loading ? '🔍 Researching...' : '🏢 Research Company'}
        </button>
      </div>
      
      {cvText && (
        <div className="cv-preview">
          <h3>CV Preview</h3>
          <div className="cv-text">
            {cvText.substring(0, 500)}...
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="App">
      <nav className="navbar">
        <div className="nav-brand">
          <span className="logo">🤖</span>
          <span className="brand-text">JobPrep AI</span>
          <span className="beta-badge">Multi-AI</span>
        </div>
        
        <div className="nav-tabs">
          <button 
            className={`nav-tab ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            📤 Upload
          </button>
          <button 
            className={`nav-tab ${activeTab === 'analyze' ? 'active' : ''}`}
            onClick={() => setActiveTab('analyze')}
            disabled={!cvText}
          >
            🔬 Analyze
          </button>
          <button 
            className={`nav-tab ${activeTab === 'results' ? 'active' : ''}`}
            onClick={() => setActiveTab('results')}
            disabled={!analysis}
          >
            📊 Results
          </button>
        </div>
      </nav>

      <main className="main-content">
        {loading && (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
            <p>AI engines processing...</p>
          </div>
        )}
        
        {activeTab === 'upload' && renderUploadTab()}
        {activeTab === 'analyze' && renderAnalyzeTab()}
        {activeTab === 'results' && renderCVAnalysis()}
      </main>

      <footer className="footer">
        <p>Powered by Multi-AI Orchestration • GPT-4 + Real-Time Intelligence</p>
      </footer>
    </div>
  );
}

export default App;