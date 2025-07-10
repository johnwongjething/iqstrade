import React, { createContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from './config';

export const UserContext = createContext();

export function UserProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [csrfToken, setCsrfToken] = useState(null);
  const navigate = useNavigate();

  // Place the improved useEffect after state and navigate declarations
  useEffect(() => {
    console.log('useEffect /api/me triggered (mount)');
    if (!user && !loading) {
      setLoading(true);
      const checkAuth = async () => {
        try {
          const res = await fetch(`${API_BASE_URL}/api/me`, { credentials: 'include' });
          if (!res.ok && res.status === 401) {
            setUser(null);
            navigate('/login');
          } else if (res.ok) {
            const data = await res.json();
            if (data && !data.error) setUser(data);
          }
        } catch (error) {
          console.error('Error fetching user on mount:', error);
          if (!user) navigate('/login');
        } finally {
          setLoading(false);
        }
      };
      checkAuth();
    }
  }, [navigate, user, loading]);

  const fetchCsrfToken = useCallback(async () => {
    console.log('fetchCsrfToken triggered, user:', user);
    try {
      const res = await fetch(`${API_BASE_URL}/api/csrf-token`, { credentials: 'include' });
      if (res.status === 401) {
        setCsrfToken(null);
        setUser(null);
        navigate('/login');
        return null;
      }
      if (res.ok) {
        const data = await res.json();
        setCsrfToken(data.csrf_token);
        return data.csrf_token;
      }
    } catch {}
    setCsrfToken(null);
    setUser(null);
    navigate('/login');
    return null;
  }, [navigate, API_BASE_URL]);

  const fetchUserIfNeeded = useCallback(async (force = false) => {
    console.log('fetchUserIfNeeded triggered, user:', user, 'force:', force);
    if (!force && user && user.username) return true;
    try {
      const res = await fetch(`${API_BASE_URL}/api/me`, { credentials: 'include' });
      if (res.status === 401) {
        setUser(null);
        navigate('/login');
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
      console.error('Error fetching user:', error);
    }
    setUser(null);
    navigate('/login');
    return false;
  }, [user, navigate, API_BASE_URL]);

  useEffect(() => {
    if (user && user.username) {
      fetchCsrfToken();
    } else {
      setCsrfToken(null); // Clear token when logged out
    }
  }, [user, fetchCsrfToken]);

  return (
    <UserContext.Provider value={{ user, setUser, loading, csrfToken, setCsrfToken, fetchCsrfToken, fetchUserIfNeeded }}>
      {children}
    </UserContext.Provider>
  );
}

export default UserProvider;
