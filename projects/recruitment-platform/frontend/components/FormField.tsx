'use client';

import React, { useCallback } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  min?: number;
  max?: number;
  pattern?: RegExp;
  patternMessage?: string;
  email?: boolean;
  url?: boolean;
  custom?: (value: string) => string | null;
}

export interface FormFieldProps {
  label: string;
  name: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'textarea' | 'select';
  value: string;
  onChange: (name: string, value: string) => void;
  onBlur?: (name: string) => void;
  placeholder?: string;
  error?: string;
  touched?: boolean;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  validation?: ValidationRule;
  options?: { value: string; label: string }[];
  rows?: number;
  helpText?: string;
  className?: string;
  labelClassName?: string;
  inputClassName?: string;
  autoComplete?: string;
  autoFocus?: boolean;
}

// ─── Validation helpers ──────────────────────────────────────────────────────

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const URL_REGEX = /^https?:\/\/.+\..+/;

function validateField(value: string, rules?: ValidationRule): string | null {
  if (!rules) return null;

  if (rules.required && !value.trim()) {
    return 'This field is required';
  }

  if (!value.trim()) return null;

  if (rules.minLength && value.length < rules.minLength) {
    return `Must be at least ${rules.minLength} characters`;
  }

  if (rules.maxLength && value.length > rules.maxLength) {
    return `Must be at most ${rules.maxLength} characters`;
  }

  if (rules.min !== undefined && Number(value) < rules.min) {
    return `Must be at least ${rules.min}`;
  }

  if (rules.max !== undefined && Number(value) > rules.max) {
    return `Must be at most ${rules.max}`;
  }

  if (rules.email && !EMAIL_REGEX.test(value)) {
    return 'Please enter a valid email address';
  }

  if (rules.url && !URL_REGEX.test(value)) {
    return 'Please enter a valid URL';
  }

  if (rules.pattern && !rules.pattern.test(value)) {
    return rules.patternMessage || 'Invalid format';
  }

  if (rules.custom) {
    return rules.custom(value);
  }

  return null;
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function FormField({
  label,
  name,
  type = 'text',
  value,
  onChange,
  onBlur,
  placeholder,
  error: externalError,
  touched: externalTouched,
  disabled = false,
  readOnly = false,
  required = false,
  validation,
  options = [],
  rows = 4,
  helpText,
  className = '',
  labelClassName = '',
  inputClassName = '',
  autoComplete,
  autoFocus = false,
}: FormFieldProps) {
  // ── Internal validation state ─────────────────────────────────────────────

  const [internalError, setInternalError] = React.useState<string | null>(null);
  const [internalTouched, setInternalTouched] = React.useState(false);

  const showError = (externalTouched ?? internalTouched) && (externalError ?? internalError);

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const newValue = e.target.value;
      onChange(name, newValue);

      // Live validation if already touched
      if (internalTouched || externalTouched) {
        const validationError = validateField(newValue, validation);
        setInternalError(validationError);
      }
    },
    [name, onChange, internalTouched, externalTouched, validation]
  );

  const handleBlur = useCallback(
    (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      setInternalTouched(true);
      const validationError = validateField(e.target.value, validation);
      setInternalError(validationError);
      onBlur?.(name);
    },
    [name, onBlur, validation]
  );

  // ── Shared input classes ──────────────────────────────────────────────────

  const baseInputClasses = `
    w-full px-3 py-2 border rounded-lg text-sm
    transition-colors duration-150
    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
    disabled:bg-gray-100 disabled:cursor-not-allowed
    ${showError ? 'border-red-500 focus:ring-red-500' : 'border-gray-300'}
  `;

  // ── Render input by type ──────────────────────────────────────────────────

  const renderInput = () => {
    const inputProps = {
      id: name,
      name,
      value,
      onChange: handleChange,
      onBlur: handleBlur,
      placeholder,
      disabled,
      readOnly,
      required: required || validation?.required,
      autoComplete,
      autoFocus,
      'aria-invalid': !!showError,
      'aria-describedby': showError ? `${name}-error` : helpText ? `${name}-help` : undefined,
    };

    switch (type) {
      case 'textarea':
        return (
          <textarea
            {...inputProps}
            rows={rows}
            className={`${baseInputClasses} resize-y ${inputClassName}`}
          />
        );

      case 'select':
        return (
          <select
            {...inputProps}
            className={`${baseInputClasses} ${inputClassName}`}
          >
            <option value="">{placeholder || 'Select an option'}</option>
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        );

      default:
        return (
          <input
            {...inputProps}
            type={type}
            className={`${baseInputClasses} ${inputClassName}`}
          />
        );
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      {/* Label */}
      <label
        htmlFor={name}
        className={`text-sm font-medium text-gray-700 ${labelClassName}`}
      >
        {label}
        {(required || validation?.required) && (
          <span className="text-red-500 ml-0.5" aria-hidden="true">
            *
          </span>
        )}
      </label>

      {/* Input */}
      {renderInput()}

      {/* Help text */}
      {helpText && !showError && (
        <p id={`${name}-help`} className="text-xs text-gray-500">
          {helpText}
        </p>
      )}

      {/* Error message */}
      {showError && (
        <p
          id={`${name}-error`}
          className="text-xs text-red-600 flex items-center gap-1"
          role="alert"
        >
          <svg
            className="w-3.5 h-3.5 flex-shrink-0"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
          {externalError ?? internalError}
        </p>
      )}
    </div>
  );
}
