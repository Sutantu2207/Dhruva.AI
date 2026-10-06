import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/layout/header";
import { AuthProvider } from "@/lib/auth-context";

export const metadata: Metadata = {
  title: "Dhruva.AI - Career Intelligence & Adaptive Learning Platform",
  description:
    "AI-powered career intelligence, adaptive learning, course delivery, student development, and institutional education platform for engineering students.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 font-sans antialiased dark:bg-slate-950">
        <AuthProvider>
          <Header />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
