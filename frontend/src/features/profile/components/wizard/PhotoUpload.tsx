import React from 'react'
import { useDropzone } from 'react-dropzone'
import { Camera, X } from 'lucide-react'

interface PhotoUploadProps {
  value: string
  onChange: (value: string) => void
}

export const PhotoUpload: React.FC<PhotoUploadProps> = ({ value, onChange }) => {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'image/*': [] },
    maxFiles: 1,
    maxSize: 5 * 1024 * 1024,
    onDrop: (acceptedFiles) => {
      const file = acceptedFiles[0]
      if (!file) return
      const reader = new FileReader()
      reader.onloadend = () => onChange(reader.result as string)
      reader.readAsDataURL(file)
    },
  })

  return (
    <div
      {...getRootProps()}
      className={`relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition-colors ${
        isDragActive
          ? 'border-blue-500 bg-blue-50/50 dark:border-blue-400 dark:bg-blue-500/10'
          : 'border-slate-300 bg-slate-50/50 dark:border-slate-600 dark:bg-slate-800/50'
      }`}
    >
      <input {...getInputProps()} />
      {value ? (
        <div className="relative">
          <img src={value} alt="Profile preview" className="h-24 w-24 rounded-full object-cover" />
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onChange('')
            }}
            className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-red-500 text-white shadow-sm hover:bg-red-600"
            aria-label="Remove photo"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      ) : (
        <>
          <Camera className="mb-2 h-8 w-8 text-slate-400" />
          <p className="text-sm font-medium text-slate-600 dark:text-slate-300">
            {isDragActive ? 'Drop the photo here' : 'Drag & drop a photo, or click to browse'}
          </p>
          <p className="mt-1 text-xs text-slate-400">PNG, JPG up to 5MB</p>
        </>
      )}
    </div>
  )
}