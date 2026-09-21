"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api-client";

interface WithId {
  id: string;
}

/** Generic list/create/update/delete against one REST collection endpoint. */
export function useResource<T extends WithId>(path: string) {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<T[]>(path);
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    reload();
  }, [reload]);

  // Reload from the server after every mutation rather than patching local
  // state optimistically: some endpoints have side effects beyond the one
  // row returned (e.g. creating a fixed transaction also generates future
  // occurrences, deleting one cancels them), so the list needs a real
  // refetch to stay correct.
  const create = useCallback(
    async (body: unknown) => {
      const created = await api.post<T>(path, body);
      await reload();
      return created;
    },
    [path, reload]
  );

  const update = useCallback(
    async (id: string, body: unknown) => {
      const updated = await api.patch<T>(`${path}/${id}`, body);
      await reload();
      return updated;
    },
    [path, reload]
  );

  const remove = useCallback(
    async (id: string) => {
      await api.delete(`${path}/${id}`);
      await reload();
    },
    [path, reload]
  );

  return { items, loading, error, reload, create, update, remove };
}
