"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/Card";
import { Briefcase, Mail, Lock } from "lucide-react";
import Link from "next/link";

export default function LoginPage() {
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      window.location.href = "/dashboard";
    } catch (err) {
      setError((err as Error).message || "Login failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <Card variant="elevated" padding="lg" className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto h-12 w-12 rounded-xl bg-primary-600 flex items-center justify-center mb-4">
            <Briefcase className="h-6 w-6 text-white" />
          </div>
          <CardTitle className="text-2xl">Welcome Back</CardTitle>
          <CardDescription>Sign in to your RecruitHub account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
                {error}
              </div>
            )}
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              leftIcon={<Mail className="h-4 w-4" />}
              required
            />
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              leftIcon={<Lock className="h-4 w-4" />}
              required
            />
            <Button type="submit" className="w-full" isLoading={isLoading}>
              Sign In
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="text-primary-600 dark:text-primary-400 hover:underline">
              Sign up
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
