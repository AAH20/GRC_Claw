"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/Card";
import { Briefcase, Mail, Lock, User } from "lucide-react";
import Link from "next/link";

export function RegisterPage() {
  const { register, isLoading } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    try {
      await register(name, email, password);
      window.location.href = "/dashboard";
    } catch (err) {
      setError((err as Error).message || "Registration failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4 py-8">
      <Card variant="elevated" padding="lg" className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto h-12 w-12 rounded-xl bg-primary-600 flex items-center justify-center mb-4">
            <Briefcase className="h-6 w-6 text-white" />
          </div>
          <CardTitle className="text-2xl">Create Account</CardTitle>
          <CardDescription>Join RecruitHub to streamline your hiring</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
                {error}
              </div>
            )}
            <Input
              label="Full Name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              leftIcon={<User className="h-4 w-4" />}
              required
            />
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
              placeholder="Min. 8 characters"
              leftIcon={<Lock className="h-4 w-4" />}
              required
            />
            <Input
              label="Confirm Password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password"
              leftIcon={<Lock className="h-4 w-4" />}
              required
            />
            <Button type="submit" className="w-full" isLoading={isLoading}>
              Create Account
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
            Already have an account?{" "}
            <Link href="/login" className="text-primary-600 dark:text-primary-400 hover:underline">
              Sign in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
