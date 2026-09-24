import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'

function MainLayout({ onBackToLanding }) {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navItems = [
    { path: '/', label: t('navHome'), icon: '🏠' },
    { path: '/how-it-works', label: t('navHowItWorks'), icon: '🎯' },
    { path: '/review', label: t('navReview'), icon: '📚' },
    { path: '/chat', label: t('navChat'), icon: '💬' },
    { path: '/quiz', label: t('navQuiz'), icon: '🎯' },
    { path: '/presentation', label: t('navPresentation'), icon: '🎨' },
    { path: '/statistics', label: t('navStatistics'), icon: '📊' },
  ]

  const isActive = (path) => location.pathname === path

  // Close mobile menu when navigating
  const handleNavClick = (path) => {
    navigate(path)
    setMobileMenuOpen(false)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation Bar */}
      <nav className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 py-3 flex items-center justify-between gap-2">
          {/* Logo */}
          <div
            className="flex items-center gap-2 cursor-pointer flex-shrink-0"
            onClick={() => navigate('/')}
          >
            <span className="text-xl sm:text-2xl">📚</span>
            <span className="text-base sm:text-xl font-bold text-blue-600 truncate">
              {t('appName')}
            </span>
          </div>

          {/* Desktop Nav Links — hidden on mobile */}
          <div className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => (
              <button
                key={item.path}
                onClick={() => handleNavClick(item.path)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition whitespace-nowrap ${
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

          {/* Right side: Language toggle + Back + Hamburger */}
          <div className="flex gap-1 sm:gap-2 items-center flex-shrink-0">
            {/* Language toggle — always visible */}
            <button
              onClick={() => i18n.changeLanguage('en')}
              className={`text-xs px-2 sm:px-3 py-1.5 rounded-lg border transition ${
                i18n.language === 'en'
                  ? 'bg-blue-500 text-white border-blue-500'
                  : 'bg-white text-gray-700 border-gray-300'
              }`}
            >
              EN
            </button>
            <button
              onClick={() => i18n.changeLanguage('bn')}
              className={`text-xs px-2 sm:px-3 py-1.5 rounded-lg border transition ${
                i18n.language === 'bn'
                  ? 'bg-blue-500 text-white border-blue-500'
                  : 'bg-white text-gray-700 border-gray-300'
              }`}
            >
              বাং
            </button>

            {/* Back to Landing — hide text on mobile */}
            <button
              onClick={onBackToLanding}
              className="text-xs px-2 sm:px-4 py-2 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-500 text-white hover:from-indigo-600 hover:to-purple-600 shadow-sm font-medium flex items-center gap-1 transition"
              title={t('backToLanding')}
            >
              <span>←</span>
              <span className="hidden sm:inline">{t('backToLanding')}</span>
            </button>

            {/* Hamburger Menu — only on mobile/tablet */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition"
              aria-label="Toggle menu"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                {mobileMenuOpen ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-gray-200 bg-white shadow-lg">
            <div className="px-3 py-2 space-y-1">
              {navItems.map((item) => (
                <button
                  key={item.path}
                  onClick={() => handleNavClick(item.path)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition ${
                    isActive(item.path)
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <span className="text-lg">{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </nav>

      {/* Page Content (nested routes render here) */}
      <Outlet />
    </div>
  )
}

export default MainLayout