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

  const create = useCallback(
    async (body: unknown) => {
      const created = await api.post<T>(path, body);
      setItems((prev) => [created, ...prev]);
      return created;
    },
    [path]
  );

  const update = useCallback(
    async (id: string, body: unknown) => {
      const updated = await api.patch<T>(`${path}/${id}`, body);
      setItems((prev) => prev.map((item) => (item.id === id ? updated : item)));
      return updated;
    },
    [path]
  );

  const remove = useCallback(
    async (id: string) => {
      await api.delete(`${path}/${id}`);
      setItems((prev) => prev.filter((item) => item.id !== id));
    },
    [path]
  );

  return { items, loading, error, reload, create, update, remove };
}
