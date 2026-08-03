import React from 'react'
import { Link } from 'react-router-dom'

const NotFound: React.FC = () => (
  <div className="min-h-screen flex flex-col items-center justify-center">
    <h1 className="text-4xl">404</h1>
    <p className="mt-2">Page not found</p>
    <Link to="/" className="mt-4 text-indigo-600">Go home</Link>
  </div>
)

export default NotFound
