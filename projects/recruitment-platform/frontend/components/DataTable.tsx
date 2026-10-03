'use client';

import React, { useState, useMemo, useCallback } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

export interface Column<T> {
  key: string;
  header: string;
  accessor: (row: T) => React.ReactNode;
  sortable?: boolean;
  filterable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

export interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  searchPlaceholder?: string;
  searchKeys?: (keyof T)[];
  pageSize?: number;
  pageSizeOptions?: number[];
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
  rowClassName?: (row: T) => string;
  className?: string;
}

type SortDirection = 'asc' | 'desc';

interface SortState {
  key: string;
  direction: SortDirection;
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function DataTable<T extends Record<string, unknown>>({
  data,
  columns,
  searchPlaceholder = 'Search...',
  searchKeys = [],
  pageSize = 10,
  pageSizeOptions = [5, 10, 25, 50],
  emptyMessage = 'No data available',
  onRowClick,
  rowClassName,
  className = '',
}: DataTableProps<T>) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortState, setSortState] = useState<SortState | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(pageSize);

  // ── Filtering ─────────────────────────────────────────────────────────────

  const filteredData = useMemo(() => {
    if (!searchQuery.trim()) return data;
    const query = searchQuery.toLowerCase();
    return data.filter((row) => {
      if (searchKeys.length > 0) {
        return searchKeys.some((key) => {
          const value = row[key];
          return value != null && String(value).toLowerCase().includes(query);
        });
      }
      // Fallback: search all string values in the row
      return Object.values(row).some(
        (val) => val != null && String(val).toLowerCase().includes(query)
      );
    });
  }, [data, searchQuery, searchKeys]);

  // ── Sorting ───────────────────────────────────────────────────────────────

  const sortedData = useMemo(() => {
    if (!sortState) return filteredData;
    const { key, direction } = sortState;
    const column = columns.find((c) => c.key === key);
    if (!column) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aVal = (a as Record<string, unknown>)[key];
      const bVal = (b as Record<string, unknown>)[key];

      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return direction === 'asc' ? -1 : 1;
      if (bVal == null) return direction === 'asc' ? 1 : -1;

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return direction === 'asc' ? aVal - bVal : bVal - aVal;
      }

      const aStr = String(aVal);
      const bStr = String(bVal);
      const cmp = aStr.localeCompare(bStr);
      return direction === 'asc' ? cmp : -cmp;
    });
  }, [filteredData, sortState, columns]);

  // ── Pagination ────────────────────────────────────────────────────────────

  const totalPages = Math.max(1, Math.ceil(sortedData.length / rowsPerPage));
  const safePage = Math.min(currentPage, totalPages);
  const startIndex = (safePage - 1) * rowsPerPage;
  const paginatedData = sortedData.slice(startIndex, startIndex + rowsPerPage);

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleSort = useCallback(
    (column: Column<T>) => {
      if (column.sortable === false) return;
      setSortState((prev) => {
        if (!prev || prev.key !== column.key) {
          return { key: column.key, direction: 'asc' };
        }
        if (prev.direction === 'asc') {
          return { key: column.key, direction: 'desc' };
        }
        return null;
      });
    },
    []
  );

  const handleSearch = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setCurrentPage(1);
  }, []);

  const handlePageSizeChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      setRowsPerPage(Number(e.target.value));
      setCurrentPage(1);
    },
    []
  );

  const goToPage = useCallback(
    (page: number) => {
      setCurrentPage(Math.max(1, Math.min(page, totalPages)));
    },
    [totalPages]
  );

  // ── Render helpers ────────────────────────────────────────────────────────

  const getSortIcon = (column: Column<T>) => {
    if (column.sortable === false) return null;
    if (!sortState || sortState.key !== column.key) {
      return (
        <span className="ml-1 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
          ↕
        </span>
      );
    }
    return (
      <span className="ml-1 text-blue-500">
        {sortState.direction === 'asc' ? '↑' : '↓'}
      </span>
    );
  };

  const alignClass = (align?: 'left' | 'center' | 'right') => {
    switch (align) {
      case 'center':
        return 'text-center';
      case 'right':
        return 'text-right';
      default:
        return 'text-left';
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className={`w-full ${className}`}>
      {/* Search & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <div className="relative flex-1 max-w-sm">
          <input
            type="text"
            value={searchQuery}
            onChange={handleSearch}
            placeholder={searchPlaceholder}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            aria-label="Search table"
          />
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>Rows per page:</span>
          <select
            value={rowsPerPage}
            onChange={handlePageSizeChange}
            className="border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Rows per page"
          >
            {pageSizeOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  style={column.width ? { width: column.width } : undefined}
                  className={`px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider ${alignClass(
                    column.align
                  )} ${
                    column.sortable !== false
                      ? 'cursor-pointer select-none group hover:bg-gray-100'
                      : ''
                  }`}
                  onClick={() => handleSort(column)}
                  role={column.sortable !== false ? 'button' : undefined}
                  tabIndex={column.sortable !== false ? 0 : undefined}
                  onKeyDown={
                    column.sortable !== false
                      ? (e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handleSort(column);
                          }
                        }
                      : undefined
                  }
                >
                  <span className="inline-flex items-center">
                    {column.header}
                    {getSortIcon(column)}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-gray-500 text-sm"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, idx) => (
                <tr
                  key={idx}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={`
                    ${onRowClick ? 'cursor-pointer hover:bg-blue-50 transition-colors' : ''}
                    ${rowClassName ? rowClassName(row) : ''}
                  `}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={`px-4 py-3 text-sm text-gray-700 ${alignClass(
                        column.align
                      )}`}
                    >
                      {column.accessor(row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {sortedData.length > 0 && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mt-4">
          <p className="text-sm text-gray-600">
            Showing{' '}
            <span className="font-medium">
              {startIndex + 1}–{Math.min(startIndex + rowsPerPage, sortedData.length)}
            </span>{' '}
            of <span className="font-medium">{sortedData.length}</span> results
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => goToPage(1)}
              disabled={safePage === 1}
              className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
              aria-label="First page"
            >
              «
            </button>
            <button
              onClick={() => goToPage(safePage - 1)}
              disabled={safePage === 1}
              className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
              aria-label="Previous page"
            >
              ‹
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter((p) => {
                if (totalPages <= 7) return true;
                if (p === 1 || p === totalPages) return true;
                return Math.abs(p - safePage) <= 1;
              })
              .map((p, i, arr) => (
                <React.Fragment key={p}>
                  {i > 0 && arr[i - 1] !== p - 1 && (
                    <span className="px-1 text-gray-400">…</span>
                  )}
                  <button
                    onClick={() => goToPage(p)}
                    className={`px-3 py-1 text-sm border rounded ${
                      p === safePage
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'border-gray-300 hover:bg-gray-100'
                    }`}
                    aria-label={`Page ${p}`}
                    aria-current={p === safePage ? 'page' : undefined}
                  >
                    {p}
                  </button>
                </React.Fragment>
              ))}
            <button
              onClick={() => goToPage(safePage + 1)}
              disabled={safePage === totalPages}
              className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
              aria-label="Next page"
            >
              ›
            </button>
            <button
              onClick={() => goToPage(totalPages)}
              disabled={safePage === totalPages}
              className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
              aria-label="Last page"
            >
              »
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
