"use client";

import { Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useCurrentUser } from "@/components/UserContext";
import { ErrorBanner, LoadingState, PageHeader, Spinner } from "@/components/ui";
import { api } from "@/lib/api-client";
import type { AdminUser } from "@/lib/types";

export default function AdminUsersPage() {
  const currentUser = useCurrentUser();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState<number | null>(null);

  const load = useCallback(async () => {
    setError("");
    try {
      setUsers((await api.getUsers()).users);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load users.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const remove = async (user: AdminUser) => {
    if (!window.confirm(`Delete ${user.username} and all of their ${user.review_count} reviews? This cannot be undone.`)) return;
    setDeleting(user.id);
    try {
      await api.deleteUser(user.id);
      setUsers((prev) => prev.filter((u) => u.id !== user.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete user.");
    } finally {
      setDeleting(null);
    }
  };

  if (currentUser?.role !== "admin") {
    return <ErrorBanner message="You need admin access to view this page." />;
  }
  if (loading) return <LoadingState label="Loading users…" />;

  return (
    <div>
      <PageHeader title="Users" description={`${users.length} registered account${users.length === 1 ? "" : "s"}`} />
      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} />
        </div>
      )}
      <div className="card overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="muted border-b border-zinc-200 text-xs dark:border-zinc-800">
            <tr>
              <th className="px-4 py-3 font-medium">User</th>
              <th className="px-4 py-3 font-medium">Role</th>
              <th className="px-4 py-3 text-right font-medium">Reviews</th>
              <th className="px-4 py-3 font-medium">Joined</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {users.map((u) => (
              <tr key={u.id}>
                <td className="px-4 py-3 font-medium">{u.username}</td>
                <td className="px-4 py-3 capitalize">{u.role}</td>
                <td className="px-4 py-3 text-right tabular-nums">{u.review_count.toLocaleString()}</td>
                <td className="muted px-4 py-3">{u.created_at.split(/[ T]/)[0]}</td>
                <td className="px-4 py-3 text-right">
                  {u.id !== currentUser.id && (
                    <button
                      type="button"
                      onClick={() => remove(u)}
                      disabled={deleting === u.id}
                      className="btn-danger px-2.5 py-1 text-xs"
                      aria-label={`Delete ${u.username}`}
                    >
                      {deleting === u.id ? <Spinner size={12} /> : <Trash2 size={12} />} Delete
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
