import React from 'react'
import { Link } from 'react-router-dom'
import AppLayout from '@/layouts/AppLayout'
import Card from '@/shared/ui/Card'

const ProfilePage: React.FC = () => {
  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto p-4 space-y-4">
        <Card>
          <h1 className="text-2xl">Your Health Profile</h1>
          <p className="mt-2 text-sm text-gray-600">Manage and update your digital health profile. Changes auto-save as you go.</p>
          <div className="mt-4">
            <Link to="/profile/wizard" className="text-indigo-600">Open Profile Wizard</Link>
          </div>
        </Card>

        <Card>
          <h2 className="text-lg">Profile completion</h2>
          <p className="mt-2">A summary of how complete your profile is. (Placeholder — progress computed in the wizard.)</p>
        </Card>

        <Card>
          <h2 className="text-lg">Recent activity</h2>
          <p className="mt-2">No recent activity to show.</p>
        </Card>
      </div>
    </AppLayout>
  )
}

export default ProfilePage
