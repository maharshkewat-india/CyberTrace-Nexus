"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Shield, Eye, FileSearch, Lock, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import { getErrorMessage } from "@/lib/api";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(username, password);
      router.push("/dashboard");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)]">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--background-secondary)]">
        <div className="container mx-auto px-4 py-4 flex items-center gap-3">
          <Shield className="h-8 w-8 text-[var(--accent)]" />
          <div>
            <h1 className="text-lg font-bold text-[var(--foreground)]">
              Digital Forensics Evidence Management
            </h1>
            <p className="text-xs text-[var(--foreground-muted)]">
              Chain of Custody &amp; Evidence Tracking
            </p>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          {/* Left side - Branding */}
          <div className="hidden lg:flex flex-col gap-8 p-8">
            <div className="space-y-4">
              <h2 className="text-4xl font-bold text-[var(--foreground)]">
                Secure Evidence<br />
                <span className="text-[var(--accent)]">Management</span>
              </h2>
              <p className="text-[var(--foreground-muted)] text-lg">
                A comprehensive platform for managing digital forensics cases,
                evidence chain of custody, and forensic analysis.
              </p>
            </div>

            {/* Features */}
            <div className="grid grid-cols-1 gap-4">
              <div className="flex items-start gap-4 p-4 rounded-lg bg-[var(--background-tertiary)] border border-[var(--border)]">
                <div className="p-2 rounded-lg bg-[var(--accent)]/10">
                  <Shield className="h-5 w-5 text-[var(--accent)]" />
                </div>
                <div>
                  <h3 className="font-semibold text-[var(--foreground)]">
                    Secure Chain of Custody
                  </h3>
                  <p className="text-sm text-[var(--foreground-muted)]">
                    Track every evidence handoff with cryptographic verification
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 rounded-lg bg-[var(--background-tertiary)] border border-[var(--border)]">
                <div className="p-2 rounded-lg bg-[var(--success)]/10">
                  <FileSearch className="h-5 w-5 text-[var(--success)]" />
                </div>
                <div>
                  <h3 className="font-semibold text-[var(--foreground)]">
                    MD5/SHA-256 Verification
                  </h3>
                  <p className="text-sm text-[var(--foreground-muted)]">
                    Automatic hash computation and integrity verification
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 rounded-lg bg-[var(--background-tertiary)] border border-[var(--border)]">
                <div className="p-2 rounded-lg bg-[var(--warning)]/10">
                  <Lock className="h-5 w-5 text-[var(--warning)]" />
                </div>
                <div>
                  <h3 className="font-semibold text-[var(--foreground)]">
                    Role-Based Access Control
                  </h3>
                  <p className="text-sm text-[var(--foreground-muted)]">
                    Granular permissions with full audit logging
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 rounded-lg bg-[var(--background-tertiary)] border border-[var(--border)]">
                <div className="p-2 rounded-lg bg-[var(--info)]/10">
                  <Eye className="h-5 w-5 text-[var(--info)]" />
                </div>
                <div>
                  <h3 className="font-semibold text-[var(--foreground)]">
                    Complete Audit Trail
                  </h3>
                  <p className="text-sm text-[var(--foreground-muted)]">
                    Every action logged with timestamps and user details
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right side - Login form */}
          <Card className="w-full max-w-md mx-auto">
            <CardHeader className="space-y-1">
              <CardTitle className="text-2xl font-bold">Sign In</CardTitle>
              <CardDescription>
                Enter your credentials to access the system
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="flex items-center gap-2 p-3 rounded-md bg-[var(--danger)]/10 border border-[var(--danger)]/30 text-[var(--danger)] text-sm">
                    <AlertCircle className="h-4 w-4 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    type="text"
                    placeholder="Enter your username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    autoComplete="username"
                    autoFocus
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  loading={isLoading}
                >
                  Sign In
                </Button>
              </form>

              <div className="mt-6 pt-6 border-t border-[var(--border)]">
                <p className="text-xs text-center text-[var(--foreground-muted)]">
                  Default credentials: <code className="px-1 py-0.5 rounded bg-[var(--background-tertiary)] text-[var(--foreground)]">admin</code> / <code className="px-1 py-0.5 rounded bg-[var(--background-tertiary)] text-[var(--foreground)]">Admin@123</code>
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--border)] bg-[var(--background-secondary)]">
        <div className="container mx-auto px-4 py-3 text-center text-xs text-[var(--foreground-muted)]">
          Digital Forensics Evidence Management System &mdash; Secure Chain of Custody Tracking
        </div>
      </footer>
    </div>
  );
}
