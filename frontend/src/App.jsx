import React, { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './components/LandingPage'
import MainLayout from './components/MainLayout'
import HomePage from './pages/HomePage'
import HowItWorks from './pages/HowItWorks'
import ReviewPage from './pages/ReviewPage'
import ChatPage from './pages/ChatPage'
import QuizPage from './pages/QuizPage'
import PresentationPage from './pages/PresentationPage'
import StatisticsPage from './pages/StatisticsPage'  // ← NEW

function App() {
  const [showLanding, setShowLanding] = useState(true)

  const enterApp = () => {
    setShowLanding(false)
  }

  const goToLanding = () => {
    setShowLanding(true)
  }

  if (showLanding) {
    return <LandingPage onGetStarted={enterApp} />
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout onBackToLanding={goToLanding} />}>
          <Route index element={<HomePage onBackToLanding={goToLanding} />} />
          <Route path="how-it-works" element={<HowItWorks />} />
          <Route path="review" element={<ReviewPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="quiz" element={<QuizPage />} />
          <Route path="presentation" element={<PresentationPage />} />
          <Route path="statistics" element={<StatisticsPage />} />  {/* ← NEW */}
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App