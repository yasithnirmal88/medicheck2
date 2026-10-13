/**
 * Phase 11 — TanStack Query hooks for governed AI care coordination.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  generateOperationalSuggestions,
  fetchOperationalSuggestions,
  generateEquityInsight,
  fetchEquityInsights,
  generateSdgNarratives,
  fetchSdgNarratives,
  reviewOperationalSuggestion,
  publishOperationalSuggestion,
  reviewPopulationInsight,
  publishPopulationInsight,
  type EquityInsightParams,
  type ReviewRequest,
} from '../api/aiGovernanceService'

export const aiGovKeys = {
  operationalSuggestions: () => ['ai-gov', 'operational'] as const,
  equityInsight: (params?: EquityInsightParams) =>
    ['ai-gov', 'equity', params ?? {}] as const,
  equityInsights: () => ['ai-gov', 'equity', 'list'] as const,
  sdgNarratives: (params?: EquityInsightParams) =>
    ['ai-gov', 'sdg-narratives', params ?? {}] as const,
  sdgNarrativeList: () => ['ai-gov', 'sdg-narratives', 'list'] as const,
}

export const useOperationalSuggestions = () =>
  useQuery({
    queryKey: aiGovKeys.operationalSuggestions(),
    queryFn: fetchOperationalSuggestions,
  })

export const useGenerateOperationalSuggestions = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: generateOperationalSuggestions,
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: aiGovKeys.operationalSuggestions() }),
  })
}

export const useEquityInsight = (params?: EquityInsightParams) =>
  useQuery({
    queryKey: aiGovKeys.equityInsight(params),
    queryFn: () => generateEquityInsight(params),
  })

export const useEquityInsights = () =>
  useQuery({ queryKey: aiGovKeys.equityInsights(), queryFn: fetchEquityInsights })

export const useSdgNarratives = (params?: EquityInsightParams) =>
  useQuery({
    queryKey: aiGovKeys.sdgNarratives(params),
    queryFn: () => generateSdgNarratives(params),
  })

export const useSdgNarrativeList = () =>
  useQuery({ queryKey: aiGovKeys.sdgNarrativeList(), queryFn: fetchSdgNarratives })

export const useReviewOperationalSuggestion = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      suggestionId,
      req,
    }: {
      suggestionId: string
      req: ReviewRequest
    }) => reviewOperationalSuggestion(suggestionId, req),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: aiGovKeys.operationalSuggestions() }),
  })
}

export const usePublishOperationalSuggestion = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: publishOperationalSuggestion,
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: aiGovKeys.operationalSuggestions() }),
  })
}

export const useReviewPopulationInsight = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      insightId,
      req,
    }: {
      insightId: string
      req: ReviewRequest
    }) => reviewPopulationInsight(insightId, req),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ai-gov'] })
    },
  })
}

export const usePublishPopulationInsight = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: publishPopulationInsight,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ai-gov'] }),
  })
}
