import React, { useMemo, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Info, AlertTriangle } from 'lucide-react'
import { useWizard } from '../state/WizardProvider'
import { DashboardLayout } from '../../../layouts/DashboardLayout'
import { Stepper } from '../components/wizard/Stepper'
import { SectionForm } from '../components/wizard/SectionForm'
import { RepeatableSection } from '../components/wizard/RepeatableSection'
import { PhotoUpload } from '../components/wizard/PhotoUpload'
import { MedicationCard } from '../components/wizard/MedicationCard'
import { AllergyCard } from '../components/wizard/AllergyCard'
import { VaccinationSection } from '../components/wizard/VaccinationSection'
import { WomenHealthSection } from '../components/wizard/WomenHealthSection'
import { MenHealthSection } from '../components/wizard/MenHealthSection'
import { DiseaseCardGrid } from '../components/wizard/DiseaseCardGrid'
import { ExpandableFamilyCard } from '../components/wizard/ExpandableFamilyCard'
import { ReviewSubmitPage } from '../components/wizard/ReviewSubmitPage'
import { HealthTips } from '../components/wizard/HealthTips'
import { ProfileErrorBoundary } from '../components/ProfileErrorBoundary'
import { ProfileSkeleton } from '../components/ProfileSkeleton'
import { AutoSaveIndicator } from '../components/AutoSaveIndicator'
import { ProfileCompletion } from '../components/ProfileCompletion'
import { AIReadinessScore } from '../components/AIReadinessScore'
import { useAutoSave } from '../hooks/useAutoSave'
import { useUnsavedChanges } from '../hooks/useUnsavedChanges'
import { useProfileCompletion } from '../hooks/useProfileCompletion'
import { useAIReadiness } from '../hooks/useAIReadiness'
import { useHealthTips } from '../hooks/useHealthTips'
import { useToast } from '../hooks/useToast'
import { useValidation } from '../hooks/useValidation'
import type { WizardState, SectionKey } from '../types/wizard'
import { fieldSpecs } from '../wizard/fieldSpecs'
import { sectionSchemas } from '../wizard/schemas'

const STEP_LABELS: { key: SectionKey; label: string; icon: string }[] = [
  { key: 'personal', label: 'Personal', icon: 'User' },
  { key: 'body', label: 'Body', icon: 'Activity' },
  { key: 'lifestyle', label: 'Lifestyle', icon: 'Heart' },
  { key: 'nutrition', label: 'Nutrition', icon: 'Apple' },
  { key: 'physical_activity', label: 'Activity', icon: 'Dumbbell' },
  { key: 'sleep', label: 'Sleep', icon: 'Moon' },
  { key: 'mental_health', label: 'Mental', icon: 'Brain' },
  { key: 'conditions', label: 'Conditions', icon: 'AlertCircle' },
  { key: 'surgeries', label: 'Surgeries', icon: 'Scissors' },
  { key: 'family_history', label: 'Family', icon: 'Users' },
  { key: 'medications', label: 'Meds', icon: 'Pill' },
  { key: 'allergies', label: 'Allergies', icon: 'Shield' },
  { key: 'vaccinations', label: 'Vaccines', icon: 'Syringe' },
  { key: 'women_health', label: "Women's", icon: 'Venus' },
  { key: 'men_health', label: "Men's", icon: 'Mars' },
  { key: 'lifestyle_risks', label: 'Risks', icon: 'AlertTriangle' },
  { key: 'environment', label: 'Environment', icon: 'Globe' },
  { key: 'occupation', label: 'Work', icon: 'Briefcase' },
  { key: 'travel', label: 'Travel', icon: 'Plane' },
  { key: 'emergency', label: 'Emergency', icon: 'Phone' },
  { key: 'consents', label: 'Review', icon: 'CheckCircle' },
]

const VISIBLE_STEPS = (state: WizardState) => {
  const gender = state.personal.gender
  return STEP_LABELS.filter((s) => {
    if (s.key === 'women_health' && gender !== 'female') return false
    if (s.key === 'men_health' && gender !== 'male') return false
    return true
  })
}

function renderSection(
  step: { key: SectionKey; label: string },
  state: WizardState,
  setSection: (key: SectionKey, value: unknown) => void,
) {
  const key = step.key

  if (key === 'consents') {
    return (
      <ReviewSubmitPage
        state={state}
        setSection={setSection}
        onSubmit={() => {
          console.log('Profile submitted:', state)
        }}
      />
    )
  }

  const specs = fieldSpecs[key]

  if (key === 'personal') {
    return (
      <div className="space-y-6">
        <SectionForm sectionKey={key} data={state.personal} onChange={(v) => setSection('personal', v)} />
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">Profile Photo</h3>
          <PhotoUpload value={state.personal.photo ?? ''} onChange={(v) => setSection('personal', { ...state.personal, photo: v })} />
        </div>
      </div>
    )
  }

  const repeatableKeys: SectionKey[] = ['conditions', 'surgeries', 'family_history', 'medications', 'allergies', 'vaccinations']
  if (repeatableKeys.includes(key)) {
    const itemMap = {
      conditions: {
        newItem: { id: crypto.randomUUID(), conditions: [], diagnosis_date: '', severity: '', status: '', notes: '', surgeries_count: '', hospital_admissions: '', previous_fractures: '', organ_transplants: '' },
        renderItem: (item: unknown, index: number, onUpdate: (item: unknown) => void, onRemove: () => void) => {
          const entry = item as WizardState['conditions'][number]
          return (
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1.5">Conditions</label>
                <DiseaseCardGrid
                  selected={entry.conditions}
                  onChange={(diseases: string[]) => onUpdate({ ...entry, conditions: diseases })}
                />
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <input placeholder="Diagnosis date" value={entry.diagnosis_date ?? ''} onChange={(e) => onUpdate({ ...entry, diagnosis_date: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
                <input placeholder="Severity" value={entry.severity ?? ''} onChange={(e) => onUpdate({ ...entry, severity: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <input placeholder="Status" value={entry.status ?? ''} onChange={(e) => onUpdate({ ...entry, status: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
                <input placeholder="Notes" value={entry.notes ?? ''} onChange={(e) => onUpdate({ ...entry, notes: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <input placeholder="Surgeries count" value={entry.surgeries_count ?? ''} onChange={(e) => onUpdate({ ...entry, surgeries_count: e.target.value })} type="number" min={0} max={50} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
                <input placeholder="Hospital admissions" value={entry.hospital_admissions ?? ''} onChange={(e) => onUpdate({ ...entry, hospital_admissions: e.target.value })} type="number" min={0} max={50} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
                <input placeholder="Previous fractures" value={entry.previous_fractures ?? ''} onChange={(e) => onUpdate({ ...entry, previous_fractures: e.target.value })} type="number" min={0} max={20} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
                <input placeholder="Organ transplants" value={entry.organ_transplants ?? ''} onChange={(e) => onUpdate({ ...entry, organ_transplants: e.target.value })} type="number" min={0} max={10} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
              </div>
            </div>
          )
        },
      },
      surgeries: {
        newItem: { id: crypto.randomUUID(), procedure: '', date: '', hospital: '', reason: '', outcome: '' },
        renderItem: (item: unknown, index: number, onUpdate: (item: unknown) => void, onRemove: () => void) => {
          const entry = item as WizardState['surgeries'][number]
          return (
            <div className="space-y-3">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <input placeholder="Procedure" value={entry.procedure} onChange={(e) => onUpdate({ ...entry, procedure: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
                <input placeholder="Date" value={entry.date ?? ''} onChange={(e) => onUpdate({ ...entry, date: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
                <input placeholder="Hospital" value={entry.hospital ?? ''} onChange={(e) => onUpdate({ ...entry, hospital: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
                <input placeholder="Reason" value={entry.reason ?? ''} onChange={(e) => onUpdate({ ...entry, reason: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
              </div>
              <input placeholder="Outcome" value={entry.outcome ?? ''} onChange={(e) => onUpdate({ ...entry, outcome: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
            </div>
          )
        },
      },
      family_history: {
        newItem: { id: crypto.randomUUID(), relative: '', diseases: [], age_at_diagnosis: '', current_status: '', notes: '' },
        renderItem: (item: unknown, index: number, onUpdate: (item: unknown) => void, onRemove: () => void) => {
          const entry = item as WizardState['family_history'][number]
          return (
            <ExpandableFamilyCard
              relative={entry.relative}
              diseases={entry.diseases}
              onDiseasesChange={(diseases: string[]) => onUpdate({ ...entry, diseases })}
              ageAtDiagnosis={entry.age_at_diagnosis ?? ''}
              onAgeAtDiagnosisChange={(v: string) => onUpdate({ ...entry, age_at_diagnosis: v })}
              currentStatus={entry.current_status ?? ''}
              onCurrentStatusChange={(v: string) => onUpdate({ ...entry, current_status: v })}
              notes={entry.notes ?? ''}
              onNotesChange={(v: string) => onUpdate({ ...entry, notes: v })}
            />
          )
        },
      },
      medications: {
        newItem: { id: crypto.randomUUID(), medication: '', dosage: '', frequency: '', reason: '', start_date: '', prescribing_doctor: '', current_status: '' },
        renderItem: (item: unknown, index: number, onUpdate: (item: unknown) => void, onRemove: () => void) => {
          const entry = item as WizardState['medications'][number]
          return (
            <MedicationCard
              medication={entry.medication}
              dosage={entry.dosage ?? ''}
              frequency={entry.frequency ?? ''}
              reason={entry.reason ?? ''}
              startDate={entry.start_date ?? ''}
              prescribingDoctor={entry.prescribing_doctor ?? ''}
              currentStatus={entry.current_status ?? ''}
              onUpdate={(field: string, value: string) => onUpdate({ ...entry, [field]: value })}
              onRemove={onRemove}
            />
          )
        },
      },
      allergies: {
        newItem: { id: crypto.randomUUID(), type: '', substance: '', severity: '', reaction: '', emergency_medication: '' },
        renderItem: (item: unknown, index: number, onUpdate: (item: unknown) => void, onRemove: () => void) => {
          const entry = item as WizardState['allergies'][number]
          return (
            <AllergyCard
              type={entry.type}
              substance={entry.substance}
              severity={entry.severity ?? ''}
              reaction={entry.reaction ?? ''}
              emergencyMedication={entry.emergency_medication ?? ''}
              onUpdate={(field: string, value: string) => onUpdate({ ...entry, [field]: value })}
              onRemove={onRemove}
            />
          )
        },
      },
      vaccinations: {
        newItem: { id: crypto.randomUUID(), vaccine: '', dose: '', date: '', provider: '' },
        renderItem: (item: unknown, index: number, onUpdate: (item: unknown) => void, onRemove: () => void) => {
          const entry = item as WizardState['vaccinations'][number]
          return (
            <div className="space-y-3">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <input placeholder="Vaccine" value={entry.vaccine} onChange={(e) => onUpdate({ ...entry, vaccine: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
                <input placeholder="Dose" value={entry.dose ?? ''} onChange={(e) => onUpdate({ ...entry, dose: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
                <input placeholder="Date" value={entry.date ?? ''} onChange={(e) => onUpdate({ ...entry, date: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
                <input placeholder="Provider" value={entry.provider ?? ''} onChange={(e) => onUpdate({ ...entry, provider: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200" />
              </div>
            </div>
          )
        },
      },
    }

    const config = itemMap[key as keyof typeof itemMap]

    const sectionContent = (
      <RepeatableSection
        title={step.label}
        items={state[key] as unknown[]}
        onChange={(v) => setSection(key, v)}
        newItem={config.newItem}
        renderItem={config.renderItem}
        emptyLabel="No entries yet"
        addLabel={`Add ${step.label.slice(0, -1)}`}
      />
    )

    if (key === 'conditions') {
      return (
        <div className="space-y-6">
          {sectionContent}
          <HealthTips medicalHistory={state.conditions} />
        </div>
      )
    }

    if (key === 'family_history') {
      return (
        <div className="space-y-6">
          {sectionContent}
          <HealthTips familyHistory={state.family_history} />
        </div>
      )
    }

    if (key === 'medications') {
      return (
        <div className="space-y-6">
          <RepeatableSection
            title={step.label}
            items={state.medications}
            onChange={(v) => setSection('medications', v)}
            newItem={config.newItem}
            renderItem={(item: unknown, index: number, onUpdate: (item: unknown) => void, onRemove: () => void) => {
              const entry = item as WizardState['medications'][number]
              return (
                <MedicationCard
                  medication={entry.medication}
                  dosage={entry.dosage ?? ''}
                  frequency={entry.frequency ?? ''}
                  reason={entry.reason ?? ''}
                  startDate={entry.start_date ?? ''}
                  prescribingDoctor={entry.prescribing_doctor ?? ''}
                  currentStatus={entry.current_status ?? ''}
                  onUpdate={(field: string, value: string) => onUpdate({ ...entry, [field]: value })}
                  onRemove={onRemove}
                />
              )
            }}
            emptyLabel="No medications yet"
            addLabel="Add Medication"
          />
          <HealthTips medicalHistory={state.medications} />
        </div>
      )
    }

    if (key === 'allergies') {
      return (
        <div className="space-y-6">
          <RepeatableSection
            title={step.label}
            items={state.allergies}
            onChange={(v) => setSection('allergies', v)}
            newItem={config.newItem}
            renderItem={(item: unknown, index: number, onUpdate: (item: unknown) => void, onRemove: () => void) => {
              const entry = item as WizardState['allergies'][number]
              return (
                <AllergyCard
                  type={entry.type}
                  substance={entry.substance}
                  severity={entry.severity ?? ''}
                  reaction={entry.reaction ?? ''}
                  emergencyMedication={entry.emergency_medication ?? ''}
                  onUpdate={(field: string, value: string) => onUpdate({ ...entry, [field]: value })}
                  onRemove={onRemove}
                />
              )
            }}
            emptyLabel="No allergies listed"
            addLabel="Add Allergy"
          />
        </div>
      )
    }

    if (key === 'vaccinations') {
      return (
        <div className="space-y-6">
          <VaccinationSection
            items={state.vaccinations}
            onChange={(v) => setSection('vaccinations', v)}
          />
        </div>
      )
    }

    return sectionContent
  }

  if (key === 'lifestyle') {
    return (
      <div className="space-y-6">
        <SectionForm sectionKey={key} data={state.lifestyle} onChange={(v) => setSection('lifestyle', v)} />
        <HealthTips lifestyle={state.lifestyle} nutrition={state.nutrition} />
      </div>
    )
  }

  if (key === 'nutrition') {
    return (
      <div className="space-y-6">
        <SectionForm sectionKey={key} data={state.nutrition} onChange={(v) => setSection('nutrition', v)} />
        <HealthTips lifestyle={state.lifestyle} nutrition={state.nutrition} />
      </div>
    )
  }

  if (key === 'physical_activity') {
    return (
      <div className="space-y-6">
        <SectionForm sectionKey={key} data={state.physical_activity} onChange={(v) => setSection('physical_activity', v)} />
        <HealthTips lifestyle={state.lifestyle} />
      </div>
    )
  }

  if (key === 'sleep') {
    return (
      <div className="space-y-6">
        <SectionForm sectionKey={key} data={state.sleep} onChange={(v) => setSection('sleep', v)} />
        <HealthTips lifestyle={state.lifestyle} />
      </div>
    )
  }

  if (key === 'mental_health') {
    return (
      <div className="space-y-6">
        <SectionForm sectionKey={key} data={state.mental_health} onChange={(v) => setSection('mental_health', v)} />
        <HealthTips lifestyle={state.lifestyle} />
      </div>
    )
  }

  if (key === 'lifestyle_risks') {
    return (
      <div className="space-y-6">
        <SectionForm sectionKey={key} data={state.lifestyle_risks} onChange={(v) => setSection('lifestyle_risks', v)} />
        <HealthTips lifestyle={state.lifestyle} lifestyleRisks={state.lifestyle_risks} />
      </div>
    )
  }

  if (key === 'environment') {
    return (
      <div className="space-y-6">
        <SectionForm sectionKey={key} data={state.environment} onChange={(v) => setSection('environment', v)} />
        <HealthTips environment={state.environment} />
      </div>
    )
  }

  if (key === 'occupation') {
    return (
      <div className="space-y-6">
        <SectionForm sectionKey={key} data={state.occupation} onChange={(v) => setSection('occupation', v)} />
        <HealthTips occupation={state.occupation} />
      </div>
    )
  }

  if (key === 'travel') {
    return (
      <div className="space-y-6">
        <SectionForm sectionKey={key} data={state.travel} onChange={(v) => setSection('travel', v)} />
        <HealthTips travel={state.travel} />
      </div>
    )
  }

  return <SectionForm sectionKey={key} data={state[key]} onChange={(v) => setSection(key, v)} />
}

export default function HealthProfilePage() {
  const { state, setSection, isHydrated, saveDraft, hasUnsavedChanges, autoSaveStatus, lastSavedAt } = useWizard()
  const [currentStep, setCurrentStep] = React.useState(0)
  const [showCompletion, setShowCompletion] = useState(false)
  const [showAIReadiness, setShowAIReadiness] = useState(false)
  const { success, error, info } = useToast()
  const { validateSection } = useValidation()
  const completion = useProfileCompletion(state)
  const aiReadiness = useAIReadiness(state)
  const healthTips = useHealthTips(state)
  useAutoSave(true)
  useUnsavedChanges(hasUnsavedChanges)

  const steps = useMemo(() => VISIBLE_STEPS(state), [state])

  const currentKey = steps[currentStep]?.key ?? 'personal'

  const handleSave = () => {
    saveDraft()
    success('Draft saved successfully')
  }

  const handleSubmit = async () => {
    const validation = validateSection('consents', state.consents)
    if (!validation.isValid) {
      error('Please review and accept the terms and conditions')
      return
    }
    try {
      const response = await fetch('/api/profiles/me', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state),
      })
      if (!response.ok) throw new Error('Failed to submit')
      success('Profile submitted successfully!')
    } catch {
      error('Failed to submit profile. Please try again.')
    }
  }

  if (!isHydrated) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="mx-auto max-w-4xl">
        <div className="mb-4 flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Health Profile</h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Complete your health profile — your data is saved automatically</p>
          </div>
          <div className="flex items-center gap-3">
            <AutoSaveIndicator status={autoSaveStatus} lastSaved={lastSavedAt ?? undefined} />
            <button
              type="button"
              onClick={() => setShowCompletion(!showCompletion)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
              aria-expanded={showCompletion}
              aria-controls="completion-panel"
            >
              {showCompletion ? 'Hide' : 'Show'} Completion
            </button>
            <button
              type="button"
              onClick={() => setShowAIReadiness(!showAIReadiness)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
              aria-expanded={showAIReadiness}
              aria-controls="ai-readiness-panel"
            >
              {showAIReadiness ? 'Hide' : 'Show'} AI Readiness
            </button>
          </div>
        </div>

        <AnimatePresence>
          {showCompletion && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              id="completion-panel"
              className="mb-4 overflow-hidden"
            >
              <ProfileCompletion state={state as WizardState} onSectionClick={(key) => {
                const idx = steps.findIndex((s) => s.key === key)
                if (idx >= 0) setCurrentStep(idx)
              }} />
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {showAIReadiness && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              id="ai-readiness-panel"
              className="mb-4 overflow-hidden"
            >
              <AIReadinessScore state={state} />
            </motion.div>
          )}
        </AnimatePresence>

        {healthTips.length > 0 && (
          <div className="mb-4 rounded-xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-800/50 dark:bg-blue-900/20">
            <h3 className="mb-2 text-sm font-semibold text-blue-800 dark:text-blue-200 flex items-center gap-2">
              <Info className="h-4 w-4" /> Health Insights
            </h3>
            <ul className="space-y-1">
              {healthTips.slice(0, 5).map((tip, i) => (
                <li key={i} className="text-xs text-blue-700 dark:text-blue-300 flex items-start gap-2">
                  <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-blue-500" />
                  {tip.text}
                </li>
              ))}
            </ul>
          </div>
        )}

        <Stepper steps={steps} currentStep={currentStep} onStepClick={setCurrentStep} />

        <ProfileErrorBoundary>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
            {renderSection(steps[currentStep], state, setSection)}
          </div>
        </ProfileErrorBoundary>

        {currentKey !== 'consents' && (
          <div className="mt-6 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setCurrentStep((prev) => Math.max(0, prev - 1))}
              disabled={currentStep === 0}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-40 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              Previous
            </button>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleSave}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                Save Draft
              </button>
              {currentStep === steps.length - 1 ? (
                <button
                  type="button"
                  onClick={handleSubmit}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                >
                  Submit Profile
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setCurrentStep((prev) => Math.min(steps.length - 1, prev + 1))}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                >
                  Next
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}