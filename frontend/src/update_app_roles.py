import re

app_file = r'c:\Users\HP\OneDrive\jandhwani local\frontend\src\App.jsx'

with open(app_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Update handleLoginSuccess
old_login = """  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    if (user.language) {
      setSelectedLanguage(user.language);
    }
    if (user.state) {
      setCustomLocation(prev => ({
        ...prev,
        state: user.state,
        district: user.district || 'Pune'
      }));
    }
    setActiveTab('grievance');
  };"""

new_login = """  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    if (user.language) {
      setSelectedLanguage(user.language);
    }
    if (user.state) {
      setCustomLocation(prev => ({
        ...prev,
        state: user.state,
        district: user.district || 'Pune'
      }));
    }
    setActiveTab(user.role === 'government' ? '3d_twin' : 'grievance');
  };"""

content = content.replace(old_login, new_login)


# Update the nav buttons area
old_nav = """        <div className="nav-buttons">
          <button 
            type="button"
            className="nav-btn"
            onClick={() => setActiveTab('login')}
          >
            {currentUser ? (t.fullName || 'Citizen Profile') : t.portalTitle}
          </button>
          <button 
            type="button"
            className={`nav-btn ${activeTab === 'grievance' ? 'active' : ''}`}
            onClick={() => setActiveTab('grievance')}
          >
            {t.fileGrievanceTitle}
          </button>
          
          {currentUser && (
            <button 
              type="button"
              className={`nav-btn ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              My Complaints (History)
            </button>
          )}

        </div>"""

new_nav = """        <div className="nav-buttons">
          <button 
            type="button"
            className="nav-btn"
            onClick={() => setActiveTab('login')}
          >
            {currentUser ? (currentUser.role === 'government' ? 'Govt Profile' : (t.fullName || 'Citizen Profile')) : t.portalTitle}
          </button>
          
          {(!currentUser || currentUser.role !== 'government') && (
            <button 
              type="button"
              className={`nav-btn ${activeTab === 'grievance' ? 'active' : ''}`}
              onClick={() => setActiveTab('grievance')}
            >
              {t.fileGrievanceTitle}
            </button>
          )}
          
          {(currentUser && currentUser.role !== 'government') && (
            <button 
              type="button"
              className={`nav-btn ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              My Complaints (History)
            </button>
          )}

          {(currentUser && currentUser.role === 'government') && (
            <>
              <button 
                type="button"
                className={`nav-btn ${activeTab === '3d_twin' ? 'active' : ''}`}
                onClick={() => setActiveTab('3d_twin')}
              >
                3D Digital Twin Map
              </button>
              <button 
                type="button"
                className={`nav-btn ${activeTab === 'resolved_archive' ? 'active' : ''}`}
                onClick={() => setActiveTab('resolved_archive')}
              >
                Resolved Archive
              </button>
            </>
          )}
        </div>"""

content = content.replace(old_nav, new_nav)

with open(app_file, 'w', encoding='utf-8') as f:
    f.write(content)
print("App.jsx roles updated successfully!")
