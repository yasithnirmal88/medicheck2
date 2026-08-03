import React, { useRef, useState } from 'react'
import type { Question } from '../../types'
import { cn } from '@/lib/utils'

interface FileUploadInputProps {
  question: Question
  value: File | null
  onChange: (value: File | null) => void
  error?: string
  disabled?: boolean
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const FileUploadInput: React.FC<FileUploadInputProps> = ({ question, value, onChange, error, disabled }) => {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)
  const rules = question.validation_rules

  const validate = (file: File): string | null => {
    if (rules?.allowed_types && rules.allowed_types.length > 0) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase()
      if (!rules.allowed_types.some((t) => t.toLowerCase() === ext)) {
        return `Invalid file type. Allowed: ${rules.allowed_types.join(', ')}`
      }
    }
    if (rules?.max_size_mb) {
      const maxBytes = rules.max_size_mb * 1024 * 1024
      if (file.size > maxBytes) {
        return `File too large. Maximum size: ${rules.max_size_mb} MB`
      }
    }
    return null
  }

  const handleFile = (file: File) => {
    if (disabled) return
    const err = validate(file)
    if (err) {
      onChange(null)
      alert(err)
      return
    }
    onChange(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  const remove = () => {
    onChange(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors min-h-[120px] flex flex-col items-center justify-center',
          dragOver
            ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input
          ref={inputRef}
          type="file"
          onChange={handleChange}
          disabled={disabled}
          className="hidden"
          accept={rules?.allowed_types?.join(',')}
          aria-label={question.text}
        />
        {value ? (
          <div className="text-left w-full" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3">
              <svg className="w-8 h-8 text-indigo-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{value.name}</p>
                <p className="text-xs text-gray-500">{formatSize(value.size)}</p>
              </div>
              {!disabled && (
                <button
                  type="button"
                  onClick={remove}
                  className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                  aria-label="Remove file"
                >
                  <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="text-gray-500">
            <svg className="w-10 h-10 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-sm">Drop a file here or click to browse</p>
            {rules?.allowed_types && (
              <p className="text-xs mt-1 text-gray-400">Allowed: {rules.allowed_types.join(', ')}</p>
            )}
            {rules?.max_size_mb && (
              <p className="text-xs text-gray-400">Max size: {rules.max_size_mb} MB</p>
            )}
          </div>
        )}
      </div>
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  )
}

export default React.memo(FileUploadInput)
