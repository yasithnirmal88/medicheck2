import React, { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { saveNutrition } from '../api/extendedService'
import debounce from 'lodash/debounce'

const defaults = {
  meals_per_day: '',
  fruit_intake_per_day: '',
  vegetable_intake_per_day: '',
  fast_food_frequency: '',
  sugary_drinks_frequency: '',
  salt_intake: '',
  fish_frequency: '',
  red_meat_frequency: '',
  processed_meat_frequency: '',
  coffee_cups_per_day: '',
  tea_cups_per_day: '',
  energy_drinks_per_day: '',
  special_diet: '',
  food_allergies: '',
}

export default function NutritionForm({ initial }: { initial?: any }) {
  const form = useForm({ defaultValues: initial ?? defaults })
  const qc = useQueryClient()
  const mutation = useMutation({
    mutationFn: (p: Record<string, unknown>) => saveNutrition(p),
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
        <label className="block text-sm">Meals per day</label>
        <input className="mt-1 block w-full" {...form.register('meals_per_day')} />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm">Fruit intake</label>
          <input className="mt-1 block w-full" {...form.register('fruit_intake_per_day')} />
        </div>
        <div>
          <label className="block text-sm">Vegetable intake</label>
          <input className="mt-1 block w-full" {...form.register('vegetable_intake_per_day')} />
        </div>
      </div>
      <div className="flex justify-end">
        <button className="px-3 py-1 bg-indigo-600 text-white rounded">Save</button>
      </div>
    </form>
  )
}
