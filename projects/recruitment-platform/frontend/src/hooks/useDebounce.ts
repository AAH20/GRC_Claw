"use client";

import { useState, useCallback, useRef, useEffect } from "react";

interface UseDebounceOptions {
  delay?: number;
}

export function useDebounce<T>(
  initialValue: T,
  options: UseDebounceOptions = {}
): [T, (value: T) => void, T] {
  const { delay = 300 } = options;
  const [value, setValue] = useState(initialValue);
  const [debouncedValue, setDebouncedValue] = useState(initialValue);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const setDebounced = useCallback(
    (newValue: T) => {
      setValue(newValue);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        setDebouncedValue(newValue);
      }, delay);
    },
    [delay]
  );

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return [value, setDebounced, debouncedValue];
}
