import React from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'

function MainLayout({ onBackToLanding }) {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()

  const navItems = [
    { path: '/', label: t('navHome'), icon: '🏠' },
    { path: '/how-it-works', label: t('navHowItWorks'), icon: '🎯' },
    { path: '/review', label: t('navReview'), icon: '📚' },
    { path: '/chat', label: t('navChat'), icon: '💬' },
    { path: '/quiz', label: t('navQuiz'), icon: '🎯' },
    { path: '/presentation', label: t('navPresentation'), icon: '🎨' },
  ]

  const isActive = (path) => location.pathname === path

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation Bar */}
      <nav className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          {/* Logo */}
          <div
            className="flex items-center gap-2 cursor-pointer"
            onClick={() => navigate('/')}
          >
            <span className="text-2xl">📚</span>
            <span className="text-xl font-bold text-blue-600">
              {t('appName')}
            </span>
          </div>

          {/* Nav Links */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                  isActive(item.path)
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <span className="mr-1">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </div>

          {/* Right side: Language toggle + Exit button */}
          <div className="flex gap-2 items-center">
            <button
              onClick={() => i18n.changeLanguage('en')}
              className={`text-xs px-3 py-1.5 rounded-lg border ${
                i18n.language === 'en'
                  ? 'bg-blue-500 text-white border-blue-500'
                  : 'bg-white text-gray-700 border-gray-300'
              }`}
            >
              EN
            </button>
            <button
              onClick={() => i18n.changeLanguage('bn')}
              className={`text-xs px-3 py-1.5 rounded-lg border ${
                i18n.language === 'bn'
                  ? 'bg-blue-500 text-white border-blue-500'
                  : 'bg-white text-gray-700 border-gray-300'
              }`}
            >
              বাং
            </button>

            {/* Exit to Landing button */}
            <button
              onClick={onBackToLanding}
              className="ml-2 text-xs px-4 py-2 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-500 text-white hover:from-indigo-600 hover:to-purple-600 shadow-sm font-medium flex items-center gap-1 transition"
              title={t('backToLanding')}
            >
              ← {t('backToLanding')}
            </button>
          </div>
        </div>
      </nav>

      {/* Page Content (nested routes render here) */}
      <Outlet />
    </div>
  )
}

export default MainLayout