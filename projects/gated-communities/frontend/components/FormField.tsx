import React, { useId, useState, useCallback } from 'react';

export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  patternMessage?: string;
  min?: number;
  max?: number;
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
  touched?: boolean;
  validation?: ValidationRule;
  options?: { value: string; label: string }[];
  rows?: number;
  helpText?: string;
  className?: string;
  labelClassName?: string;
  inputClassName?: string;
  required?: boolean;
  autoComplete?: string;
  icon?: React.ReactNode;
}

export function FormField({
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
  touched: externalTouched,
  validation = {},
  options = [],
  rows = 4,
  helpText,
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
  const helpId = `${id}-help`;
  const [internalError, setInternalError] = useState<string | null>(null);
  const [internalTouched, setInternalTouched] = useState(false);

  const validate = useCallback(
    (val: string): string | null => {
      if (validation.required && !val.trim()) {
        return `${label} is required`;
      }
      if (!val.trim()) return null;
      if (validation.minLength && val.length < validation.minLength) {
        return `${label} must be at least ${validation.minLength} characters`;
      }
      if (validation.maxLength && val.length > validation.maxLength) {
        return `${label} must be at most ${validation.maxLength} characters`;
      }
      if (validation.pattern && !validation.pattern.test(val)) {
        return validation.patternMessage || `${label} format is invalid`;
      }
      if (type === 'number' || validation.min !== undefined || validation.max !== undefined) {
        const num = Number(val);
        if (isNaN(num)) return `${label} must be a valid number`;
        if (validation.min !== undefined && num < validation.min) {
          return `${label} must be at least ${validation.min}`;
        }
        if (validation.max !== undefined && num > validation.max) {
          return `${label} must be at most ${validation.max}`;
        }
      }
      if (validation.custom) {
        return validation.custom(val);
      }
      return null;
    },
    [validation, label, type]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const newValue = e.target.value;
      onChange(name, newValue);
      if (internalTouched) {
        setInternalError(validate(newValue));
      }
    },
    [name, onChange, internalTouched, validate]
  );

  const handleBlur = useCallback(
    (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      setInternalTouched(true);
      const validationError = validate(e.target.value);
      setInternalError(validationError);
      onBlur?.(name, e.target.value);
    },
    [name, onBlur, validate]
  );

  const showError = (externalTouched || internalTouched) && (externalError || internalError);
  const errorMessage = externalError || internalError;

  const baseInputClasses =
    'w-full px-3 py-2 border rounded-md shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors';
  const stateClasses = showError
    ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
    : 'border-gray-300 hover:border-gray-400';
  const disabledClasses = disabled || readOnly ? 'bg-gray-100 cursor-not-allowed text-gray-500' : 'bg-white';

  const inputClasses = `${baseInputClasses} ${stateClasses} ${disabledClasses} ${inputClassName}`;

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
      'aria-invalid': showError ? 'true' : undefined,
      'aria-describedby': showError ? errorId : helpText ? helpId : undefined,
      className: inputClasses,
    };

    switch (type) {
      case 'textarea':
        return <textarea {...inputProps} rows={rows} />;
      case 'select':
        return (
          <select {...inputProps}>
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
      default:
        return <input {...inputProps} type={type} />;
    }
  };

  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      <label htmlFor={id} className={`text-sm font-medium text-gray-700 ${labelClassName}`}>
        {label}
        {required && (
          <span className="ml-1 text-red-500" aria-hidden="true">
            *
          </span>
        )}
      </label>

      {icon && (
        <div className="relative">
          <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400 pointer-events-none">
            {icon}
          </span>
          <div className="pl-10">{renderInput()}</div>
        </div>
      )}

      {!icon && renderInput()}

      {helpText && !showError && (
        <p id={helpId} className="text-xs text-gray-500">
          {helpText}
        </p>
      )}

      {showError && errorMessage && (
        <p id={errorId} className="text-xs text-red-600 flex items-center gap-1" role="alert">
          <svg className="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
          {errorMessage}
        </p>
      )}
    </div>
  );
}

export default FormField;
