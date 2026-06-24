import type { Metadata } from "next";
import { Space_Grotesk, Space_Mono } from "next/font/google";
import { CursorSpotlight } from "@/components/CursorSpotlight";
import { Footer } from "@/components/Footer";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const spaceMono = Space_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "700"],
});

export const metadata: Metadata = {
  title: "FlightNu — Flight Price Intelligence",
  description: "Track flight prices, forecast fares, and know exactly when to buy.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${spaceMono.variable} dark h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <CursorSpotlight />
        {children}
        <Footer />
      </body>
    </html>
  );
}
