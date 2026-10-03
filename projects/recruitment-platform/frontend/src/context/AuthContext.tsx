"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { User } from "@/lib/types";
import apiClient from "@/lib/api-client";

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = "recruitment_token";
const USER_KEY = "recruitment_user";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
    isAuthenticated: false,
  });

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    const userStr = localStorage.getItem(USER_KEY);

    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        apiClient.setToken(token);
        setState({
          user,
          token,
          isLoading: false,
          isAuthenticated: true,
        });
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        setState((s) => ({ ...s, isLoading: false }));
      }
    } else {
      setState((s) => ({ ...s, isLoading: false }));
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiClient.post<{ user: User; token: string }>(
      "/auth/login",
      { email, password }
    );

    const { user, token } = response;
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    apiClient.setToken(token);

    setState({
      user,
      token,
      isLoading: false,
      isAuthenticated: true,
    });
  }, []);

  const register = useCallback(
    async (name: string, email: string, password: string) => {
      const response = await apiClient.post<{ user: User; token: string }>(
        "/auth/register",
        { name, email, password }
      );

      const { user, token } = response;
      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      apiClient.setToken(token);

      setState({
        user,
        token,
        isLoading: false,
        isAuthenticated: true,
      });
    },
    []
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    apiClient.setToken(null);
    setState({
      user: null,
      token: null,
      isLoading: false,
      isAuthenticated: false,
    });
  }, []);

  const updateUser = useCallback((updates: Partial<User>) => {
    setState((prev) => {
      if (!prev.user) return prev;
      const updated = { ...prev.user, ...updates };
      localStorage.setItem(USER_KEY, JSON.stringify(updated));
      return { ...prev, user: updated };
    });
  }, []);

  return (
    <AuthContext.Provider
      value={{ ...state, login, register, logout, updateUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
