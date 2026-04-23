import { MessageSquare, User, Settings, ClipboardList } from 'lucide-react'
import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', icon: MessageSquare, label: 'Chat' },
  { to: '/tracker', icon: ClipboardList, label: 'Tracker' },
  { to: '/profile', icon: User, label: 'Profile' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  return (
    <aside className="w-16 bg-slate-900 border-r border-slate-800 flex flex-col items-center py-4 gap-2">
      <div className="mb-4">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
          L
        </div>
      </div>
      {links.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end
          className={({ isActive }) =>
            `w-10 h-10 rounded-lg flex items-center justify-center transition-colors group relative
            ${isActive ? 'bg-blue-600 text-white' : 'text-slate-500 hover:bg-slate-800 hover:text-slate-300'}`
          }
          title={label}
        >
          <Icon size={18} />
        </NavLink>
      ))}
    </aside>
  )
}
