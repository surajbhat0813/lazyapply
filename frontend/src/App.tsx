import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Chat from './pages/Chat'
import Profile from './pages/Profile'
import Settings from './pages/Settings'
import Tracker from './pages/Tracker'

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen w-screen bg-slate-900 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-hidden flex">
          <Routes>
            <Route path="/" element={<Chat />} />
            <Route path="/tracker" element={<Tracker />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
