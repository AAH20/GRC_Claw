import React, { useState, useMemo, useCallback } from 'react';

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
  searchable?: boolean;
  searchPlaceholder?: string;
  searchKeys?: (keyof T)[];
  pageSize?: number;
  pageSizeOptions?: number[];
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
  className?: string;
  striped?: boolean;
  bordered?: boolean;
  hoverable?: boolean;
}

export function DataTable<T extends Record<string, unknown>>({
  data,
  columns,
  searchable = true,
  searchPlaceholder = 'Search...',
  searchKeys = [],
  pageSize = 10,
  pageSizeOptions = [5, 10, 25, 50],
  onRowClick,
  emptyMessage = 'No data available',
  className = '',
  striped = true,
  bordered = true,
  hoverable = true,
}: DataTableProps<T>) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [filterText, setFilterText] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(pageSize);

  const filteredData = useMemo(() => {
    if (!filterText || searchKeys.length === 0) return data;
    const lowerFilter = filterText.toLowerCase();
    return data.filter((row) =>
      searchKeys.some((key) => {
        const value = row[key];
        if (value == null) return false;
        return String(value).toLowerCase().includes(lowerFilter);
      })
    );
  }, [data, filterText, searchKeys]);

  const sortedData = useMemo(() => {
    if (!sortColumn) return filteredData;
    const column = columns.find((c) => c.key === sortColumn);
    if (!column) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aVal = column.accessor(a);
      const bVal = column.accessor(b);
      const aStr = String(aVal ?? '');
      const bStr = String(bVal ?? '');
      const comparison = aStr.localeCompare(bStr, undefined, { numeric: true });
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [filteredData, sortColumn, sortDirection, columns]);

  const totalPages = Math.max(1, Math.ceil(sortedData.length / rowsPerPage));
  const safePage = Math.min(currentPage, totalPages);
  const paginatedData = useMemo(() => {
    const start = (safePage - 1) * rowsPerPage;
    return sortedData.slice(start, start + rowsPerPage);
  }, [sortedData, safePage, rowsPerPage]);

  const handleSort = useCallback(
    (columnKey: string) => {
      if (sortColumn === columnKey) {
        setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
      } else {
        setSortColumn(columnKey);
        setSortDirection('asc');
      }
    },
    [sortColumn]
  );

  const handleFilterChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFilterText(e.target.value);
    setCurrentPage(1);
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  }, [totalPages]);

  const handleRowsPerPageChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setRowsPerPage(Number(e.target.value));
    setCurrentPage(1);
  }, []);

  const getSortIcon = (columnKey: string) => {
    if (sortColumn !== columnKey) return '↕';
    return sortDirection === 'asc' ? '↑' : '↓';
  };

  const alignmentClass = (align?: 'left' | 'center' | 'right') => {
    switch (align) {
      case 'center': return 'text-center';
      case 'right': return 'text-right';
      default: return 'text-left';
    }
  };

  return (
    <div className={`w-full ${className}`}>
      {searchable && (
        <div className="mb-4">
          <input
            type="text"
            value={filterText}
            onChange={handleFilterChange}
            placeholder={searchPlaceholder}
            className="w-full max-w-sm px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            aria-label="Search table"
          />
        </div>
      )}

      <div className="overflow-x-auto">
        <table className={`min-w-full divide-y divide-gray-200 ${bordered ? 'border border-gray-200' : ''}`}>
          <thead className="bg-gray-50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  scope="col"
                  className={`px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider ${alignmentClass(column.align)} ${
                    column.sortable !== false ? 'cursor-pointer select-none hover:bg-gray-100' : ''
                  }`}
                  style={column.width ? { width: column.width } : undefined}
                  onClick={column.sortable !== false ? () => handleSort(column.key) : undefined}
                >
                  <span className="inline-flex items-center gap-1">
                    {column.header}
                    {column.sortable !== false && (
                      <span className="text-gray-400 text-xs">{getSortIcon(column.key)}</span>
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className={`bg-white ${striped ? 'divide-y divide-gray-100' : 'divide-y divide-gray-200'}`}>
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-gray-500 text-sm">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  className={`${hoverable ? 'hover:bg-gray-50' : ''} ${onRowClick ? 'cursor-pointer' : ''}`}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={`px-4 py-3 text-sm text-gray-700 ${alignmentClass(column.align)}`}
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

      <div className="mt-4 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>Rows per page:</span>
          <select
            value={rowsPerPage}
            onChange={handleRowsPerPageChange}
            className="border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Rows per page"
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
          <span className="ml-2">
            Showing {sortedData.length === 0 ? 0 : (safePage - 1) * rowsPerPage + 1}–{' '}
            {Math.min(safePage * rowsPerPage, sortedData.length)} of {sortedData.length}
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => handlePageChange(1)}
            disabled={safePage === 1}
            className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label="First page"
          >
            «
          </button>
          <button
            onClick={() => handlePageChange(safePage - 1)}
            disabled={safePage === 1}
            className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label="Previous page"
          >
            ‹
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter((page) => page === 1 || page === totalPages || Math.abs(page - safePage) <= 2)
            .reduce<(number | '...')[]>((acc, page, idx, arr) => {
              if (idx > 0 && page - (arr[idx - 1] as number) > 1) acc.push('...');
              acc.push(page);
              return acc;
            }, [])
            .map((page, idx) =>
              page === '...' ? (
                <span key={`ellipsis-${idx}`} className="px-2 text-gray-400">
                  …
                </span>
              ) : (
                <button
                  key={page}
                  onClick={() => handlePageChange(page)}
                  className={`px-3 py-1 text-sm border rounded ${
                    page === safePage
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'border-gray-300 hover:bg-gray-100'
                  }`}
                >
                  {page}
                </button>
              )
            )}
          <button
            onClick={() => handlePageChange(safePage + 1)}
            disabled={safePage === totalPages}
            className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label="Next page"
          >
            ›
          </button>
          <button
            onClick={() => handlePageChange(totalPages)}
            disabled={safePage === totalPages}
            className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label="Last page"
          >
            »
          </button>
        </div>
      </div>
    </div>
  );
}

export default DataTable;
