import React, { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { saveLifestyle } from '../api/extendedService'
import debounce from 'lodash/debounce'

const defaultValues = {
  smoking: '',
  alcohol: '',
  water_intake_l_per_day: '',
  exercise_frequency: '',
  exercise_type: '',
  daily_walking_minutes: '',
  avg_daily_steps: '',
  transportation_method: '',
  occupation: '',
  working_hours: '',
  working_style: '',
  sitting_hours: '',
  sleep_duration_hours: '',
  sleep_quality: '',
  stress_level: '',
  physical_activity_level: '',
}

interface LifestyleFormProps {
  initial?: typeof defaultValues
}

export default function LifestyleForm({ initial }: LifestyleFormProps) {
  const form = useForm({ defaultValues: initial ?? defaultValues })
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: (p: Record<string, unknown>) => saveLifestyle(p),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['profile'] }),
  })

  useEffect(() => {
    if (initial) form.reset(initial)
  }, [initial])

  useEffect(() => {
    const handler = debounce((v) => mutation.mutate(v), 800)
    const sub = form.watch((val) => handler(val))
    return () => sub.unsubscribe()
  }, [form, mutation])

  return (
    <form className="space-y-3">
      <div>
        <label className="block text-sm">Smoking</label>
        <input className="mt-1 block w-full" {...form.register('smoking')} />
      </div>
      <div>
        <label className="block text-sm">Alcohol</label>
        <input className="mt-1 block w-full" {...form.register('alcohol')} />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm">Water intake (L/day)</label>
          <input className="mt-1 block w-full" {...form.register('water_intake_l_per_day')} />
        </div>
        <div>
          <label className="block text-sm">Exercise frequency</label>
          <input className="mt-1 block w-full" {...form.register('exercise_frequency')} />
        </div>
      </div>
      <div className="flex justify-end">
        <button className="px-3 py-1 bg-indigo-600 text-white rounded">Save</button>
      </div>
    </form>
  )
}
