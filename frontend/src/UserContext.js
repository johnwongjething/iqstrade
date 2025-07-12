import React, { createContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from './config';

export const UserContext = createContext();

export function UserProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [csrfToken, setCsrfToken] = useState(null);
  const navigate = useNavigate();

  // Initial user authentication check
  useEffect(() => {
    if (!user && loading) {
      const checkAuth = async () => {
        try {
          const res = await fetch(`${API_BASE_URL}/api/me`, { credentials: 'include' });
          if (res.status === 401) {
            setUser(null);
            setLoading(false);
            // Do NOT navigate to /login here; let unauthenticated users stay on home page
          } else if (res.ok) {
            const data = await res.json();
            if (data && !data.error) setUser(data);
            setLoading(false);
          } else {
            setLoading(false);
          }
        } catch (error) {
          setLoading(false);
          setUser(null);
          // Do NOT navigate to /login here
        }
      };
      checkAuth();
    }
  }, [navigate, user, loading]);

  // Fetch CSRF token, but do not block UI or log out if token is missing/null
  const fetchCsrfToken = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/csrf-token`, { credentials: 'include' });
      if (res.status === 401) {
        setCsrfToken(null);
        setUser(null);
        // Do NOT navigate to /login here
        return null;
      }
      if (res.ok) {
        const data = await res.json();
        setCsrfToken(data.csrf_token || null); // Accept null/undefined
        return data.csrf_token || null;
      }
    } catch (e) {
      // Network or other error: do not block UI, just clear CSRF
      setCsrfToken(null);
    }
    return null;
  }, [navigate, API_BASE_URL]);

  // Fetch user if needed, with optional force
  const fetchUserIfNeeded = useCallback(async (force = false) => {
    if (!force && user && user.username) return true;
    try {
      const res = await fetch(`${API_BASE_URL}/api/me`, { credentials: 'include' });
      if (res.status === 401) {
        setUser(null);
        // Only navigate to /login if trying to access a protected route (not here)
        return false;
      }
      if (res.ok) {
        const data = await res.json();
        if (!data.error) {
          setUser(data);
          return true;
        }
      }
    } catch (error) {
      setUser(null);
      // Only navigate to /login if trying to access a protected route
    }
    return false;
  }, [user, navigate, API_BASE_URL]);

  // When user changes, fetch CSRF token if logged in, else clear it
  useEffect(() => {
    if (user && user.username) {
      fetchCsrfToken();
    } else {
      setCsrfToken(null);
    }
  }, [user, fetchCsrfToken]);

  // Always clear loading if user or CSRF token changes (never block UI)
  useEffect(() => {
    if (loading) setLoading(false);
  }, [user, csrfToken, loading]);

  return (
    <UserContext.Provider value={{ user, setUser, loading, csrfToken, setCsrfToken, fetchCsrfToken, fetchUserIfNeeded }}>
      {children}
    </UserContext.Provider>
  );
}

export default UserProvider;
