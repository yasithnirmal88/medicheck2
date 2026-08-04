import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchTemplates,
  fetchTemplate,
  startSession,
  fetchSession,
  saveAnswer,
  pauseSession,
  resumeSession,
  completeSession,
  fetchProgress,
  fetchSessions,
  fetchQuestions,
  searchQuestions,
} from '../api/questionnaireApi'
import type { SaveAnswerRequest, QuestionFilters } from '../types'

export const useTemplates = () =>
  useQuery({
    queryKey: ['questionnaire-templates'],
    queryFn: fetchTemplates,
    staleTime: 1000 * 60 * 5,
  })

export const useTemplate = (id: string | undefined) =>
  useQuery({
    queryKey: ['questionnaire-template', id],
    queryFn: () => fetchTemplate(id!),
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
  })

export const useStartSession = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (templateId: string) => startSession(templateId),
    onSuccess: (data) => {
      qc.setQueryData(['session', data.id], data)
      qc.invalidateQueries({ queryKey: ['sessions'] })
    },
  })
}

export const useSession = (sessionId: string | undefined) =>
  useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => fetchSession(sessionId!),
    enabled: !!sessionId,
    refetchInterval: (query) => {
      const data = query.state.data
      if (data && (data.status === 'in_progress' || data.status === 'paused')) return 5000
      return false
    },
  })

export const useSaveAnswer = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ sessionId, data }: { sessionId: string; data: SaveAnswerRequest }) =>
      saveAnswer(sessionId, data),
    onMutate: async ({ sessionId, data: _data }) => {
      await qc.cancelQueries({ queryKey: ['session', sessionId] })
      const previous = qc.getQueryData(['session', sessionId])
      return { previous }
    },
    onError: (_err, { sessionId }, context) => {
      if (context?.previous) {
        qc.setQueryData(['session', sessionId], context.previous)
      }
    },
    onSettled: (_data, _err, { sessionId }) => {
      qc.invalidateQueries({ queryKey: ['session', sessionId] })
      qc.invalidateQueries({ queryKey: ['progress', sessionId] })
    },
  })
}

export const usePauseSession = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) => pauseSession(sessionId),
    onSuccess: (data) => {
      qc.setQueryData(['session', data.id], data)
      qc.invalidateQueries({ queryKey: ['sessions'] })
    },
  })
}

export const useResumeSession = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) => resumeSession(sessionId),
    onSuccess: (data) => {
      qc.setQueryData(['session', data.id], data)
      qc.invalidateQueries({ queryKey: ['sessions'] })
    },
  })
}

export const useCompleteSession = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sessionId: string) => completeSession(sessionId),
    onSuccess: (data) => {
      qc.setQueryData(['session', data.id], data)
      qc.invalidateQueries({ queryKey: ['sessions'] })
    },
  })
}

export const useProgress = (sessionId: string | undefined) =>
  useQuery({
    queryKey: ['progress', sessionId],
    queryFn: () => fetchProgress(sessionId!),
    enabled: !!sessionId,
    refetchInterval: 10000,
  })

export const useSessions = () =>
  useQuery({
    queryKey: ['sessions'],
    queryFn: fetchSessions,
    staleTime: 1000 * 60,
  })

export const useQuestions = (params?: QuestionFilters) =>
  useQuery({
    queryKey: ['questions', params],
    queryFn: () => fetchQuestions(params),
    staleTime: 1000 * 60 * 5,
  })

export const useSearchQuestions = () =>
  useMutation({
    mutationFn: (query: string) => searchQuestions(query),
  })
