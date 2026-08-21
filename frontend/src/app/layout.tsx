import type { Metadata } from "next";
import { Outfit, Manrope } from "next/font/google";
import "./globals.css";

const display = Outfit({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const body = Manrope({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

export const metadata: Metadata = {
  title: "LiftAI — AI-Powered Lifting Coach",
  description: "Track workouts, analyze progress, and get AI coaching",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable}`}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
