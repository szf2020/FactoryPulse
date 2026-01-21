import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext();

/**
 * AuthProvider Component.
 * Manages the authentication state of the application.
 * Handles Login, Registration, Session Restoration, and Logout.
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  /**
   * Session Restoration Effect.
   * Checks LocalStorage for existing tokens on page load to restore the user session.
   */
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user_data');
    
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  /**
   * Logs in the user.
   * Sends credentials to the backend to retrieve JWT tokens.
   * Stores tokens and user data in LocalStorage.
   * @param {string} username 
   * @param {string} password 
   */
  const login = async (username, password) => {
    try {
      // Request JWT Token from Django Backend
      const response = await api.post('token/', { username, password });
      
      const { access, refresh } = response.data;
      
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      
      const userData = { username }; 
      localStorage.setItem('user_data', JSON.stringify(userData));
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      console.error("Login Error:", error);
      return { success: false, message: 'Invalid credentials' };
    }
  };

  /**
   * Registers a new user.
   * Creates a new account and automatically logs the user in upon success.
   * @param {string} username 
   * @param {string} email 
   * @param {string} password 
   */
  const register = async (username, email, password) => {
    try {
      await api.post('register/', { username, email, password });
      return await login(username, password);
    } catch (error) {
      console.error("Registration Error:", error);
      return { success: false, message: 'Error creating account.' };
    }
  };

  /**
   * Logs out the user.
   * Clears all session data from LocalStorage and redirects to the login page.
   */
  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_data');
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);