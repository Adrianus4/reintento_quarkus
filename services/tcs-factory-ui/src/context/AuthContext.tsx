// src/context/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { api, setStoredToken, clearStoredToken } from '../services/api';
import { Role } from '../types';

interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  assigned_clients: string[];
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  role: Role | null;
  login: (email: string, password: string, remember?: boolean) => Promise<void>;
  register: (email: string, password: string, fullName: string, role?: string) => Promise<void>;
  setupInitialAdmin: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('tcs_auth_token') || sessionStorage.getItem('tcs_auth_token');
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshProfile = async () => {
    try {
      const profile = await api.auth.getMe();
      const clientInfo = await api.auth.getMeClients();
      
      setUser({
        id: profile.id,
        email: profile.email,
        full_name: profile.full_name,
        role: profile.role.toUpperCase() as Role,
        assigned_clients: clientInfo.client_codes || [],
      });
    } catch (err) {
      console.warn('Failed to fetch user profile, clearing session', err);
      clearStoredToken();
      setToken(null);
      setUser(null);
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        await refreshProfile();
      }
      setIsLoading(false);
    };

    initAuth();

    const handleUnauthorized = () => {
      setToken(null);
      setUser(null);
    };

    window.addEventListener('tcs:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('tcs:unauthorized', handleUnauthorized);
  }, [token]);

  const login = async (email: string, password: string, remember: boolean = true) => {
    setIsLoading(true);
    try {
      const res = await api.auth.login({ email, password });
      setStoredToken(res.access_token, remember);
      setToken(res.access_token);
      
      const roleUpper = res.user.role.toUpperCase() as Role;
      const assigned = roleUpper === 'ADMIN' ? ['*'] : (res.user.assigned_clients || []);

      setUser({
        id: res.user.id,
        email: res.user.email,
        full_name: res.user.full_name,
        role: roleUpper,
        assigned_clients: assigned,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName: string, role: string = 'ADMIN') => {
    setIsLoading(true);
    try {
      const res = await api.auth.register({ email, password, full_name: fullName, role });
      setStoredToken(res.access_token, true);
      setToken(res.access_token);
      
      const roleUpper = res.user.role.toUpperCase() as Role;
      const assigned = roleUpper === 'ADMIN' ? ['*'] : (res.user.assigned_clients || []);

      setUser({
        id: res.user.id,
        email: res.user.email,
        full_name: res.user.full_name,
        role: roleUpper,
        assigned_clients: assigned,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const setupInitialAdmin = async (email: string, password: string, fullName: string) => {
    return register(email, password, fullName, 'ADMIN');
  };

  const logout = () => {
    clearStoredToken();
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        role: user ? user.role : null,
        login,
        register,
        setupInitialAdmin,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
