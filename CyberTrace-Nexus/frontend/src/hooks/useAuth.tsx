/**
 * useAuth.tsx - React context for authentication state.
 */

"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  getStoredUser,
  getStoredToken,
  login as loginAction,
  logout as logoutAction,
  type User,
} from "@/lib/auth";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<User>;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasRole: (role: string) => boolean;
  refreshUser: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Hydrate from localStorage on mount
    const stored = getStoredUser();
    const storedToken = getStoredToken();
    setUser(stored);
    setToken(storedToken);
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string): Promise<User> => {
    const response = await loginAction(username, password);
    setUser(response.user);
    setToken(response.access_token);
    return response.user;
  };

  const logout = () => {
    logoutAction();
    setUser(null);
    setToken(null);
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    return user.permissions.includes(permission);
  };

  const hasAnyPermission = (permissions: string[]): boolean => {
    if (!user) return false;
    return permissions.some((p) => user.permissions.includes(p));
  };

  const hasRole = (role: string): boolean => {
    if (!user) return false;
    return user.role_names.includes(role);
  };

  const refreshUser = () => {
    setUser(getStoredUser());
  };

  const value: AuthContextValue = {
    user,
    token,
    isAuthenticated: !!user && !!token,
    isLoading,
    login,
    logout,
    hasPermission,
    hasAnyPermission,
    hasRole,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (ctx === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
