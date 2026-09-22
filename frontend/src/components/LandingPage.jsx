import React from 'react'
import { useTranslation } from 'react-i18next'

function LandingPage({ onGetStarted }) {
  const { t, i18n } = useTranslation()

  // Persist language choice in localStorage
  const changeLang = (lang) => {
    i18n.changeLanguage(lang)
    localStorage.setItem('reviewmind_lang', lang)
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <div className="max-w-xl w-full text-center">
        {/* Language toggle */}
        <div className="flex justify-center gap-2 mb-6">
          <button
            onClick={() => changeLang('en')}
            className={`px-4 py-1.5 rounded-lg text-sm ${
              i18n.language === 'en' ? 'bg-blue-500 text-white' : 'bg-white border'
            }`}
          >
            English
          </button>
          <button
            onClick={() => changeLang('bn')}
            className={`px-4 py-1.5 rounded-lg text-sm ${
              i18n.language === 'bn' ? 'bg-blue-500 text-white' : 'bg-white border'
            }`}
          >
            বাংলা
          </button>
        </div>

        {/* Logo + title */}
        <h1 className="text-4xl font-bold text-blue-600 mb-3">
          📚 {t('appName')}
        </h1>

        {/* Tagline */}
        <p className="text-lg text-gray-600 mb-8">{t('tagline')}</p>

        {/* CTA button */}
        <button
          onClick={onGetStarted}
          className="px-8 py-3 bg-blue-500 text-white rounded-lg text-lg hover:bg-blue-600"
        >
          {t('getStarted')} →
        </button>

        {/* Feature grid — all text via translation keys */}
        <div className="grid grid-cols-2 gap-3 mt-10 text-left">
          <div className="bg-white p-4 rounded-lg border">
            <p className="font-semibold text-sm">🔍 {t('featureSearch')}</p>
            <p className="text-xs text-gray-500 mt-1">{t('featureSearchDesc')}</p>
          </div>

          <div className="bg-white p-4 rounded-lg border">
            <p className="font-semibold text-sm">🤖 {t('featureAiScreen')}</p>
            <p className="text-xs text-gray-500 mt-1">{t('featureAiScreenDesc')}</p>
          </div>

          <div className="bg-white p-4 rounded-lg border">
            <p className="font-semibold text-sm">📊 {t('featurePrisma')}</p>
            <p className="text-xs text-gray-500 mt-1">{t('featurePrismaDesc')}</p>
          </div>

          <div className="bg-white p-4 rounded-lg border">
            <p className="font-semibold text-sm">📄 {t('featureReport')}</p>
            <p className="text-xs text-gray-500 mt-1">{t('featureReportDesc')}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LandingPage