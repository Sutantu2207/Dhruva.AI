"use client";

import * as React from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { User, LogOut, LayoutDashboard, Brain, FileText, FolderGit2, Network, Briefcase, Compass } from "lucide-react";

export function Header() {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/95 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/95">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center space-x-3 transition-opacity hover:opacity-90">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white font-bold tracking-tight">
            Δ
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-slate-100">
                Dhruva.AI
              </span>
              <Badge variant="outline" className="text-[10px] uppercase font-mono tracking-wider">
                Production Core
              </Badge>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Career Intelligence & Institutional Education Platform
            </p>
          </div>
        </Link>

        <div className="flex items-center space-x-3">
          {isAuthenticated && user ? (
            <div className="flex items-center space-x-1 sm:space-x-2">
              <Link href="/projects">
                <Button variant="ghost" size="sm" className="hidden lg:flex items-center space-x-1 text-xs text-slate-700 dark:text-slate-300">
                  <FolderGit2 className="h-3.5 w-3.5 text-indigo-600" />
                  <span>Projects</span>
                </Button>
              </Link>
              <Link href="/skills/graph">
                <Button variant="ghost" size="sm" className="hidden lg:flex items-center space-x-1 text-xs text-slate-700 dark:text-slate-300">
                  <Network className="h-3.5 w-3.5 text-indigo-600" />
                  <span>Skill Graph</span>
                </Button>
              </Link>
              <Link href="/portfolio">
                <Button variant="ghost" size="sm" className="hidden lg:flex items-center space-x-1 text-xs text-slate-700 dark:text-slate-300">
                  <Briefcase className="h-3.5 w-3.5 text-indigo-600" />
                  <span>Portfolio</span>
                </Button>
              </Link>
              <Link href="/career">
                <Button variant="ghost" size="sm" className="hidden md:flex items-center space-x-1 text-xs text-slate-700 dark:text-slate-300">
                  <Compass className="h-3.5 w-3.5 text-indigo-600" />
                  <span>Career</span>
                </Button>
              </Link>
              <Link href="/knowledge">
                <Button variant="ghost" size="sm" className="hidden xl:flex items-center space-x-1 text-xs text-slate-700 dark:text-slate-300">
                  <Brain className="h-3.5 w-3.5 text-indigo-600" />
                  <span>Knowledge</span>
                </Button>
              </Link>
              <Link href="/my-assessments">
                <Button variant="ghost" size="sm" className="hidden md:flex items-center space-x-1 text-xs text-slate-700 dark:text-slate-300">
                  <FileText className="h-3.5 w-3.5 text-indigo-600" />
                  <span>Assessments</span>
                </Button>
              </Link>
              {(user.role === "teacher" || user.role === "mentor" || user.role === "super_admin") && (
                <Link href="/faculty">
                  <Button variant="ghost" size="sm" className="hidden md:flex items-center space-x-1 text-xs text-indigo-600 font-semibold">
                    <span>Faculty</span>
                  </Button>
                </Link>
              )}
              {(user.role === "hod" || user.role === "super_admin") && (
                <Link href="/hod">
                  <Button variant="ghost" size="sm" className="hidden md:flex items-center space-x-1 text-xs text-indigo-600 font-semibold">
                    <span>HOD</span>
                  </Button>
                </Link>
              )}
              {(user.role === "placement_officer" || user.role === "super_admin") && (
                <Link href="/placement">
                  <Button variant="ghost" size="sm" className="hidden md:flex items-center space-x-1 text-xs text-indigo-600 font-semibold">
                    <span>Placement</span>
                  </Button>
                </Link>
              )}
              {(user.role === "institution_admin" || user.role === "super_admin") && (
                <Link href="/admin/analytics">
                  <Button variant="ghost" size="sm" className="hidden md:flex items-center space-x-1 text-xs text-indigo-600 font-semibold">
                    <span>Admin</span>
                  </Button>
                </Link>
              )}
              <Link href="/dashboard">
                <Button variant="ghost" size="sm" className="flex items-center space-x-1.5">
                  <LayoutDashboard className="h-4 w-4 text-indigo-600" />
                  <span className="hidden sm:inline font-medium">{user.display_name}</span>
                  <Badge variant="secondary" className="ml-1 text-[10px] font-mono">
                    {user.role}
                  </Badge>
                </Button>
              </Link>

              <Button
                variant="outline"
                size="sm"
                onClick={() => logout()}
                className="flex items-center space-x-1 text-slate-600 hover:text-rose-600"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Sign Out</span>
              </Button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Link href="/login">
                <Button variant="ghost" size="sm" className="flex items-center space-x-1">
                  <User className="h-3.5 w-3.5" />
                  <span>Sign In</span>
                </Button>
              </Link>
              <Link href="/register">
                <Button variant="default" size="sm">
                  <span>Register</span>
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
