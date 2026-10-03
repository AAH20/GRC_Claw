'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { apiClient } from '@/lib/api';
import type { User, AuthTokens, LoginRequest, RegisterRequest } from '@/lib/types';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const STORAGE_KEY = 'gc_auth_tokens';

function getStoredTokens(): AuthTokens | null {
  if (typeof window === 'undefined') return null;
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

function storeTokens(tokens: AuthTokens): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens));
}

function clearStoredTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(STORAGE_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const tokens = getStoredTokens();
    if (tokens) {
      apiClient.setTokens(tokens);
      apiClient
        .getCurrentUser()
        .then(setUser)
        .catch(() => {
          apiClient.clearTokens();
          clearStoredTokens();
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (credentials: LoginRequest) => {
    const response = await apiClient.login(credentials);
    storeTokens(response.tokens);
    setUser(response.user);
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    const response = await apiClient.register(data);
    storeTokens(response.tokens);
    setUser(response.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiClient.logout();
    } finally {
      apiClient.clearTokens();
      clearStoredTokens();
      setUser(null);
    }
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await apiClient.getCurrentUser();
      setUser(currentUser);
    } catch {
      apiClient.clearTokens();
      clearStoredTokens();
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
