import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "REVERSEFORGE AI",
  description: "Authorized application analysis and independent reconstruction",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-mesh font-sans text-ink-900 antialiased dark:bg-ink-950 dark:text-paper-100">
        {children}
      </body>
    </html>
  );
}
