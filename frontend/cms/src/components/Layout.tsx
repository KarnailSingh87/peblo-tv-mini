import React from "react";
import { Link, useLocation } from "wouter";
import {
  Film,
  PlusCircle,
  UploadCloud,
  LogOut,
  Tv,
  CheckCircle,
  AlertTriangle,
  ExternalLink,
  ShieldCheck,
  Edit3
} from "lucide-react";
import { useAuth } from "../features/auth/AuthContext";
import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [location] = useLocation();
  const { user, logout } = useAuth();

  const { data: validationReport } = useQuery({
    queryKey: ["validationReport"],
    queryFn: () => api.getValidationReport(),
    refetchInterval: 15000
  });

  const hasBlockers = (validationReport?.blocking_count || 0) > 0;

  const navItems = [
    {
      label: "Show Catalogue",
      href: "/admin/shows",
      icon: Film,
      exact: true
    },
    {
      label: "Add New Show",
      href: "/admin/shows/new",
      icon: PlusCircle
    },
    {
      label: "Publish & Audit",
      href: "/admin/publish",
      icon: UploadCloud,
      badge: hasBlockers ? `${validationReport?.blocking_count} issues` : "Ready",
      badgeColor: hasBlockers
        ? "bg-rose-500/20 text-rose-300 border-rose-500/30"
        : "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
    }
  ];

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500 selection:text-white">
      {/* Left Sidebar */}
      <aside className="w-64 bg-slate-900/90 border-r border-slate-800 flex flex-col justify-between shrink-0 fixed inset-y-0 left-0 z-30 backdrop-blur-md">
        <div>
          {/* Brand Header */}
          <div className="h-16 px-6 flex items-center gap-3 border-b border-slate-800/80 bg-slate-950/40">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
              <Tv className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold tracking-tight text-base bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-300">
                Peblo TV
              </span>
              <span className="text-[10px] ml-1.5 uppercase font-semibold px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-400 border border-indigo-800/60">
                CMS
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1.5">
            <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Content Operations
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.exact ? location === item.href : location.startsWith(item.href);

              return (
                <Link key={item.href} href={item.href}>
                  <a
                    className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                      isActive
                        ? "bg-indigo-600/15 text-indigo-300 border border-indigo-500/30 shadow-sm"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className={`w-4 h-4 ${isActive ? "text-indigo-400" : "text-slate-400"}`} />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${item.badgeColor}`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </a>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Footer */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/30">
          <div className="flex items-center justify-between mb-3 px-1">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-xs font-semibold text-slate-200 border border-slate-700">
                {user?.username?.[0]?.toUpperCase() || "U"}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-semibold text-slate-200 truncate">{user?.username}</p>
                <div className="flex items-center gap-1 mt-0.5">
                  {user?.role === "admin" ? (
                    <span className="flex items-center gap-1 text-[10px] font-medium text-amber-400">
                      <ShieldCheck className="w-3 h-3" /> Admin
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-[10px] font-medium text-cyan-400">
                      <Edit3 className="w-3 h-3" /> Editor
                    </span>
                  )}
                </div>
              </div>
            </div>
            <button
              onClick={logout}
              title="Log out"
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>

          <a
            href="http://localhost:3000"
            target="_blank"
            rel="noreferrer"
            className="flex items-center justify-center gap-1.5 w-full py-1.5 px-3 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-800/50 hover:bg-slate-800 border border-slate-700/60 transition-all"
          >
            <span>Open Viewer UI</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 ml-64 min-h-screen flex flex-col">
        {children}
      </main>
    </div>
  );
};
