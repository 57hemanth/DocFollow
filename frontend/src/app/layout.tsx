import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { DM_Sans } from 'next/font/google'

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
})


export const metadata: Metadata = {
  title: "PingDoc",
  description: "AI that follows up, so you can focus on healing",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${dmSans.variable} font-sans antialiased`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
