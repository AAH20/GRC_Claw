"use client";

import { useState, useEffect, useCallback } from "react";
import { PaginatedResponse, ApiError } from "@/lib/types";

interface UseApiOptions<T> {
  initialData?: T;
  enabled?: boolean;
  params?: Record<string, string>;
}

interface UseApiResult<T> {
  data: T | null;
  error: ApiError | null;
  isLoading: boolean;
  isError: boolean;
  refetch: () => void;
  setData: (data: T) => void;
}

export function useApi<T>(
  fetcher: () => Promise<T>,
  options: UseApiOptions<T> = {}
): UseApiResult<T> {
  const { initialData, enabled = true, params } = options;
  const [data, setData] = useState<T | null>(initialData ?? null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState(enabled);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      setData(result);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setIsLoading(false);
    }
  }, [fetcher, params]);

  useEffect(() => {
    if (enabled) fetchData();
  }, [enabled, fetchData]);

  return {
    data,
    error,
    isLoading,
    isError: error !== null,
    refetch: fetchData,
    setData,
  };
}

export function usePaginatedApi<T>(
  fetcher: (page: number, limit: number) => Promise<PaginatedResponse<T>>,
  initialPage = 1,
  limit = 10
) {
  const [data, setData] = useState<T[]>([]);
  const [page, setPage] = useState(initialPage);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchData = useCallback(
    async (p: number) => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await fetcher(p, limit);
        setData(result.data);
        setTotalPages(result.totalPages);
        setTotal(result.total);
        setPage(p);
      } catch (err) {
        setError(err as ApiError);
      } finally {
        setIsLoading(false);
      }
    },
    [fetcher, limit]
  );

  useEffect(() => {
    fetchData(initialPage);
  }, [fetchData, initialPage]);

  return {
    data,
    page,
    totalPages,
    total,
    error,
    isLoading,
    setPage: fetchData,
    refetch: () => fetchData(page),
  };
}
