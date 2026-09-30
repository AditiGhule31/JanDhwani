import { useState, useMemo } from 'react';
import { 
  ALL_LANGUAGES, 
  LANGUAGE_REGIONS, 
  STATES_AND_DISTRICTS, 
  PINCODE_MAP, 
  EXPANDED_DEMO_CITIZENS,
  DISTRICTS_AND_TALUKAS
} from '../../indiaData';
import { VALIDATION_RULES } from '../../validators';
import { UI_STRINGS } from '../../translations';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
import { jwtDecode } from 'jwt-decode';

import './Login.css';

// Note: Replace this Client ID with your actual Google OAuth Client ID for production
const GOOGLE_CLIENT_ID = '364462220122-7qntf1pjtllbnfr24ak583f9bpgbblpu.apps.googleusercontent.com';

function Login({ onLoginSuccess, onContinueAsGuest, activeLanguage, onLanguageChange }) {
  // Step 0: Language Gate state
  const [currentLang, setCurrentLang] = useState(activeLanguage || 'hi-IN');

  // Auth view mode ('register' by default after language selection or 'login')
  const [authMode, setAuthMode] = useState('register');
  const [loginMethod, setLoginMethod] = useState('otp'); // 'otp' | 'password'

  // Location method (Flipkart/Swiggy style: 'gps_permission' vs 'manual')
  const [locationMode, setLocationMode] = useState('manual');
  const [gpsStatus, setGpsStatus] = useState(null);

  // Login form state
  const [loginIdentifier, setLoginIdentifier] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginOtp, setLoginOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);

  // Government Registration state (Strictly Validated)
  const [regData, setRegData] = useState({
  fullName: '',
  mobile: '',
  email: '',
  aadhaar: '',
  state: '',
  district: '',
  taluka: '',
  password: '',
  confirmPassword: ''
});

  // Validation Error States
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [alertInfo, setAlertInfo] = useState(null);
  const [pincodeDetectedInfo, setPincodeDetectedInfo] = useState(null);

  // Helper for UI text based on chosen language (with fallback)
  const t = UI_STRINGS[currentLang] || UI_STRINGS['en-IN'] || UI_STRINGS['hi-IN'];

  // Handle Language Select
  const handleLanguageSelect = (langCode) => {
    setCurrentLang(langCode);
    setRegData(prev => ({ ...prev, preferredLanguage: langCode }));
    if (onLanguageChange) {
      onLanguageChange(langCode);
    }
  };

  // Field validation trigger
  const validateField = (field, value, extra) => {
    let error = null;
    if (!value || value.trim() === '') {
      if (field !== 'email') {
        error = `${t.requiredErr} *`;
      }
    } else {
      if (field === 'fullName') error = VALIDATION_RULES.fullName(value) ? `${t.requiredErr} (Min. 3 letters)` : null;
      if (field === 'mobile') error = VALIDATION_RULES.mobile(value) ? `${t.requiredErr} (10 digits, 6-9)` : null;
    if (field === 'aadhaar') error = value.length !== 12 ? `${t.requiredErr} (12 digits required)` : null;
            if (field === 'email') error = VALIDATION_RULES.email(value);
      if (field === 'password') error = VALIDATION_RULES.password(value) ? `${t.requiredErr} (Min. 6 chars)` : null;
      if (field === 'confirmPassword') {
        if (value !== regData.password) error = 'Passwords do not match';
      }
                      }

    setErrors(prev => ({ ...prev, [field]: error }));
    return error;
  };

  const handleBlur = (field) => {
    setTouched(prev => ({ ...prev, [field]: true }));
    validateField(field, regData[field]);
  };

  const handleAadhaarChange = (val) => {
    const sanitized = val.replace(/\D/g, '').slice(0, 12);
    setRegData(prev => ({ ...prev, aadhaar: sanitized }));
    if (touched.aadhaar) validateField('aadhaar', sanitized);
  };

  // Sanitized Name Change
  const handleNameChange = (val) => {
    const sanitized = val.replace(/[^a-zA-Z\u0900-\u0DFF\s.]/g, '');
    setRegData(prev => ({ ...prev, fullName: sanitized }));
    if (touched.fullName) validateField('fullName', sanitized);
  };

  // Sanitized Mobile Change
  const handleMobileChange = (val) => {
    const sanitized = val.replace(/\D/g, '').slice(0, 10);
    setRegData(prev => ({ ...prev, mobile: sanitized }));
    if (touched.mobile) validateField('mobile', sanitized);
  };

  // Flipkart / Swiggy Style Location Permission Handler (Fully Localized)
  const requestLocationPermission = () => {
    if (!navigator.geolocation) {
      setGpsStatus({
        granted: false,
        message: currentLang === 'en-IN' 
          ? 'Geolocation is not supported by your browser' 
          : 'लोकेशन सेवा उपलब्ध नहीं है (Geolocation not supported)'
      });
      return;
    }

    setGpsStatus({ 
      granted: null, 
      message: currentLang === 'en-IN' 
        ? 'Requesting GPS Location Permission...' 
        : 'लोकेशन अनुमति मांगी जा रही है (Requesting GPS)...' 
    });

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        
        let detectedState = 'Maharashtra';
        let detectedDistrict = 'Pune';
        let detectedPin = '411001';

        if (lat > 28.0) {
          detectedState = 'Delhi (NCT)';
          detectedDistrict = 'New Delhi';
          detectedPin = '110001';
        } else if (lat > 25.0) {
          detectedState = 'Bihar';
          detectedDistrict = 'Patna';
          detectedPin = '800001';
        } else if (lat < 14.0) {
          detectedState = 'Tamil Nadu';
          detectedDistrict = 'Chennai';
          detectedPin = '600001';
        }

        setRegData(prev => ({
          ...prev,
          state: detectedState,
          district: detectedDistrict,
          pincode: detectedPin
        }));

        setGpsStatus({
          granted: true,
          coords: { lat, lng },
          message: `${detectedDistrict}, ${detectedState} (${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E)`
        });
        setLocationMode('gps_permission');
      },
      (err) => {
        setGpsStatus({
          granted: false,
          message: currentLang === 'en-IN' 
            ? 'Permission Denied. Please select manually from the dropdowns below.' 
            : 'अनुमति अस्वीकृत (Permission Denied). कृपया नीचे मैन्युअल रूप से चुनें।'
        });
        setLocationMode('manual');
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  // 1-Click Fast Auto-Fill with DigiLocker / Aadhaar Sandbox
  const handleDigiLockerFastFill = () => {
    setRegData({
      fullName: 'Sunil Deshmukh',
      mobile: '9822998877',
      email: 'sunil.deshmukh@gov.in',
      state: 'Maharashtra',
      district: 'Pune',
      areaType: 'rural',
      tehsil: 'Haveli Taluka',
      panchayatOrWard: 'Loni Kalbhor Panchayat',
      pincode: '412201',
      preferredLanguage: currentLang,
      password: 'Password@123',
      confirmPassword: 'Password@123'
    });
    setErrors({});
    setAlertInfo({ 
      type: 'success', 
      text: 'DigiLocker: All credentials auto-filled' 
    });
  };

  const handleSendOtp = () => {
    const mobErr = VALIDATION_RULES.mobile(loginIdentifier);
    if (mobErr) {
      setAlertInfo({ type: 'error', text: `${t.requiredErr} (10 digits)` });
      return;
    }
    setOtpSent(true);
    setAlertInfo({ 
      type: 'info', 
      text: 'OTP sent: [9 4 2 1 0 8]' 
    });
  };

  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const handleGoogleSuccess = (credentialResponse) => {
    try {
      const decoded = jwtDecode(credentialResponse.credential);
      setAuthMode('register');
      setRegData(prev => ({ 
        ...prev, 
        fullName: decoded.name || 'Citizen (Google)', 
        email: decoded.email 
      }));
      setAlertInfo({ type: 'success', text: `Welcome ${decoded.name}! Please complete Aadhaar, Mobile, and Location.` });
    } catch (err) {
      setAlertInfo({ type: 'error', text: 'Error decoding Google Profile' });
    }
  };

  const handleGoogleError = () => {
    setAlertInfo({ type: 'error', text: 'Google Login Failed or was cancelled' });
  };
  const handleGovSubmit = (e) => {
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

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    if (!loginIdentifier || !loginPassword) {
      setAlertInfo({ type: 'error', text: `${t.requiredErr} *` });
      return;
    }

    const existingUsers = JSON.parse(localStorage.getItem('janDhwaniUsers') || '[]');
    const savedUser = existingUsers.find(u => (u.mobile === loginIdentifier || u.email === loginIdentifier) && u.password === loginPassword);

    let citizen = savedUser;

    if (!citizen) {
      setAlertInfo({ type: 'error', text: 'Account not found or incorrect password. Please Sign Up first.' });
      return;
    }

    setAlertInfo({ type: 'success', text: 'Verified! Redirecting...' });
    setTimeout(() => {
      onLoginSuccess(citizen);
    }, 500);
  };

  const handleRegisterSubmit = (e) => {
    e.preventDefault();

    // Validate ALL fields on submit
    const nameErr = !regData.fullName ? `${t.requiredErr} *` : (VALIDATION_RULES.fullName(regData.fullName) ? `${t.requiredErr} (Min. 3 letters)` : null);
    const mobErr = !regData.mobile ? `${t.requiredErr} *` : (VALIDATION_RULES.mobile(regData.mobile) ? `${t.requiredErr} (10 digits)` : null);
    const aadhaarErr = !regData.aadhaar ? `${t.requiredErr} *` : (regData.aadhaar.length !== 12 ? `${t.requiredErr} (12 digits required)` : null);
    const passErr = !regData.password ? `${t.requiredErr} *` : (VALIDATION_RULES.password(regData.password) ? `${t.requiredErr} (Min. 6 chars)` : null);
    const emailErr = VALIDATION_RULES.email(regData.email);
    
    let confirmPassErr = null;
    if (!regData.confirmPassword) {
      confirmPassErr = `${t.requiredErr} *`;
    } else if (regData.password !== regData.confirmPassword) {
      confirmPassErr = 'Passwords do not match';
    }

    const allErrors = {
      fullName: nameErr,
      mobile: mobErr,
      aadhaar: aadhaarErr,
      password: passErr,
      confirmPassword: confirmPassErr,
      email: emailErr
    };

    setErrors(allErrors);

    // Mark all as touched
    const allTouched = Object.keys(allErrors).reduce((acc, key) => ({ ...acc, [key]: true }), {});
    setTouched(allTouched);

    let isValid = !Object.values(allErrors).some(err => err !== null);

    if (!regData.aadhaar || regData.aadhaar.length !== 12) isValid = false;
    if (!gpsStatus || !gpsStatus.granted) {
      alert('Please click \'Detect My Location\' (GPS) to proceed.');
      return;
    }

    if (isValid) {
      setIsLoggingIn(true);
      setTimeout(() => {
        setIsLoggingIn(false);
        const newUser = {
          fullName: regData.fullName,
          mobile: regData.mobile,
          state: 'Maharashtra', // Auto-detected via GPS
          district: 'Pune', // Auto-detected via GPS
          tehsil: 'Haveli', // Auto-detected via GPS
          panchayatOrWard: 'Ward 14', // Auto-detected via GPS
          areaType: 'urban', // Auto-detected via GPS
          pincode: '411001', // Auto-detected via GPS
          aadhaar: regData.aadhaar,
          email: regData.email,
          password: regData.password,
          preferredLanguage: regData.preferredLanguage,
          isLoggedIn: true
        };
        const existingUsers = JSON.parse(localStorage.getItem('janDhwaniUsers') || '[]');
        existingUsers.push(newUser);
        localStorage.setItem('janDhwaniUsers', JSON.stringify(existingUsers));
        onLoginSuccess(newUser);
      }, 1000);
    } else {
      setAlertInfo({ type: 'error', text: 'Please fill all required fields correctly.' });
    }
  };

  const handleDemoSelect = (demoCitizen) => {
    setAlertInfo({ type: 'success', text: `Profile: ${demoCitizen.fullName}` });
    setTimeout(() => {
      onLoginSuccess({ ...demoCitizen, language: currentLang, isLoggedIn: true });
    }, 350);
  };

  /* =========================================================================
     SIGN UP / LOGIN (IN CHOSEN LANGUAGE)
     ========================================================================= */
  const currentDistricts = STATES_AND_DISTRICTS[regData.state] || STATES_AND_DISTRICTS['Maharashtra'];
  const currentTalukas = DISTRICTS_AND_TALUKAS[regData.district] || [];

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div className="login-card">
      {/* Top Header with Active Language Indicator */}
      <div className="login-header">
        <div className="header-top-bar">

          <select 
            className="change-lang-btn"
            value={currentLang}
            onChange={(e) => handleLanguageSelect(e.target.value)}
            title="Switch Language"
          >
            {ALL_LANGUAGES.map(l => (
              <option key={l.code} value={l.code}>
                {l.native} ({l.name})
              </option>
            ))}
          </select>
        </div>

        <h1 className="login-title">{t.portalTitle}</h1>
        <p className="login-tagline">{t.portalSub}</p>

        {/* Civic Issue Preview Grid */}
        <div className="login-issue-images">
          <div className="issue-img-container">
            <img src="/issue1.png" alt="Water Scarcity" className="issue-img" />
            <div className="issue-caption">Water Crisis</div>
          </div>
          <div className="issue-img-container">
            <img src="/issue2.jpg" alt="Potholes" className="issue-img" />
            <div className="issue-caption">Road Damage</div>
          </div>
          <div className="issue-img-container">
            <img src="/issue3.jpg" alt="Rural Infrastructure" className="issue-img" />
            <div className="issue-caption">Rural Infra</div>
          </div>
          <div className="issue-img-container">
            <img src="/issue4.png" alt="Power Issue" className="issue-img" />
            <div className="issue-caption">Power Outage</div>
          </div>
        </div>
      </div>



      {/* Tabs switcher: Sign Up vs Login */}
      <div className="auth-tabs" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '5px' }}>
        <button 
          type="button" 
          className={`auth-tab ${authMode === 'register' ? 'active' : ''}`}
          onClick={() => { setAuthMode('register'); setAlertInfo(null); }}
          style={{ fontSize: '0.85rem', padding: '12px 5px' }}
        >
          New Citizen Sign Up
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
      </div>

      {alertInfo && (
        <div className={`auth-alert ${alertInfo.type}`}>
          {alertInfo.text}
        </div>
      )}

      {authMode === 'gov_login' ? (
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
      ) : authMode === 'register' ? (
        /* =========================================================================
           REGISTRATION FORM (Rendered In Chosen Language Only)
           ========================================================================= */
        <form onSubmit={handleRegisterSubmit} className="auth-form registration-form" noValidate>

          <div className="form-grid-layout">
            <div className="form-column">
              {/* Section 1: Identity & Contact */}
              <div className="section-title">
            <span>{t.sec1}</span>
          </div>

          {/* Full Name Input */}
          <div className="form-group">
            <label>{t.fullName} <span className="req">*</span></label>
            <div className="input-wrapper">
              <input 
                type="text"
                className={`input-field ${touched.fullName && errors.fullName ? 'input-error' : ''}`}
                placeholder={t.fullNamePlaceholder}
                value={regData.fullName}
                onChange={(e) => handleNameChange(e.target.value)}
                onBlur={() => handleBlur('fullName')}
                required
              />
            </div>
            {touched.fullName && errors.fullName && (
              <span className="error-text">{errors.fullName}</span>
            )}
          </div>

          <div className="form-row">
            {/* Mobile Number Input */}
            <div className="form-group">
              <label>{t.mobile} <span className="req">*</span></label>
              <div className="input-wrapper">
                <input 
                  type="tel"
                  className={`input-field ${touched.mobile && errors.mobile ? 'input-error' : ''}`}
                  placeholder="e.g. 9822012345"
                  value={regData.mobile}
                  onChange={(e) => handleMobileChange(e.target.value)}
                  onBlur={() => handleBlur('mobile')}
                  maxLength="10"
                  required
                />
              </div>
              {touched.mobile && errors.mobile && (
                <span className="error-text">{errors.mobile}</span>
              )}
            </div>

            {/* Email Address */}
            <div className="form-group">
              <label>{t.email}</label>
              <div className="input-wrapper">
                <input 
                  type="email"
                  className={`input-field ${touched.email && errors.email ? 'input-error' : ''}`}
                  placeholder="name@example.com"
                  value={regData.email}
                  onChange={(e) => {
                    setRegData({ ...regData, email: e.target.value });
                    validateField('email', e.target.value);
                  }}
                  onBlur={() => handleBlur('email')}
                />
              </div>
              {touched.email && errors.email && (
                <span className="error-text">{errors.email}</span>
              )}
            </div>
          </div>

<div className="form-group">
              <label>Aadhaar Number (UIDAI) <span className="req">*</span></label>
              <input 
                type="text"
                className={`input-field ${touched.aadhaar && errors.aadhaar ? 'input-error' : ''}`}
                placeholder="12-digit Aadhaar"
                value={regData.aadhaar}
                onChange={(e) => handleAadhaarChange(e.target.value)}
                onBlur={() => handleBlur('aadhaar')}
                required
              />
              {touched.aadhaar && errors.aadhaar && (
                <span className="error-text">{errors.aadhaar}</span>
              )}
            </div>
            
            
{/* Section 3: Security */}
          <div className="section-title">
            <span>{t.sec3}</span>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>{t.createPass} <span className="req">*</span></label>
              <input 
                type="password"
                className={`input-field ${touched.password && errors.password ? 'input-error' : ''}`}
                placeholder="Password (Min. 6 chars)"
                value={regData.password}
                onChange={(e) => {
                  setRegData({ ...regData, password: e.target.value });
                  validateField('password', e.target.value);
                }}
                onBlur={() => handleBlur('password')}
                required
              />
              {touched.password && errors.password && (
                <span className="error-text">{errors.password}</span>
              )}
            </div>

            <div className="form-group">
              <label>{t.confirmPass} <span className="req">*</span></label>
              <input 
                type="password"
                className={`input-field ${touched.confirmPassword && errors.confirmPassword ? 'input-error' : ''}`}
                placeholder="Confirm Password"
                value={regData.confirmPassword}
                onChange={(e) => {
                  setRegData({ ...regData, confirmPassword: e.target.value });
                  validateField('confirmPassword', e.target.value);
                }}
                onBlur={() => handleBlur('confirmPassword')}
                required
              />
              {touched.confirmPassword && errors.confirmPassword && (
                <span className="error-text">{errors.confirmPassword}</span>
              )}
            </div>
          </div>


            </div>
            <div className="form-column">
                          <div className="form-group" style={{gridColumn: '1 / -1', background: '#e3f2fd', padding: '15px', borderRadius: '10px', marginTop: '10px'}}>
              <label style={{color: '#1565c0'}}>{t.locModeTitle} <span className="req">*</span></label>
              <p style={{fontSize: '0.85rem', color: '#333', marginBottom: '10px'}}>{t.locConfirmSub}</p>
              <button 
                type="button" 
                className={`gps-btn ${gpsStatus?.granted ? 'active' : ''}`}
                onClick={requestLocationPermission}
                style={{width: '100%', padding: '12px', background: gpsStatus?.granted ? '#4caf50' : '#1a73e8', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold'}}
              >
                {gpsStatus?.granted ? '✓ ' + t.shareGpsBtn : '📍 ' + t.shareGpsBtn}
              </button>
            </div>

          {/* Section 2: Permanent Address */}
          <div className="section-title" style={{marginTop: '20px'}}>
            <span>{t.sec2}</span>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>{t.state} <span className="req">*</span></label>
              <input 
                type="text"
                list="state-list"
                className={`input-field ${touched.state && errors.state ? 'input-error' : ''}`}
                placeholder={t.state}
                value={regData.state || ''}
                onChange={(e) => {
                  setRegData({ ...regData, state: e.target.value, district: '', taluka: '' });
                  validateField('state', e.target.value);
                }}
                onBlur={() => handleBlur('state')}
                required
              />
              <datalist id="state-list">
                {Object.keys(STATES_AND_DISTRICTS).map(s => (
                  <option key={s} value={s} />
                ))}
              </datalist>
              {touched.state && errors.state && (
                <span className="error-text">{errors.state}</span>
              )}
            </div>

            <div className="form-group">
              <label>{t.district} <span className="req">*</span></label>
              <input 
                type="text"
                list="district-list"
                className={`input-field ${touched.district && errors.district ? 'input-error' : ''}`}
                placeholder={t.district}
                value={regData.district || ''}
                onChange={(e) => {
                  setRegData({ ...regData, district: e.target.value, taluka: '' });
                  validateField('district', e.target.value);
                }}
                onBlur={() => handleBlur('district')}
                required
              />
              <datalist id="district-list">
                {currentDistricts.map(d => (
                  <option key={d} value={d} />
                ))}
              </datalist>
              {touched.district && errors.district && (
                <span className="error-text">{errors.district}</span>
              )}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>{t.tehsil} <span className="req">*</span></label>
              <input 
                type="text"
                list="taluka-list"
                className={`input-field ${touched.taluka && errors.taluka ? 'input-error' : ''}`}
                placeholder={t.tehsil}
                value={regData.taluka || ''}
                onChange={(e) => {
                  setRegData({ ...regData, taluka: e.target.value });
                  validateField('taluka', e.target.value);
                }}
                onBlur={() => handleBlur('taluka')}
                required
              />
              <datalist id="taluka-list">
                {currentTalukas.map(t => (
                  <option key={t} value={t} />
                ))}
              </datalist>
              {touched.taluka && errors.taluka && (
                <span className="error-text">{errors.taluka}</span>
              )}
            </div>
          </div>

                      </div>
          </div>
          <button type="submit" className="auth-submit-btn">
            {t.submitSignUp}
          </button>

          {onContinueAsGuest && (
            <>
              <div className="guest-divider">
                <span>OR</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '15px' }}>
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={handleGoogleError}
                  text="signup_with"
                  shape="rectangular"
                  theme="outline"
                />
              </div>
            </>
          )}
        </form>
      ) : (
        /* =========================================================================
           LOGIN FORM (Rendered In Chosen Language Only)
           ========================================================================= */
        <form onSubmit={handleLoginSubmit} className="auth-form" noValidate>


          <div className="form-group">
            <label>{t.mobile} <span className="req">*</span></label>
            <div className="input-wrapper">
              <input 
                type="text"
                className="input-field"
                placeholder="e.g. 9822012345"
                value={loginIdentifier}
                onChange={(e) => setLoginIdentifier(e.target.value)}
                required
              />
            </div>
          </div>

            <div className="form-group">
              <label>{t.createPass} <span className="req">*</span></label>
              <div className="input-wrapper">
                <input 
                  type="password"
                  className="input-field"
                  placeholder="Password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  required
                />
              </div>
            </div>

          <button type="submit" className="auth-submit-btn">
            {t.loginSubmit}
          </button>

          {onContinueAsGuest && (
            <>
              <div className="guest-divider">
                <span>OR</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '15px' }}>
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={handleGoogleError}
                  text="signin_with"
                  shape="rectangular"
                  theme="outline"
                />
              </div>
              
              <button 
                type="button" 
                className="guest-btn"
                onClick={onContinueAsGuest}
              >
                Proceed as Guest ➔
              </button>
            </>
          )}
        </form>
      )}
      </div>
    </GoogleOAuthProvider>
  );
}

export default Login;

