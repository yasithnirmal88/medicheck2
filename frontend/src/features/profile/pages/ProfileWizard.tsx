import React, { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useProfile } from '../hooks/useProfile'
import { PersonalInfo } from '../types/profile'
import debounce from 'lodash/debounce'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'
import Button from '@/shared/ui/Button'

const PersonalInfoSchema = z.object({
  full_name: z.string().min(1),
  date_of_birth: z.string().optional().nullable(),
  sex: z.string().optional().nullable(),
  height_cm: z.preprocess((v) => (v === '' ? undefined : Number(v)), z.number().optional().nullable()),
  weight_kg: z.preprocess((v) => (v === '' ? undefined : Number(v)), z.number().optional().nullable()),
  blood_group: z.string().optional().nullable(),
})

export default function ProfileWizard() {
  const { data: profile } = useProfile()
  const { savePersonal } = useProfile()

  const form = useForm<PersonalInfo>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(PersonalInfoSchema) as any,
    defaultValues: profile?.personal_info ?? { full_name: '' },
  })

  // sync updated profile into form when loaded
  useEffect(() => {
    if (profile?.personal_info) form.reset(profile.personal_info)
  }, [profile])

  // autosave on changes (debounced)
  useEffect(() => {
    const handler = debounce((values: any) => {
      savePersonal.mutate(values)
    }, 800)

    const subscription = form.watch((value) => {
      handler(value as any)
    })

    return () => subscription.unsubscribe()
  }, [form, savePersonal])

  const onSubmit = form.handleSubmit((values) => {
    savePersonal.mutate(values)
  })

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto p-4">
        <h1 className="text-2xl mb-4">Profile Wizard</h1>
        <Card>
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="block text-sm">Full name</label>
              <input className="mt-1 block w-full" {...form.register('full_name')} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm">Date of Birth</label>
                <input type="date" className="mt-1 block w-full" {...form.register('date_of_birth')} />
              </div>
              <div>
                <label className="block text-sm">Sex</label>
                <select className="mt-1 block w-full" {...form.register('sex')}>
                  <option value="">Select</option>
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm">Height (cm)</label>
                <input className="mt-1 block w-full" {...form.register('height_cm')} />
              </div>
              <div>
                <label className="block text-sm">Weight (kg)</label>
                <input className="mt-1 block w-full" {...form.register('weight_kg')} />
              </div>
            </div>

            <div>
              <label className="block text-sm">Blood group</label>
              <input className="mt-1 block w-full" {...form.register('blood_group')} />
            </div>

            <div className="flex justify-end">
              <Button type="submit">Save</Button>
            </div>
          </form>
        </Card>
      </div>
    </AppLayout>
  )
}
