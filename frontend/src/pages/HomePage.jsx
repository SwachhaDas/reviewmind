import React from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

function HomePage() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const features = [
    {
      icon: '📚',
      title: t('homeFeatureReviewTitle'),
      desc: t('homeFeatureReviewDesc'),
      route: '/review',
      color: 'from-blue-500 to-blue-600',
    },
    {
      icon: '💬',
      title: t('homeFeatureChatTitle'),
      desc: t('homeFeatureChatDesc'),
      route: '/chat',
      color: 'from-green-500 to-green-600',
    },
    {
      icon: '🎯',
      title: t('homeFeatureQuizTitle'),
      desc: t('homeFeatureQuizDesc'),
      route: '/quiz',
      color: 'from-yellow-500 to-yellow-600',
    },
    {
      icon: '🎨',
      title: t('homeFeaturePresentationTitle'),
      desc: t('homeFeaturePresentationDesc'),
      route: '/presentation',
      color: 'from-purple-500 to-purple-600',
    },
  ]

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          {t('homeWelcome')} 👋
        </h1>
        <p className="text-gray-600">{t('homeSubtitle')}</p>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {features.map((feature, idx) => (
          <button
            key={idx}
            onClick={() => navigate(feature.route)}
            className="group text-left bg-white border border-gray-200 rounded-2xl p-6 hover:shadow-xl transition-all duration-200 hover:-translate-y-1"
          >
            <div
              className={`inline-flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-br ${feature.color} text-white text-2xl mb-4`}
            >
              {feature.icon}
            </div>
            <h2 className="text-xl font-bold text-gray-800 mb-2 group-hover:text-blue-600">
              {feature.title}
            </h2>
            <p className="text-sm text-gray-500">{feature.desc}</p>
          </button>
        ))}
      </div>

      {/* Quick Tip */}
      <div className="mt-12 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">
          ✨ {t('homeQuickTip')}
        </h3>
        <p className="text-sm text-gray-600">{t('homeQuickTipDesc')}</p>
      </div>
    </div>
  )
}

export default HomePage