import React from 'react'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'
import LifestyleForm from '../components/LifestyleForm'
import NutritionForm from '../components/NutritionForm'
import { useProfile } from '../hooks/useProfile'

export default function ProfileSections() {
  const { data: profile } = useProfile()

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto p-4 space-y-4">
        <Card>
          <h1 className="text-2xl">Profile Sections</h1>
          <p className="mt-2 text-sm">Edit different sections of your health profile. Changes autosave.</p>
        </Card>

        <Card>
          <h2 className="text-lg">Personal Information</h2>
          <p className="text-sm">Use the Profile Wizard to edit personal info.</p>
        </Card>

        <Card>
          <h2 className="text-lg">Lifestyle</h2>
          <LifestyleForm initial={profile?.personal_info ?? undefined} />
        </Card>

        <Card>
          <h2 className="text-lg">Nutrition</h2>
          <NutritionForm initial={profile?.nutrition ?? undefined} />
        </Card>

        <Card>
          <h2 className="text-lg">Medical History</h2>
          <p className="text-sm">Add conditions, medications, surgeries, family history, allergies, immunizations, measurements and lab reports.</p>
        </Card>
      </div>
    </AppLayout>
  )
}
