import clsx from 'clsx';
import {
  Home,
  Sparkles,
  BookOpen,
  Wand2,
  Globe,
  Map,
  Settings,
  LogOut,
} from 'lucide-react';

const Sidebar = ({ currentPath, onNavigate, onLogout, user }) => {
  const navItems = [
    { icon: Home, label: 'Dashboard', path: '/' },
    { icon: Sparkles, label: 'AI', path: '/chat' },
    { icon: BookOpen, label: 'Browse', path: '/browse' },
    { icon: Wand2, label: 'Create', path: '/create' },
    { icon: Globe, label: 'Universe', path: '/universe' },
    { icon: Map, label: 'Maps', path: '/maps' },
  ];

  return (
    <div className="w-[250px] bg-surface h-full flex flex-col border-r border-border-subtle">
      {/* Logo Section */}
      <div className="px-4 py-6 border-b border-border-subtle">
        <h2 className="text-lg font-bold text-txt flex items-center gap-2">
          ⚡ MythosEngine
        </h2>
        <p className="text-xs text-txt-muted mt-2">Your world. Your story.</p>
      </div>

      {/* Navigation Section */}
      <div className="px-4 py-4">
        <p className="uppercase text-[11px] tracking-widest text-txt-muted font-bold mb-3">
          Navigation
        </p>

        <nav className="flex flex-col gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPath === item.path;

            return (
              <button
                key={item.path}
                onClick={() => onNavigate(item.path)}
                className={clsx(
                  'flex items-center gap-3 rounded-xl px-4 py-3 transition-all text-left w-full',
                  isActive
                    ? 'bg-accent-soft text-accent font-semibold border-l-4 border-accent'
                    : 'text-txt-dim hover:bg-hover'
                )}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Bottom Section */}
      <div className="px-4 py-4 border-t border-border-subtle flex flex-col gap-2">
        {/* User info */}
        {user && (
          <div className="px-4 py-2 mb-1">
            <p className="text-txt text-sm font-medium truncate">{user.username}</p>
            <p className="text-txt-muted text-xs truncate">{user.email}</p>
          </div>
        )}

        <button
          onClick={() => onNavigate('/settings')}
          className={clsx(
            'flex items-center gap-3 rounded-xl px-4 py-3 transition-all text-left w-full',
            currentPath === '/settings'
              ? 'bg-accent-soft text-accent font-semibold border-l-4 border-accent'
              : 'text-txt-dim hover:bg-hover'
          )}
        >
          <Settings size={20} />
          <span>Settings</span>
        </button>

        <button
          onClick={onLogout}
          className="flex items-center gap-3 rounded-xl px-4 py-3 transition-all text-left w-full text-txt-dim hover:bg-hover"
        >
          <LogOut size={20} />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
