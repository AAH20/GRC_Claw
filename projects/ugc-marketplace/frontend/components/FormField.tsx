'use client';

import React, { useState, useCallback, useId } from 'react';

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
  onBlur?: (name: string, value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  readOnly?: boolean;
  error?: string;
  hint?: string;
  validation?: ValidationRule;
  options?: { value: string; label: string }[];
  rows?: number;
  className?: string;
  labelClassName?: string;
  inputClassName?: string;
  required?: boolean;
  autoComplete?: string;
  icon?: React.ReactNode;
}

// ─── Validation helpers ──────────────────────────────────────────────────────

function validateValue(value: string, rules: ValidationRule): string | null {
  const trimmed = value.trim();

  if (rules.required && !trimmed) {
    return 'This field is required';
  }

  if (!trimmed) return null;

  if (rules.minLength != null && trimmed.length < rules.minLength) {
    return `Must be at least ${rules.minLength} characters`;
  }

  if (rules.maxLength != null && trimmed.length > rules.maxLength) {
    return `Must be at most ${rules.maxLength} characters`;
  }

  if (rules.min != null && Number(trimmed) < rules.min) {
    return `Must be at least ${rules.min}`;
  }

  if (rules.max != null && Number(trimmed) > rules.max) {
    return `Must be at most ${rules.max}`;
  }

  if (rules.email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmed)) {
      return 'Please enter a valid email address';
    }
  }

  if (rules.url) {
    try {
      new URL(trimmed);
    } catch {
      return 'Please enter a valid URL';
    }
  }

  if (rules.pattern && !rules.pattern.test(trimmed)) {
    return rules.patternMessage || 'Invalid format';
  }

  if (rules.custom) {
    const customError = rules.custom(trimmed);
    if (customError) return customError;
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
  disabled = false,
  readOnly = false,
  error: externalError,
  hint,
  validation = {},
  options = [],
  rows = 4,
  className = '',
  labelClassName = '',
  inputClassName = '',
  required = false,
  autoComplete,
  icon,
}: FormFieldProps) {
  const generatedId = useId();
  const id = `field-${name}-${generatedId}`;
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;

  const [internalError, setInternalError] = useState<string | null>(null);
  const [touched, setTouched] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const displayError = externalError || (touched ? internalError : null);
  const isRequired = required || validation.required || false;

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const newValue = e.target.value;
      onChange(name, newValue);

      if (touched) {
        const validationError = validateValue(newValue, validation);
        setInternalError(validationError);
      }
    },
    [name, onChange, touched, validation]
  );

  const handleBlur = useCallback(
    (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      setTouched(true);
      const validationError = validateValue(e.target.value, validation);
      setInternalError(validationError);
      onBlur?.(name, e.target.value);
    },
    [name, onBlur, validation]
  );

  // ── Shared input classes ──────────────────────────────────────────────────

  const baseInputClasses = `
    w-full px-3 py-2 border rounded-lg text-sm
    transition-colors duration-150
    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
    disabled:bg-gray-100 disabled:cursor-not-allowed disabled:text-gray-500
    ${displayError ? 'border-red-400 bg-red-50' : 'border-gray-300 bg-white'}
    ${icon ? 'pl-10' : ''}
  `;

  // ── Render input by type ──────────────────────────────────────────────────

  const renderInput = () => {
    const inputProps = {
      id,
      name,
      value,
      onChange: handleChange,
      onBlur: handleBlur,
      placeholder,
      disabled,
      readOnly,
      autoComplete,
      'aria-invalid': displayError ? true : undefined,
      'aria-describedby': displayError ? errorId : hint ? hintId : undefined,
      'aria-required': isRequired || undefined,
    };

    switch (type) {
      case 'textarea':
        return (
          <textarea
            {...inputProps}
            rows={rows}
            className={`${baseInputClasses} resize-y min-h-[80px] ${inputClassName}`}
          />
        );

      case 'select':
        return (
          <select
            {...inputProps}
            className={`${baseInputClasses} cursor-pointer ${inputClassName}`}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        );

      case 'password':
        return (
          <div className="relative">
            <input
              {...inputProps}
              type={showPassword ? 'text' : 'password'}
              className={`${baseInputClasses} pr-10 ${inputClassName}`}
            />
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              tabIndex={-1}
            >
              {showPassword ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              )}
            </button>
          </div>
        );

      default:
        return (
          <div className="relative">
            {icon && (
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
                {icon}
              </span>
            )}
            <input
              {...inputProps}
              type={type}
              className={`${baseInputClasses} ${inputClassName}`}
            />
          </div>
        );
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      {/* Label */}
      <label
        htmlFor={id}
        className={`text-sm font-medium text-gray-700 ${labelClassName}`}
      >
        {label}
        {isRequired && (
          <span className="ml-0.5 text-red-500" aria-hidden="true">
            *
          </span>
        )}
      </label>

      {/* Input */}
      {renderInput()}

      {/* Error message */}
      {displayError && (
        <p
          id={errorId}
          className="text-xs text-red-600 flex items-center gap-1"
          role="alert"
        >
          <svg className="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
          {displayError}
        </p>
      )}

      {/* Hint text */}
      {hint && !displayError && (
        <p id={hintId} className="text-xs text-gray-500">
          {hint}
        </p>
      )}
    </div>
  );
}
