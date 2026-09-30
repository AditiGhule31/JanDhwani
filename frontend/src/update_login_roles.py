import re

login_file = r'c:\Users\HP\OneDrive\jandhwani local\frontend\src\components\login\Login.jsx'

with open(login_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Update the tabs structure
old_tabs = """      <div className="auth-tabs">
        <button 
          type="button"
          className={`auth-tab ${authMode === 'register' ? 'active' : ''}`}
          onClick={() => { setAuthMode('register'); setAlertInfo(null); }}
        >
          {t.signUpTab}
        </button>
        <button 
          type="button"
          className={`auth-tab ${authMode === 'login' ? 'active' : ''}`}
          onClick={() => { setAuthMode('login'); setAlertInfo(null); }}
        >
          {t.logInTab}
        </button>
      </div>"""

new_tabs = """      <div className="auth-tabs" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '5px' }}>
        <button 
          type="button"
          className={`auth-tab ${authMode === 'register' ? 'active' : ''}`}
          onClick={() => { setAuthMode('register'); setAlertInfo(null); }}
          style={{ fontSize: '0.85rem', padding: '12px 5px' }}
        >
          {t.signUpTab}
        </button>
        <button 
          type="button"
          className={`auth-tab ${authMode === 'login' ? 'active' : ''}`}
          onClick={() => { setAuthMode('login'); setAlertInfo(null); }}
          style={{ fontSize: '0.85rem', padding: '12px 5px' }}
        >
          Citizen Login
        </button>
        <button 
          type="button"
          className={`auth-tab ${authMode === 'gov_login' ? 'active' : ''}`}
          onClick={() => { setAuthMode('gov_login'); setAlertInfo(null); }}
          style={{ fontSize: '0.85rem', padding: '12px 5px', borderBottom: authMode === 'gov_login' ? '3px solid #b71c1c' : 'none', color: authMode === 'gov_login' ? '#b71c1c' : '#666' }}
        >
          Govt Login
        </button>
      </div>"""

content = content.replace(old_tabs, new_tabs)

# Add gov login handle submit function right after handleLoginSubmit
old_login_submit = """  const handleLoginSubmit = (e) => {
    e.preventDefault();
    if (!loginIdentifier || !loginPassword) {
      setAlertInfo({ type: 'error', text: `${t.requiredErr} *` });
      return;
    }"""
new_gov_submit = """  const handleGovSubmit = (e) => {
    e.preventDefault();
    if (loginIdentifier === 'admin' && loginPassword === 'admin123') {
      setAlertInfo({ type: 'success', text: 'Official Verified! Accessing 3D Dashboard...' });
      setTimeout(() => {
        onLoginSuccess({
          fullName: 'S. K. Sharma (Collector)',
          role: 'government',
          district: 'Pune',
          state: 'Maharashtra',
          language: currentLang,
          isLoggedIn: true
        });
      }, 500);
    } else {
      setAlertInfo({ type: 'error', text: 'Invalid Government Credentials. Use admin / admin123' });
    }
  };

"""
content = content.replace(old_login_submit, new_gov_submit + old_login_submit)

# Replace the conditional render for the login form
old_render = """      {authMode === 'register' ? ("""
new_render = """      {authMode === 'gov_login' ? (
        <form onSubmit={handleGovSubmit} className="auth-form" noValidate>
          <div className="login-instructions" style={{ background: '#ffebee', color: '#b71c1c', border: '1px solid #ffcdd2' }}>
            <p style={{ margin: 0, fontWeight: 'bold' }}>National Digital Twin Access</p>
            <p style={{ margin: '5px 0 0 0', fontSize: '0.85rem' }}>Restricted to Authorized Government Officials Only.</p>
          </div>

          <div className="form-group">
            <label>Official Govt ID <span className="req">*</span></label>
            <input 
              type="text" 
              value={loginIdentifier} 
              onChange={e => setLoginIdentifier(e.target.value)} 
              placeholder="e.g. admin" 
            />
          </div>
          <div className="form-group">
            <label>Secure Password <span className="req">*</span></label>
            <input 
              type="password" 
              value={loginPassword} 
              onChange={e => setLoginPassword(e.target.value)} 
              placeholder="e.g. admin123" 
            />
          </div>

          <button type="submit" className="auth-submit-btn" style={{ background: '#b71c1c' }}>
            Access 3D Digital Twin Map
          </button>
        </form>
      ) : authMode === 'register' ? ("""
content = content.replace(old_render, new_render)

with open(login_file, 'w', encoding='utf-8') as f:
    f.write(content)
print("Login updated!")
