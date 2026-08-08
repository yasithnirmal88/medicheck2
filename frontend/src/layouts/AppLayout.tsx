import React from 'react'

/**
 * AppLayout — thin passthrough wrapper.
 *
 * Every routed patient page that uses AppLayout is already wrapped at the
 * route level by DashboardLayout (see `PatientLayoutWithContent` in the
 * router), which provides the shrinkable sidebar + TopBar. Previously AppLayout
 * ALSO rendered its own TopNav + footer + padding, producing a double layout
 * (a second nav bar and extra padding stacked inside the sidebar's content
 * column) that squeezed page content behind/around the sidebar.
 *
 * To eliminate that duplication without touching each page component, AppLayout
 * now renders only its children. The single DashboardLayout supplies all chrome.
 *
 * Note: the standalone TopNav-based chrome that AppLayout used to render is
 * fully superseded by DashboardLayout's TopBar (theme toggle, user menu /
 * sign-out, notifications, search) and the sidebar (navigation). Full
 * AppLayout-vs-DashboardLayout consolidation is tracked separately (P3-4).
 */
const AppLayout: React.FC<React.PropsWithChildren> = ({ children }) => {
  return <>{children}</>
}

export default AppLayout
