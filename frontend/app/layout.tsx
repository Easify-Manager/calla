import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MedVoice - Voice-First Medication Adherence",
  description: "AI-powered phone calls for medication reminders. Zero app learning curve for patients.",
  keywords: ["medication", "adherence", "voice AI", "healthcare", "caregiver"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700,900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
