import React from 'react'

interface SectionHeaderProps {
  groupName: string | null
  groupDescription: string | null
  questionIndex: number
  totalQuestions: number
}

const SectionHeader: React.FC<SectionHeaderProps> = ({ groupName, groupDescription, questionIndex, totalQuestions }) => {
  return (
    <div className="mb-6">
      {groupName && (
        <div className="inline-block px-3 py-1 rounded-full bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 text-xs font-medium mb-2">
          {groupName}
        </div>
      )}
      <p className="text-xs text-gray-400">
        Question {questionIndex + 1} of {totalQuestions}
      </p>
      {groupDescription && (
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{groupDescription}</p>
      )}
    </div>
  )
}

export default SectionHeader
