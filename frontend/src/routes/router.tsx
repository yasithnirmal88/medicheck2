/**
 * Medicheck Router - Role-Based Access Control
 * 
 * Implements complete separation between Patient and Doctor portals.
 * All routes are protected with appropriate role guards.
 */

import React, { Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import NotFound from '../shared/ui/NotFound'
import LoadingPage from '../shared/loading/LoadingPage'
import { RequireAuth, RequirePatient, RequireDoctor, GuestRoute } from '../guards'
import PatientLayout from '../layouts/PatientLayout'
import DoctorLayout from '../layouts/DoctorLayout'
import { WizardProvider } from '../features/profile/state/WizardProvider'

// ============================================================================
// Lazy-loaded Patient Components
// ============================================================================
const PatientDashboard = React.lazy(() => import('../features/dashboard/pages/Dashboard'))
const QuestionnaireListPage = React.lazy(() => import('../features/questionnaire/pages/QuestionnaireListPage'))
const QuestionnaireSessionPage = React.lazy(() => import('../features/questionnaire/pages/QuestionnaireSessionPage'))
const QuestionnaireHistoryPage = React.lazy(() => import('../features/questionnaire/pages/QuestionnaireHistoryPage'))
const AssessmentSelectionPage = React.lazy(() => import('../features/questionnaire/pages/AssessmentSelectionPage'))
const AssessmentHistory = React.lazy(() => import('../features/dashboard/pages/AssessmentHistory'))
const ReportViewer = React.lazy(() => import('../features/dashboard/pages/ReportViewer'))
const ResultsDashboard = React.lazy(() => import('../features/dashboard/pages/ResultsDashboard'))
const BodySystemDashboard = React.lazy(() => import('../features/dashboard/pages/BodySystemDashboard'))
const RecommendationCenter = React.lazy(() => import('../features/dashboard/pages/RecommendationCenter'))
const AssessmentsPage = React.lazy(() => import('../features/dashboard/pages/Assessments'))
const TimelinePage = React.lazy(() => import('../features/health-timeline/pages/TimelinePage'))
const ComparePage = React.lazy(() => import('../features/health-timeline/pages/ComparePage'))
const ProfileWizard = React.lazy(() => import('../features/profile/pages/ProfileWizard'))
const ProfileSections = React.lazy(() => import('../features/profile/pages/ProfileSections'))
const ProfileVersions = React.lazy(() => import('../features/profile/pages/ProfileVersions'))
const HealthProfilePage = React.lazy(() => import('../features/profile/pages/HealthProfilePage'))

// ============================================================================
// Lazy-loaded Doctor/CMS Components
// ============================================================================
const CMSDashboardPage = React.lazy(() => import('../features/cms/pages/CMSDashboardPage').then(m => ({ default: m.CMSDashboardPage })))
const QuestionnaireBuilderPage = React.lazy(() => import('../features/cms/pages/QuestionnaireBuilderPage').then(m => ({ default: m.QuestionnaireBuilderPage })))
const RuleBuilderPage = React.lazy(() => import('../features/cms/pages/RuleBuilderPage').then(m => ({ default: m.RuleBuilderPage })))
const KnowledgeGraphEditorPage = React.lazy(() => import('../features/cms/pages/KnowledgeGraphEditorPage').then(m => ({ default: m.KnowledgeGraphEditorPage })))
const ApprovalQueuePage = React.lazy(() => import('../features/cms/pages/ApprovalQueuePage').then(m => ({ default: m.ApprovalQueuePage })))
const VersionHistoryPage = React.lazy(() => import('../features/cms/pages/VersionHistoryPage').then(m => ({ default: m.VersionHistoryPage })))
const ClinicalEvidencePage = React.lazy(() => import('../features/cms/pages/ClinicalEvidencePage').then(m => ({ default: m.ClinicalEvidencePage })))
const AuditViewerPage = React.lazy(() => import('../features/cms/pages/AuditViewerPage').then(m => ({ default: m.AuditViewerPage })))
const UsersRolesPage = React.lazy(() => import('../features/cms/pages/UsersRolesPage').then(m => ({ default: m.UsersRolesPage })))
const PublishingWorkflowsPage = React.lazy(() => import('../features/cms/pages/PublishingWorkflowsPage').then(m => ({ default: m.PublishingWorkflowsPage })))
const SearchPage = React.lazy(() => import('../features/cms/pages/SearchPage').then(m => ({ default: m.SearchPage })))
const SettingsPage = React.lazy(() => import('../features/cms/pages/SettingsPage').then(m => ({ default: m.SettingsPage })))

// Content list pages - dynamically loaded based on entity type
const ContentListPageWrapper = React.lazy(() => 
  import('../features/cms/pages/ContentListPages').then(m => ({ default: m.QuestionsListPage }))
)

// ============================================================================
// Auth Components (lazy-loaded)
// ============================================================================
const LoginPage = React.lazy(() => import('../features/auth/pages/Login'))
const RegisterPage = React.lazy(() => import('../features/auth/pages/Register'))
const LandingPage = React.lazy(() => import('../features/auth/pages/LandingPage'))

// ============================================================================
// Main Router
// ============================================================================
export default function Router() {
  return (
    <Suspense fallback={<LoadingPage />}>
      <Routes>
        {/* ============================================================ */}
        {/* PUBLIC ROUTES - No authentication required */}
        {/* ============================================================ */}
        <Route
          path="/"
          element={
            <GuestRoute>
              <LandingPage />
            </GuestRoute>
          }
        />
        <Route
          path="/login"
          element={
            <GuestRoute>
              <LoginPage />
            </GuestRoute>
          }
        />
        <Route
          path="/register"
          element={
            <GuestRoute>
              <RegisterPage />
            </GuestRoute>
          }
        />

        {/* ============================================================ */}
        {/* PATIENT ROUTES - Patient portal only */}
        {/* ============================================================ */}
        
        {/* Dashboard with nested routes */}
        <Route
          path="/app"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayout />
            </RequirePatient>
          }
        >
          <Route index element={<PatientDashboard />} />
          <Route path="dashboard" element={<Navigate to="/app" replace />} />
        </Route>

        {/* Patient-specific routes - each wrapped in PatientLayout */}
        <Route
          path="/profile"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<WizardProvider><HealthProfilePage /></WizardProvider>} />
            </RequirePatient>
          }
        />
        <Route
          path="/profile/wizard"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<ProfileWizard />} />
            </RequirePatient>
          }
        />
        <Route
          path="/profile/sections"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<ProfileSections />} />
            </RequirePatient>
          }
        />
        <Route
          path="/profile/versions"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<ProfileVersions />} />
            </RequirePatient>
          }
        />
        <Route
          path="/questionnaires"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<QuestionnaireListPage />} />
            </RequirePatient>
          }
        />
        <Route
          path="/questionnaires/history"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<QuestionnaireHistoryPage />} />
            </RequirePatient>
          }
        />
        <Route
          path="/questionnaires/:id"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<QuestionnaireSessionPage />} />
            </RequirePatient>
          }
        />
        <Route
          path="/assessments"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<AssessmentSelectionPage />} />
            </RequirePatient>
          }
        />
        <Route
          path="/assessments/dashboard"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<AssessmentsPage />} />
            </RequirePatient>
          }
        />
        <Route
          path="/assessments/history"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<AssessmentHistory />} />
            </RequirePatient>
          }
        />
        <Route
          path="/assessments/:id"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<ReportViewer />} />
            </RequirePatient>
          }
        />
        <Route
          path="/assessments/:id/results"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<ResultsDashboard />} />
            </RequirePatient>
          }
        />
        <Route
          path="/report/:id"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<ReportViewer />} />
            </RequirePatient>
          }
        />
        <Route
          path="/timeline"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<TimelinePage />} />
            </RequirePatient>
          }
        />
        <Route
          path="/timeline/compare"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<ComparePage />} />
            </RequirePatient>
          }
        />
        <Route
          path="/body-systems"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<BodySystemDashboard />} />
            </RequirePatient>
          }
        />
        <Route
          path="/recommendations"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<RecommendationCenter />} />
            </RequirePatient>
          }
        />
        <Route
          path="/settings"
          element={
            <RequirePatient fallbackPath="/cms/dashboard">
              <PatientLayoutWithContent content={<SettingsPage />} />
            </RequirePatient>
          }
        />

        {/* ============================================================ */}
        {/* DOCTOR/CMS ROUTES - Clinical staff only */}
        {/* ============================================================ */}
        <Route
          path="/cms"
          element={
            <RequireDoctor fallbackPath="/app">
              <DoctorLayout />
            </RequireDoctor>
          }
        >
          <Route index element={<Navigate to="/cms/dashboard" replace />} />
          <Route path="dashboard" element={<CMSDashboardPage />} />

          {/* Content Management */}
          <Route path="questions" element={<ContentListPageWrapper />} />
          <Route path="question-groups" element={<Navigate to="/cms/questions" replace />} />
          <Route path="diseases" element={<ContentListPageWrapper />} />
          <Route path="body-systems" element={<ContentListPageWrapper />} />
          <Route path="symptoms" element={<ContentListPageWrapper />} />
          <Route path="indicators" element={<ContentListPageWrapper />} />
          <Route path="lab-tests" element={<ContentListPageWrapper />} />
          <Route path="imaging" element={<ContentListPageWrapper />} />
          <Route path="recommendations" element={<ContentListPageWrapper />} />
          <Route path="lifestyle" element={<ContentListPageWrapper />} />
          <Route path="exercise" element={<ContentListPageWrapper />} />
          <Route path="nutrition" element={<ContentListPageWrapper />} />
          <Route path="evidence" element={<ClinicalEvidencePage />} />
          <Route path="templates" element={<ContentListPageWrapper />} />
          <Route path="medications" element={<ContentListPageWrapper />} />
          <Route path="guidelines" element={<ContentListPageWrapper />} />
          <Route path="rules" element={<ContentListPageWrapper />} />
          <Route path="thresholds" element={<ContentListPageWrapper />} />

          {/* Builders */}
          <Route path="builder" element={<QuestionnaireBuilderPage />} />
          <Route path="rules-builder" element={<RuleBuilderPage />} />
          <Route path="graph" element={<KnowledgeGraphEditorPage />} />

          {/* Workflow */}
          <Route path="publishing" element={<PublishingWorkflowsPage />} />
          <Route path="approvals" element={<ApprovalQueuePage />} />
          <Route path="history" element={<VersionHistoryPage />} />

          {/* Operations */}
          <Route path="audit" element={<AuditViewerPage />} />
          <Route path="users" element={<UsersRolesPage />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        {/* ============================================================ */}
        {/* UNAUTHORIZED */}
        {/* ============================================================ */}
        <Route
          path="/unauthorized"
          element={
            <div className="flex min-h-screen items-center justify-center">
              <div className="text-center">
                <h1 className="text-4xl font-bold text-red-600">Access Denied</h1>
                <p className="mt-2 text-gray-600">You do not have permission to access this page.</p>
                <a href="/app" className="mt-4 inline-block text-blue-600 hover:underline">
                  Go to Dashboard
                </a>
              </div>
            </div>
          }
        />

        {/* ============================================================ */}
        {/* 404 */}
        {/* ============================================================ */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}

// ============================================================================
// Layout Wrapper Components
// ============================================================================

// Wrapper for PatientLayout with content
const PatientLayoutWithContent: React.FC<{ content: React.ReactNode }> = ({ content }) => (
  <PatientLayout>{content}</PatientLayout>
)