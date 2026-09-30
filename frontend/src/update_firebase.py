import os
import re

filepath = r'c:\Users\HP\OneDrive\jandhwani local\frontend\src\App.jsx'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add imports for firebase
firebase_import = "import { database } from './firebase';\nimport { ref, onValue, set, remove } from 'firebase/database';\n"
if "import { database }" not in content:
    content = content.replace("import './App.css';", "import './App.css';\n" + firebase_import)

# Replace activeComplaints state
old_state = """  const [activeComplaints, setActiveComplaints] = useState(() => {
    try {
      const saved = localStorage.getItem('jandhwani_active_complaints');
      return saved ? JSON.parse(saved) : DEFAULT_HOTSPOTS;
    } catch {
      return DEFAULT_HOTSPOTS;
    }
  });"""
new_state = "  const [activeComplaints, setActiveComplaints] = useState(DEFAULT_HOTSPOTS);"
if old_state in content:
    content = content.replace(old_state, new_state)

# Replace resolvedRecords state
old_resolved = """  const [resolvedRecords, setResolvedRecords] = useState(() => {
    try {
      const saved = localStorage.getItem('jandhwani_resolved_records');
      return saved ? JSON.parse(saved) : INITIAL_RESOLVED_RECORDS;
    } catch {
      return INITIAL_RESOLVED_RECORDS;
    }
  });"""
new_resolved = "  const [resolvedRecords, setResolvedRecords] = useState(INITIAL_RESOLVED_RECORDS);"
if old_resolved in content:
    content = content.replace(old_resolved, new_resolved)

# Replace the useEffects for localStorage with Firebase listeners
old_effects = """  // Sync to Local Storage
  useEffect(() => {
    try {
      localStorage.setItem('jandhwani_active_complaints', JSON.stringify(activeComplaints));
    } catch (e) {
      console.warn("Could not sync active complaints", e);
    }
  }, [activeComplaints]);

  useEffect(() => {
    try {
      localStorage.setItem('jandhwani_resolved_records', JSON.stringify(resolvedRecords));
    } catch (e) {
      console.warn("Could not sync resolved records", e);
    }
  }, [resolvedRecords]);"""
  
new_effects = """  // Sync with Firebase Realtime Database
  useEffect(() => {
    const complaintsRef = ref(database, 'complaints');
    const unsubscribe = onValue(complaintsRef, (snapshot) => {
      const data = snapshot.val();
      if (data) {
        const complaintsArray = Object.values(data);
        complaintsArray.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
        setActiveComplaints(complaintsArray);
      } else {
        setActiveComplaints(DEFAULT_HOTSPOTS);
      }
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    const resolvedRef = ref(database, 'resolved');
    const unsubscribe = onValue(resolvedRef, (snapshot) => {
      const data = snapshot.val();
      if (data) {
        const resolvedArray = Object.values(data);
        resolvedArray.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
        setResolvedRecords(resolvedArray);
      } else {
        setResolvedRecords(INITIAL_RESOLVED_RECORDS);
      }
    });
    return () => unsubscribe();
  }, []);"""

if old_effects in content:
    content = content.replace(old_effects, new_effects)


# Replace handleClearAllComplaints
old_clear = """  const handleClearAllComplaints = () => {
    setActiveComplaints([]);
    setSubmissionResult(null);
  };"""
new_clear = """  const handleClearAllComplaints = () => {
    set(ref(database, 'complaints'), null);
    setSubmissionResult(null);
  };"""
content = content.replace(old_clear, new_clear)

# Update handleResolveByCitizen
# We need to find the `setActiveComplaints(prev => prev.filter(c => c.id !== ticketId));` and `setResolvedRecords` 
old_resolve = """    setActiveComplaints(prev => prev.filter(c => c.id !== ticketId));
    setResolvedRecords(prev => [newRecord, ...prev.filter(r => r.id !== ticketId)]);"""
new_resolve = """    // Move from complaints to resolved in Firebase
    newRecord.timestamp = Date.now();
    set(ref(database, 'resolved/' + ticketId), newRecord);
    remove(ref(database, 'complaints/' + ticketId));"""
content = content.replace(old_resolve, new_resolve)


# Replace in handleSubmit where we set active complaints manually
old_submit_push = """      setActiveComplaints(prev => [newSpot, ...prev]);"""
new_submit_push = """      // Push to Firebase directly from Frontend
      newSpot.timestamp = Date.now();
      set(ref(database, 'complaints/' + newSpot.id), newSpot);"""
content = content.replace(old_submit_push, new_submit_push)


with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated App.jsx successfully!")
