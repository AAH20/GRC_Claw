'use client';

import React, { type ReactNode } from 'react';
import { AuthProvider } from '@/context/AuthContext';
import { ThemeProvider } from '@/context/ThemeContext';

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>{children}</AuthProvider>
    </ThemeProvider>
  );
}
