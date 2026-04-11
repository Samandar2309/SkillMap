import { Home, Target, BookOpen, BarChart3, User, Moon, Sun, FileCheck2, LogOut } from 'lucide-react';
import { motion } from 'motion/react';

interface SidebarProps {
  currentView: string;
  onViewChange: (view: string) => void;
  theme: string;
  toggleTheme: () => void;
  onLogout: () => void;
}

export function Sidebar({ currentView, onViewChange, theme, toggleTheme, onLogout }: SidebarProps) {
  const menuItems = [
    { id: 'dashboard', label: 'Bosh sahifa', icon: Home },
    { id: 'roadmap', label: 'Yo\'l xaritasi', icon: Target },
    { id: 'resources', label: 'Manbalar', icon: BookOpen },
    { id: 'tests', label: 'Testlar', icon: FileCheck2 },
    { id: 'analytics', label: 'Statistika', icon: BarChart3 },
    { id: 'profile', label: 'Profil', icon: User },
  ];

  return (
    <motion.div
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="w-64 h-screen bg-sidebar border-r border-sidebar-border flex flex-col"
    >
      <div className="p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#06B6D4] via-[#0EA5E9] to-[#10B981] flex items-center justify-center">
            <Target className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-sidebar-foreground">GrowthAI</h1>
            <p className="text-xs text-muted-foreground">Rivojlanish platformasi</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;

          return (
            <motion.button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg mb-1 transition-colors ${
                isActive
                  ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                  : 'text-sidebar-foreground hover:bg-sidebar-accent'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </motion.button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-sidebar-border space-y-2">
        <motion.button
          onClick={toggleTheme}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg bg-sidebar-accent text-sidebar-accent-foreground"
        >
          {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          <span>{theme === 'dark' ? 'Yorug\' rejim' : 'Qorong\'i rejim'}</span>
        </motion.button>
        <motion.button
          onClick={onLogout}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg border border-sidebar-border text-sidebar-foreground"
        >
          <LogOut className="w-5 h-5" />
          <span>Chiqish</span>
        </motion.button>
      </div>
    </motion.div>
  );
}
