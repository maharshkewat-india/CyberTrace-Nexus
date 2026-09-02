/**
 * users/page.tsx - User management (admin only).
 */

"use client";

import { useEffect, useState } from "react";
import { Plus, AlertCircle, Users as UsersIcon, Shield, UserX } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api, getErrorMessage } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { formatDate } from "@/lib/utils";
import type { User } from "@/types";

const roleColors: Record<string, "danger" | "info" | "warning" | "secondary"> = {
  ADMINISTRATOR: "danger",
  "CASE INVESTIGATOR": "info",
  "FORENSIC ANALYST": "warning",
  "EVIDENCE CUSTODIAN": "secondary",
  AUDITOR: "secondary",
};

export default function UsersPage() {
  const { hasPermission } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [disabling, setDisabling] = useState<number | null>(null);

  // Create form
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("CASE INVESTIGATOR");

  const canManage = hasPermission("user.create");

  const loadUsers = async () => {
    try {
      setIsLoading(true);
      const response = await api.get<User[]>("/users");
      setUsers(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;

    try {
      setCreating(true);
      await api.post("/users", {
        username,
        password,
        role_name: role,
      });
      setCreateOpen(false);
      setUsername("");
      setPassword("");
      setRole("CASE INVESTIGATOR");
      loadUsers();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setCreating(false);
    }
  };

  const handleDisable = async (userId: number) => {
    try {
      setDisabling(userId);
      await api.post(`/users/${userId}/disable`);
      loadUsers();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDisabling(null);
    }
  };

  const handleEnable = async (userId: number) => {
    try {
      setDisabling(userId);
      await api.post(`/users/${userId}/enable`);
      loadUsers();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDisabling(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[var(--foreground)]">User Management</h1>
          <p className="text-[var(--foreground-muted)] mt-1">
            Manage system users and roles
          </p>
        </div>
        {canManage && (
          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Add User
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New User</DialogTitle>
                <DialogDescription>
                  Add a new user account to the system
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    placeholder="Enter username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Enter password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <Select value={role} onValueChange={setRole}>
                    <SelectTrigger id="role">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ADMINISTRATOR">Administrator</SelectItem>
                      <SelectItem value="CASE INVESTIGATOR">Case Investigator</SelectItem>
                      <SelectItem value="FORENSIC ANALYST">Forensic Analyst</SelectItem>
                      <SelectItem value="EVIDENCE CUSTODIAN">Evidence Custodian</SelectItem>
                      <SelectItem value="AUDITOR">Auditor</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setCreateOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" loading={creating}>
                    Create User
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-md bg-[var(--danger)]/10 border border-[var(--danger)]/30 text-[var(--danger)] text-sm">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Users Table */}
      <Card>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : users.length === 0 ? (
          <div className="text-center py-12">
            <UsersIcon className="h-12 w-12 mx-auto text-[var(--foreground-muted)]" />
            <p className="mt-4 text-[var(--foreground-muted)]">No users found</p>
            {canManage && (
              <Button
                variant="link"
                onClick={() => setCreateOpen(true)}
                className="mt-2"
              >
                Add your first user
              </Button>
            )}
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Username</TableHead>
                <TableHead>Roles</TableHead>
                <TableHead>Permissions</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Login</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-[var(--foreground-muted)]" />
                      <span className="font-medium">{user.username}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {user.role_names.map((r) => (
                        <Badge key={r} variant={roleColors[r] || "default"}>
                          {r}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-xs text-[var(--foreground-muted)]">
                      {user.permissions.length} permission{user.permissions.length !== 1 ? "s" : ""}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge variant={user.is_active ? "success" : "danger"}>
                      {user.is_active ? "Active" : "Disabled"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-[var(--foreground-muted)]">
                    {user.last_login ? formatDate(user.last_login) : "Never"}
                  </TableCell>
                  <TableCell className="text-right">
                    {canManage && user.id !== 1 && (
                      user.is_active ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-[var(--danger)] hover:text-[var(--danger)]"
                          loading={disabling === user.id}
                          onClick={() => handleDisable(user.id)}
                        >
                          <UserX className="h-4 w-4" />
                        </Button>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-[var(--success)] hover:text-[var(--success)]"
                          loading={disabling === user.id}
                          onClick={() => handleEnable(user.id)}
                        >
                          Enable
                        </Button>
                      )
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
