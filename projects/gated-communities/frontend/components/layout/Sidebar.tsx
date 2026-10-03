'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export interface SidebarItem {
  label: string;
  href: string;
  icon?: React.ReactNode;
  badge?: string | number;
  children?: SidebarItem[];
}

export interface SidebarProps {
  items: SidebarItem[];
  title?: string;
  logo?: React.ReactNode;
  collapsed?: boolean;
  onToggle?: () => void;
  className?: string;
  footer?: React.ReactNode;
}

const Sidebar: React.FC<SidebarProps> = ({
  items,
  title = 'Gated Communities',
  logo,
  collapsed = false,
  onToggle,
  className = '',
  footer,
}) => {
  const pathname = usePathname();
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  const toggleExpand = (label: string) => {
    setExpandedItems((prev) => {
      const next = new Set(prev);
      if (next.has(label)) {
        next.delete(label);
      } else {
        next.add(label);
      }
      return next;
    });
  };

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + '/');

  const renderItem = (item: SidebarItem, depth = 0) => {
    const active = isActive(item.href);
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.has(item.label);

    return (
      <li key={item.label}>
        <div
          className={`
            flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors
            ${active ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}
            ${collapsed ? 'justify-center' : ''}
          `}
          style={{ paddingLeft: collapsed ? undefined : 12 + depth * 16 }}
          onClick={() => hasChildren && toggleExpand(item.label)}
        >
          {item.icon && <span className="flex-shrink-0">{item.icon}</span>}
          {!collapsed && (
            <>
              <span className="flex-1 text-sm font-medium truncate">{item.label}</span>
              {item.badge && (
                <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
                  {item.badge}
                </span>
              )}
              {hasChildren && (
                <svg
                  className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              )}
            </>
          )}
        </div>
        {hasChildren && isExpanded && !collapsed && (
          <ul className="mt-1 space-y-0.5">
            {item.children!.map((child) => renderItem(child, depth + 1))}
          </ul>
        )}
      </li>
    );
  };

  return (
    <aside
      className={`
        flex flex-col h-screen bg-white border-r border-gray-200 transition-all duration-200
        ${collapsed ? 'w-16' : 'w-64'} ${className}
      `}
    >
      {/* Header */}
      <div className={`flex items-center h-16 px-4 border-b border-gray-200 ${collapsed ? 'justify-center' : ''}`}>
        {logo && <div className="flex-shrink-0">{logo}</div>}
        {!collapsed && <span className="ml-3 text-lg font-semibold text-gray-900 truncate">{title}</span>}
        {onToggle && (
          <button
            onClick={onToggle}
            className={`ml-auto p-1.5 rounded-lg hover:bg-gray-100 transition-colors ${collapsed ? 'mx-auto' : ''}`}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d={collapsed ? 'M13 5l7 7-7 7' : 'M11 19l-7-7 7-7'}
              />
            </svg>
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-3">
        <ul className="space-y-1">{items.map((item) => renderItem(item))}</ul>
      </nav>

      {/* Footer */}
      {footer && !collapsed && <div className="p-4 border-t border-gray-200">{footer}</div>}
    </aside>
  );
};

export default Sidebar;
