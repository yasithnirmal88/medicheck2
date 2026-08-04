import React, { Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import NotFound from '../shared/ui/NotFound'
import LoadingPage from '../shared/loading/LoadingPage'
import { useAuth } from '../hooks/useAuth'

const LoginPage = React.lazy(() => import('../features/auth/pages/Login'))
const ProfilePage = React.lazy(() => import('../features/profile/pages/Profile'))
const Dashboard = React.lazy(() => import('../features/dashboard/pages/Dashboard'))
const QuestionnaireListPage = React.lazy(() => import('../features/questionnaire/pages/QuestionnaireListPage'))
const QuestionnaireSessionPage = React.lazy(() => import('../features/questionnaire/pages/QuestionnaireSessionPage'))
const QuestionnaireHistoryPage = React.lazy(() => import('../features/questionnaire/pages/QuestionnaireHistoryPage'))
const AssessmentSelectionPage = React.lazy(() => import('../features/questionnaire/pages/AssessmentSelectionPage'))
const AdminDashboard = React.lazy(() => import('../features/admin/pages/AdminDashboard'))
const PatientDashboard = React.lazy(() => import('../features/dashboard/pages/PatientDashboard'))
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
const CMSLayout = React.lazy(() => import('../features/cms/layouts/CMSLayout').then(m => ({ default: m.CMSLayout })))
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

const RequireAuth: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { user, loading } = useAuth()
  if (loading) return <LoadingPage />
  if (!user) return <Navigate to="/login" replace />
  return children
}

function LazyPage({ Component }: { Component: React.LazyExoticComponent<React.ComponentType<any>> }) {
  return <Component />
}

export default function Router() {
  return (
    <Suspense fallback={<LoadingPage />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/app/*"
          element={
            <RequireAuth>
              <Dashboard />
            </RequireAuth>
          }
        />
        <Route path="/profile" element={<RequireAuth><HealthProfilePage /></RequireAuth>} />
        <Route path="/profile/wizard" element={<RequireAuth><ProfileWizard /></RequireAuth>} />
        <Route path="/profile/sections" element={<RequireAuth><ProfileSections /></RequireAuth>} />
        <Route path="/profile/versions" element={<RequireAuth><ProfileVersions /></RequireAuth>} />
        <Route path="/" element={<Navigate to="/app" replace />} />
        <Route path="/questionnaires" element={<RequireAuth><QuestionnaireListPage /></RequireAuth>} />
        <Route path="/assessments" element={<RequireAuth><AssessmentSelectionPage /></RequireAuth>} />
        <Route path="/questionnaires/history" element={<RequireAuth><QuestionnaireHistoryPage /></RequireAuth>} />
        <Route path="/questionnaires/:id" element={<RequireAuth><QuestionnaireSessionPage /></RequireAuth>} />
        <Route path="/admin" element={<RequireAuth><AdminDashboard /></RequireAuth>} />
        <Route path="/dashboard" element={<RequireAuth><PatientDashboard /></RequireAuth>} />
        <Route path="/assessments/history" element={<RequireAuth><AssessmentHistory /></RequireAuth>} />
        <Route path="/assessments/dashboard" element={<RequireAuth><AssessmentsPage /></RequireAuth>} />
        <Route path="/assessments/:id/results" element={<RequireAuth><ResultsDashboard /></RequireAuth>} />
        <Route path="/assessments/:id" element={<RequireAuth><ReportViewer /></RequireAuth>} />
        <Route path="/report/:id" element={<RequireAuth><ReportViewer /></RequireAuth>} />
        <Route path="/body-systems" element={<RequireAuth><BodySystemDashboard /></RequireAuth>} />
        <Route path="/recommendations" element={<RequireAuth><RecommendationCenter /></RequireAuth>} />
        <Route path="/timeline" element={<RequireAuth><TimelinePage /></RequireAuth>} />
        <Route path="/timeline/compare" element={<RequireAuth><ComparePage /></RequireAuth>} />

        {/* Doctor CMS & Clinical Validation Suite Routes */}
        <Route
          path="/cms"
          element={
            <RequireAuth>
              <CMSLayout />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/cms/dashboard" replace />} />
          <Route path="dashboard" element={<CMSDashboardPage />} />

          {/* Content list pages */}
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
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}