/**
 * Medicheck Router - Role-Based Access Control
 *
 * Implements complete separation between Patient and Doctor portals.
 * All routes are protected with appropriate role guards.
 *
 * Layout: every authenticated route (patient + doctor/CMS) is a child
 * of a single RootLayout route, so the chrome (sidebar/header) mounts
 * once and never unmounts on normal navigation. RootLayout switches
 * chrome by role internally; the per-route guards below still enforce
 * RBAC on each page. Public/auth routes stay outside the layout.
 */

import React, { Suspense } from 'react'
import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import NotFound from '../shared/ui/NotFound'
import LoadingPage from '../shared/loading/LoadingPage'
import { RequireAuth, RequirePatient, RequireDoctor, GuestRoute } from '../guards'
import { RootLayout } from '../layouts/RootLayout'
import { WizardProvider } from '../features/profile/state/WizardProvider'

// ============================================================================
// Lazy-loaded Patient Components
// ============================================================================
const PatientDashboard = React.lazy(() => import('../features/dashboard/pages/Dashboard'))
const QuestionnaireListPage = React.lazy(() => import('../features/questionnaire/pages/QuestionnaireListPage'))
const QuestionnaireSessionPage = React.lazy(() => import('../features/questionnaire/pages/QuestionnaireSessionPage'))
const QuestionnaireHistoryPage = React.lazy(() => import('../features/questionnaire/pages/QuestionnaireHistoryPage'))
const AssessmentSelectionPage = React.lazy(() => import('../features/questionnaire/pages/AssessmentSelectionPage'))
const IntakePage = React.lazy(() => import('../features/questionnaire/pages/IntakePage'))
const AssessmentHistory = React.lazy(() => import('../features/dashboard/pages/AssessmentHistory'))
const ReportViewer = React.lazy(() => import('../features/dashboard/pages/ReportViewer'))
const ResultsDashboard = React.lazy(() => import('../features/dashboard/pages/ResultsDashboard'))
const BodySystemDashboard = React.lazy(() => import('../features/dashboard/pages/BodySystemDashboard'))
const RecommendationCenter = React.lazy(() => import('../features/dashboard/pages/RecommendationCenter'))
const AssessmentsPage = React.lazy(() => import('../features/dashboard/pages/Assessments'))
const TimelinePage = React.lazy(() => import('../features/health-timeline/pages/TimelinePage'))
const ComparePage = React.lazy(() => import('../features/health-timeline/pages/ComparePage'))
const TrajectoryPage = React.lazy(() => import('../features/health-timeline/pages/TrajectoryPage'))
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

// Phase 6 — Population Health & SDG Analytics
const AnalyticsDashboardPage = React.lazy(() => import('../features/analytics/pages/AnalyticsDashboardPage'))

// Phase 10 — Interoperability, Health-System Integration & Outcome Feedback
const InteroperabilityDashboardPage = React.lazy(() =>
  import('../features/interop/pages/InteroperabilityDashboardPage')
)
const SdgDashboardPage = React.lazy(() => import('../features/interop/pages/SdgDashboardPage'))
const CareContinuityPage = React.lazy(() => import('../features/interop/pages/CareContinuityPage'))
const FacilitiesPage = React.lazy(() => import('../features/interop/pages/FacilitiesPage'))
const ChwQueuePage = React.lazy(() => import('../features/interop/pages/ChwQueuePage'))

// Phase 11 — Governed AI Care Coordination & Equity Intelligence
const ChwSuggestionsPage = React.lazy(() =>
  import('../features/ai-governance/pages/ChwSuggestionsPage')
)
const EquityIntelligencePage = React.lazy(() =>
  import('../features/ai-governance/pages/EquityIntelligencePage')
)
const SdgNarrativesPage = React.lazy(() =>
  import('../features/ai-governance/pages/SdgNarrativesPage')
)

// Content list pages - one lazy component per entity type, wired to its
// dedicated page. Previously a single ContentListPageWrapper (hardcoded to
// QuestionsListPage) was used for every content route, so diseases, symptoms,
// indicators, etc. all rendered the Questions list.
const QuestionsListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.QuestionsListPage })))
const DiseasesListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.DiseasesListPage })))
const BodySystemsListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.BodySystemsListPage })))
const SymptomsListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.SymptomsListPage })))
const IndicatorsListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.IndicatorsListPage })))
const LabTestsListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.LabTestsListPage })))
const ImagingTestsListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.ImagingTestsListPage })))
const RecommendationsListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.RecommendationsListPage })))
const LifestyleAdviceListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.LifestyleAdviceListPage })))
const ExerciseProgramsListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.ExerciseProgramsListPage })))
const NutritionAdviceListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.NutritionAdviceListPage })))
const TemplatesListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.TemplatesListPage })))
const MedicationsListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.MedicationsListPage })))
const ClinicalGuidelinesListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.ClinicalGuidelinesListPage })))
const DecisionRulesListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.DecisionRulesListPage })))
const SeverityThresholdsListPage = React.lazy(() => import('../features/cms/pages/ContentListPages').then(m => ({ default: m.SeverityThresholdsListPage })))

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
        {/* AUTHENTICATED ROUTES - single persistent RootLayout          */}
        {/* (role-based chrome is chosen inside RootLayout; per-route    */}
        {/* guards below still enforce RBAC on each page)                */}
        {/* ============================================================ */}
        <Route
          element={
            <RequireAuth>
              <RootLayout />
            </RequireAuth>
          }
        >
          {/* ------------------------------------------------------------ */}
          {/* PATIENT ROUTES - Patient portal only */}
          {/* ------------------------------------------------------------ */}

          {/* Dashboard with nested routes */}
          <Route
            path="/app"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <PatientDashboard />
              </RequirePatient>
            }
          >
            <Route path="dashboard" element={<Navigate to="/app" replace />} />
          </Route>

          {/* HealthProfilePage renders inside the RootLayout chrome */}
          <Route
            path="/profile"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <WizardProvider>
                  <HealthProfilePage />
                </WizardProvider>
              </RequirePatient>
            }
          />
          <Route
            path="/profile/wizard"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <ProfileWizard />
              </RequirePatient>
            }
          />
          <Route
            path="/profile/sections"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <ProfileSections />
              </RequirePatient>
            }
          />
          <Route
            path="/profile/versions"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <ProfileVersions />
              </RequirePatient>
            }
          />
          <Route
            path="/questionnaires"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <QuestionnaireListPage />
              </RequirePatient>
            }
          />
          <Route
            path="/questionnaires/history"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <QuestionnaireHistoryPage />
              </RequirePatient>
            }
          />
          <Route
            path="/questionnaires/:id"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <QuestionnaireSessionPage />
              </RequirePatient>
            }
          />
          <Route
            path="/assessments"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <AssessmentSelectionPage />
              </RequirePatient>
            }
          />
          <Route
            path="/assessments/intake"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <IntakePage />
              </RequirePatient>
            }
          />
          <Route
            path="/assessments/dashboard"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <AssessmentsPage />
              </RequirePatient>
            }
          />
          <Route
            path="/assessments/history"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <AssessmentHistory />
              </RequirePatient>
            }
          />
          <Route
            path="/assessments/:id"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <ReportViewer />
              </RequirePatient>
            }
          />
          <Route
            path="/assessments/:id/results"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <ResultsDashboard />
              </RequirePatient>
            }
          />
          <Route
            path="/report/:id"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <ReportViewer />
              </RequirePatient>
            }
          />
          <Route
            path="/timeline"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <TimelinePage />
              </RequirePatient>
            }
          />
          <Route
            path="/timeline/compare"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <ComparePage />
              </RequirePatient>
            }
          />
          <Route
            path="/timeline/trajectory"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <TrajectoryPage />
              </RequirePatient>
            }
          />
          <Route
            path="/body-systems"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <BodySystemDashboard />
              </RequirePatient>
            }
          />
          <Route
            path="/recommendations"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <RecommendationCenter />
              </RequirePatient>
            }
          />
          <Route
            path="/settings"
            element={
              <RequirePatient fallbackPath="/cms/dashboard">
                <SettingsPage />
              </RequirePatient>
            }
          />

          {/* ------------------------------------------------------------ */}
          {/* DOCTOR/CMS ROUTES - Clinical staff only */}
          {/* ------------------------------------------------------------ */}
          <Route
            path="/cms"
            element={
              <RequireDoctor fallbackPath="/app">
                <Outlet />
              </RequireDoctor>
            }
          >
            <Route index element={<Navigate to="/cms/dashboard" replace />} />
            <Route path="dashboard" element={<CMSDashboardPage />} />

            {/* Content Management */}
            <Route path="questions" element={<QuestionsListPage />} />
            <Route path="question-groups" element={<Navigate to="/cms/questions" replace />} />
            <Route path="diseases" element={<DiseasesListPage />} />
            <Route path="body-systems" element={<BodySystemsListPage />} />
            <Route path="symptoms" element={<SymptomsListPage />} />
            <Route path="indicators" element={<IndicatorsListPage />} />
            <Route path="lab-tests" element={<LabTestsListPage />} />
            <Route path="imaging" element={<ImagingTestsListPage />} />
            <Route path="recommendations" element={<RecommendationsListPage />} />
            <Route path="lifestyle" element={<LifestyleAdviceListPage />} />
            <Route path="exercise" element={<ExerciseProgramsListPage />} />
            <Route path="nutrition" element={<NutritionAdviceListPage />} />
            <Route path="evidence" element={<ClinicalEvidencePage />} />
            <Route path="templates" element={<TemplatesListPage />} />
            <Route path="medications" element={<MedicationsListPage />} />
            <Route path="guidelines" element={<ClinicalGuidelinesListPage />} />
            <Route path="rules" element={<DecisionRulesListPage />} />
            <Route path="thresholds" element={<SeverityThresholdsListPage />} />

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

            {/* Phase 6 — Population Health & SDG Analytics */}
            <Route path="analytics" element={<AnalyticsDashboardPage />} />

            {/* Phase 10 — Interoperability, Health-System Integration & Outcome Feedback */}
            <Route path="interop" element={<InteroperabilityDashboardPage />} />
            <Route path="interop/sdg" element={<SdgDashboardPage />} />
            <Route path="interop/care-continuity" element={<CareContinuityPage />} />
            <Route path="interop/facilities" element={<FacilitiesPage />} />
            <Route path="interop/chw-queue" element={<ChwQueuePage />} />

            {/* Phase 11 — Governed AI Care Coordination & Equity Intelligence */}
            <Route path="ai-governance/chw-suggestions" element={<ChwSuggestionsPage />} />
            <Route path="ai-governance/equity" element={<EquityIntelligencePage />} />
            <Route path="ai-governance/sdg-narratives" element={<SdgNarrativesPage />} />
          </Route>
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
