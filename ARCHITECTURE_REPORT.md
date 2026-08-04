# Medicheck Frontend Architecture Audit Report

**Date:** 2026-08-04  
**Author:** Principal Software Architect  
**Project:** Medicheck Healthcare Platform  

---

## Executive Summary

The Medicheck frontend has **CRITICAL security vulnerabilities** that allow unauthorized access to protected areas. A patient can access Doctor CMS pages, and the application lacks proper role-based access control (RBAC).

**Security Rating: 🔴 CRITICAL**

---

## Part 1: Current Problems

### 1.1 No Role-Based Access Control (RBAC)

**Issue:** The `RequireAuth` wrapper only checks if a user is logged in - NOT their role.

```tsx
// Current router.tsx - INSECURE
const RequireAuth: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { user, loading } = useAuth()
  if (loading) return <LoadingPage />
  if (!user) return <Navigate to="/login" replace />
  return children  // ❌ No role check!
}
```

**Impact:** Any authenticated user can access ANY route.

### 1.2 Patient Sidebar Contains CMS Link

**File:** `src/features/dashboard/components/layout/navConfig.ts`

```tsx
export const secondaryNav: NavItem[] = [
  { label: 'Knowledge Center', to: '/cms', icon: BookOpen },  // ❌ Patients can navigate to CMS!
  // ...
]
```

**Impact:** Patients can navigate to CMS routes through the sidebar.

### 1.3 No Route Guards for CMS

**Issue:** CMS routes are only wrapped with `RequireAuth`, not role verification.

```tsx
// Current - Anyone authenticated can access CMS
<Route
  path="/cms"
  element={
    <RequireAuth>
      <CMSLayout />
    </RequireAuth>
  }
>
```

**Impact:** Patients can access all CMS functionality by typing `/cms/*` URLs.

### 1.4 AuthProvider Lacks Role Information

**Issue:** `AuthProvider` only tracks `user`, not role.

```tsx
type AuthContextType = {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  // ❌ Missing: role, role loading, etc.
}
```

**Impact:** No way to determine user permissions in components.

### 1.5 No Role-Aware Login/Register

**Issue:** Login page always redirects to `/app` regardless of role.

```tsx
// Login.tsx
const onEmailSubmit = async (values: LoginFormValues) => {
  await login.mutateAsync(values)
  navigate('/app')  // ❌ Should redirect based on role!
}
```

### 1.6 Shared Dashboard Layout

**Issue:** Patient and Doctor use the same layout with same navigation structure.

**Impact:** Hard to maintain separation, easy to accidentally expose features.

### 1.7 No Lazy Loading Separation

**Issue:** CMS pages are imported but not properly code-split by role.

**Impact:** CMS code may be included in patient bundle (needs verification).

---

## Part 2: Security Risks

| Risk | Severity | Description |
|------|----------|-------------|
| Patient accessing CMS | 🔴 CRITICAL | Can view/edit medical content |
| Patient accessing Doctor routes | 🔴 CRITICAL | Can access `/cms/*` |
| Role stored only in backend | 🟠 HIGH | Frontend trusts backend, no local verification |
| No route-level authorization | 🔴 CRITICAL | UI hiding doesn't prevent URL access |
| Shared layouts | 🟡 MEDIUM | Easy to accidentally expose features |

---

## Part 3: Architecture Improvements

### Recommended Architecture

```
Landing Page
    │
    ▼
Account Type Selection
────────────────────────
│ Patient │ Doctor │
────────────────────────
    │
    ▼
Login / Register
(Form knows the selected type)
    │
    ├──────────────────┐
    ▼                  ▼
PATIENT              DOCTOR
┌─────────┐    ┌──────────────┐
│ Patient │    │ Doctor CMS  │
│ App     │    │ Portal      │
│ Layout  │    │ Layout      │
└─────────┘    └──────────────┘
```

### New Folder Structure

```
src/
├── modules/
│   ├── patient/          # Patient-only features
│   │   ├── pages/
│   │   ├── components/
│   │   └── hooks/
│   ├── doctor/           # Doctor-only features
│   │   ├── pages/
│   │   ├── components/
│   │   └── hooks/
│   └── auth/             # Shared auth (login/register/landing)
├── contexts/
│   ├── AuthContext.tsx    # Enhanced with role
│   └── RoleContext.tsx    # Role state management
├── routes/
│   ├── patientRoutes.tsx  # Patient-only routes
│   ├── doctorRoutes.tsx   # Doctor-only routes
│   └── authRoutes.tsx     # Public routes
├── layouts/
│   ├── PatientLayout.tsx  # Patient navigation
│   ├── DoctorLayout.tsx   # Doctor CMS navigation
│   └── AuthLayout.tsx     # Login/Register layout
├── guards/
│   ├── RequireAuth.tsx    # Authentication check
│   ├── RequireRole.tsx    # Role-based access
│   └── RequirePatient.tsx # Patient-only guard
└── types/
    └── role.ts            # Role definitions
```

---

## Part 4: Files to Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/providers/AuthProvider.tsx` | MODIFY | Add role state, fetch from API |
| `src/contexts/RoleContext.tsx` | CREATE | Role state management |
| `src/types/role.ts` | CREATE | Role type definitions |
| `src/guards/RequireAuth.tsx` | CREATE | Enhanced auth guard |
| `src/guards/RequireRole.tsx` | CREATE | Role-based route guard |
| `src/routes/patientRoutes.tsx` | CREATE | Patient-only routes |
| `src/routes/doctorRoutes.tsx` | CREATE | Doctor-only routes |
| `src/routes/router.tsx` | MODIFY | Use new route system |
| `src/layouts/PatientLayout.tsx` | CREATE | Patient layout |
| `src/layouts/DoctorLayout.tsx` | CREATE | Doctor CMS layout |
| `src/features/auth/pages/LandingPage.tsx` | CREATE | Account type selection |
| `src/features/auth/pages/Login.tsx` | MODIFY | Role-aware login |
| `src/features/auth/pages/Register.tsx` | CREATE | Role-aware registration |
| `src/features/dashboard/components/layout/navConfig.ts` | MODIFY | Remove CMS link |
| `src/features/dashboard/components/layout/Sidebar.tsx` | MODIFY | Patient-only nav |

---

## Part 5: Route Map

### Patient Routes (PATIENT role only)

| Route | Component | Description |
|-------|-----------|-------------|
| `/app` | Dashboard | Patient dashboard |
| `/profile` | HealthProfilePage | Health profile |
| `/profile/wizard` | ProfileWizard | Profile setup |
| `/questionnaires` | QuestionnaireListPage | Available questionnaires |
| `/questionnaires/:id` | QuestionnaireSessionPage | Active questionnaire |
| `/questionnaires/history` | QuestionnaireHistoryPage | Past sessions |
| `/assessments` | AssessmentSelectionPage | Assessment selection |
| `/assessments/dashboard` | AssessmentsPage | Assessment overview |
| `/assessments/:id` | ReportViewer | Assessment report |
| `/assessments/:id/results` | ResultsDashboard | Results view |
| `/timeline` | TimelinePage | Health timeline |
| `/timeline/compare` | ComparePage | Compare assessments |
| `/recommendations` | RecommendationCenter | Health recommendations |
| `/body-systems` | BodySystemDashboard | Body systems overview |
| `/settings` | SettingsPage | User settings |

### Doctor Routes (DOCTOR role only)

| Route | Component | Description |
|-------|-----------|-------------|
| `/cms` | CMSLayout | CMS root |
| `/cms/dashboard` | CMSDashboardPage | CMS dashboard |
| `/cms/questions` | QuestionsListPage | Question management |
| `/cms/builder` | QuestionnaireBuilderPage | Question builder |
| `/cms/graph` | KnowledgeGraphEditorPage | Knowledge graph |
| `/cms/rules-builder` | RuleBuilderPage | Rule builder |
| `/cms/approvals` | ApprovalQueuePage | Approval queue |
| `/cms/publishing` | PublishingWorkflowsPage | Publishing workflows |
| `/cms/audit` | AuditViewerPage | Audit logs |
| `/cms/users` | UsersRolesPage | User management |
| `/cms/settings` | SettingsPage | CMS settings |

### Shared Routes (Public)

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | LandingPage | Account type selection |
| `/login` | LoginPage | Login (with returnTo) |
| `/register` | RegisterPage | Registration (with role) |
| `/forgot-password` | ForgotPasswordPage | Password reset |

---

## Part 6: Permission Matrix

| Role | Patient Routes | Doctor Routes | CMS Routes | Admin Routes |
|------|--------------|--------------|------------|--------------|
| patient | ✅ | ❌ | ❌ | ❌ |
| doctor | ❌ | ✅ | ✅ | ❌ |
| super_admin | ❌ | ✅ | ✅ | ✅ |

---

## Part 7: Implementation Plan

### Phase 1: Foundation
1. Create role types
2. Create guards (RequireAuth, RequireRole)
3. Update AuthProvider with role

### Phase 2: Layouts
4. Create PatientLayout (patient sidebar)
5. Create DoctorLayout (CMS sidebar)
6. Update navigation configs

### Phase 3: Routes
7. Create patientRoutes.tsx
8. Create doctorRoutes.tsx
9. Update main router.tsx

### Phase 4: Auth Flow
10. Create LandingPage with account type
11. Update Login with role-aware redirect
12. Create Register with role

### Phase 5: Cleanup
13. Remove CMS link from patient nav
14. Bundle analysis
15. Testing

---

## Part 8: Verification Checklist

- [ ] Patients cannot access `/cms/*` routes
- [ ] Doctors cannot access patient dashboard
- [ ] Login redirects based on role
- [ ] Registration stores role in database
- [ ] Sidebar shows only role-appropriate items
- [ ] URL-based access blocked for wrong roles
- [ ] Bundle does not include CMS for patients
- [ ] Deep links protected
- [ ] Refresh maintains role state

---

## Conclusion

The application requires **immediate architectural changes** to implement proper RBAC. The current architecture is unsuitable for production due to critical security vulnerabilities.

**Estimated Implementation Time:** 8-12 hours

**Priority:** 🔴 CRITICAL

---

*Report Generated: 2026-08-04*
