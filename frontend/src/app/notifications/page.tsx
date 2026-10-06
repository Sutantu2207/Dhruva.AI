"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  fetchNotificationPreferences,
  updateNotificationPreferences,
} from "@/lib/api";
import { NotificationItem, NotificationPreferences } from "@/lib/types";
import {
  Bell,
  CheckCircle2,
  Clock,
  ExternalLink,
  Settings,
  ShieldCheck,
  Check,
  BookOpen,
  Briefcase,
} from "lucide-react";

export default function NotificationsCenterPage() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [unreadOnly, setUnreadOnly] = useState(false);

  const loadData = React.useCallback(async () => {
    try {
      setLoading(true);
      const [list, prefs] = await Promise.all([
        fetchNotifications(unreadOnly),
        fetchNotificationPreferences().catch(() => null),
      ]);
      setNotifications(list);
      setPreferences(prefs);
    } catch (err) {
      console.error("Failed to load notifications:", err);
    } finally {
      setLoading(false);
    }
  }, [unreadOnly]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleMarkRead = async (id: string) => {
    try {
      await markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (err) {
      console.error("Mark read error:", err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      console.error("Mark all read error:", err);
    }
  };

  const handleTogglePreference = async (key: keyof NotificationPreferences) => {
    if (!preferences) return;
    const updated = { ...preferences, [key]: !preferences[key] };
    setPreferences(updated);
    try {
      await updateNotificationPreferences({ [key]: updated[key] });
    } catch (err) {
      console.error("Failed to update preference:", err);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "LEARNING":
      case "REMINDER":
        return <BookOpen className="w-4 h-4 text-emerald-400" />;
      case "ASSESSMENT":
      case "DEADLINE":
        return <Clock className="w-4 h-4 text-amber-400" />;
      case "PLACEMENT":
        return <Briefcase className="w-4 h-4 text-cyan-400" />;
      case "SECURITY":
        return <ShieldCheck className="w-4 h-4 text-rose-400" />;
      default:
        return <Bell className="w-4 h-4 text-neutral-400" />;
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 md:p-12 font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-center text-emerald-400">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-100">
                Academic Notifications
              </h1>
              <p className="text-xs text-neutral-400 mt-0.5">
                Deterministic reminders, assessment deadlines, and adaptive learning updates.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 rounded-lg border border-neutral-800 bg-neutral-900 text-neutral-400 hover:text-neutral-200 text-xs flex items-center gap-1.5 transition-colors"
              title="Notification Preferences"
            >
              <Settings className="w-4 h-4" />
            </button>
            <button
              onClick={handleMarkAllRead}
              className="px-3 py-1.5 rounded-lg border border-neutral-800 bg-neutral-900 text-xs text-neutral-300 hover:bg-neutral-800 flex items-center gap-1.5 transition-colors"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Mark All as Read</span>
            </button>
          </div>
        </div>

        {/* Preferences Drawer */}
        {showSettings && preferences && (
          <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-300">
                Delivery Preferences
              </h3>
              <span className="text-[11px] text-neutral-400 font-mono">Role-governed</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
              {[
                { key: "in_app_enabled" as const, label: "In-App Feed" },
                { key: "email_enabled" as const, label: "Transactional Email" },
                { key: "learning_reminders" as const, label: "Spaced Review Alerts" },
                { key: "assessment_alerts" as const, label: "Assessment Deadlines" },
                { key: "remediation_updates" as const, label: "Remediation Plans" },
                { key: "placement_alerts" as const, label: "Placement Alerts" },
              ].map((item) => (
                <button
                  key={item.key}
                  onClick={() => handleTogglePreference(item.key)}
                  className={`p-2.5 rounded-lg border text-left flex items-center justify-between transition-colors ${
                    preferences[item.key]
                      ? "bg-neutral-950 border-emerald-500/40 text-emerald-300"
                      : "bg-neutral-950/40 border-neutral-800 text-neutral-400"
                  }`}
                >
                  <span>{item.label}</span>
                  <div
                    className={`w-3.5 h-3.5 rounded-full border ${
                      preferences[item.key]
                        ? "bg-emerald-500 border-emerald-400"
                        : "border-neutral-700"
                    }`}
                  />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Filter bar */}
        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => setUnreadOnly(false)}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              !unreadOnly
                ? "bg-neutral-800 text-neutral-200 border border-neutral-700"
                : "text-neutral-400 hover:text-neutral-300"
            }`}
          >
            All Updates
          </button>
          <button
            onClick={() => setUnreadOnly(true)}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              unreadOnly
                ? "bg-neutral-800 text-neutral-200 border border-neutral-700"
                : "text-neutral-400 hover:text-neutral-300"
            }`}
          >
            Unread Only
          </button>
        </div>

        {/* Notifications List */}
        <div className="space-y-2.5">
          {loading && (
            <div className="p-8 text-center text-xs text-neutral-400">Loading notifications...</div>
          )}

          {!loading && notifications.length === 0 && (
            <div className="p-12 text-center bg-neutral-900/30 rounded-2xl border border-neutral-800 space-y-2">
              <CheckCircle2 className="w-8 h-8 mx-auto text-neutral-600" />
              <p className="text-xs text-neutral-400">All caught up! No notifications to review.</p>
            </div>
          )}

          {notifications.map((n) => (
            <div
              key={n.id}
              className={`p-4 rounded-xl border transition-all flex items-start justify-between gap-4 ${
                n.is_read
                  ? "bg-neutral-900/20 border-neutral-800 text-neutral-400"
                  : "bg-neutral-900/60 border-neutral-700 text-neutral-200 shadow-sm"
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-neutral-950 border border-neutral-800 flex items-center justify-center shrink-0 mt-0.5">
                  {getTypeIcon(n.notification_type)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold">{n.title}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-950 border border-neutral-800 text-neutral-400 font-mono">
                      {n.notification_type}
                    </span>
                  </div>
                  <p className="text-xs text-neutral-400 mt-1 leading-relaxed">{n.message}</p>
                  <div className="text-[10px] text-neutral-400 mt-2 font-mono">
                    {new Date(n.created_at).toLocaleString()}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {n.link_url && (
                  <Link
                    href={n.link_url}
                    className="p-1.5 rounded-lg border border-neutral-800 bg-neutral-950 hover:text-emerald-400 transition-colors"
                    title="Navigate"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </Link>
                )}
                {!n.is_read && (
                  <button
                    onClick={() => handleMarkRead(n.id)}
                    className="px-2.5 py-1 rounded bg-neutral-800 hover:bg-neutral-700 text-[11px] text-neutral-300 transition-colors"
                  >
                    Mark Read
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
