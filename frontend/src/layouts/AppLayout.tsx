import React from 'react'
import TopNav from '../shared/ui/TopNav'

const AppLayout: React.FC<React.PropsWithChildren> = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col">
      <TopNav />
      <main className="flex-1 p-4">{children}</main>
      <footer className="p-4 text-center text-sm text-gray-500">© {new Date().getFullYear()} Medicheck</footer>
    </div>
  )
}

export default AppLayout
