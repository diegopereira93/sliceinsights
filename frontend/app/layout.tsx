import type { Metadata, Viewport } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
});

export const metadata: Metadata = {
  title: {
    default: "SliceInsights - Encontre Sua Raquete Ideal de Pickleball",
    template: "%s | SliceInsights",
  },
  description:
    "Encontre a raquete de pickleball perfeita para seu estilo de jogo. Quiz inteligente, catálogo brasileiro com 37+ raquetes, preços atualizados e recomendações personalizadas.",
  keywords: [
    "pickleball",
    "raquete pickleball",
    "paddle pickleball",
    "pickleball brasil",
    "recomendação raquete",
    "quiz pickleball",
    "comprar raquete pickleball",
  ],
  authors: [{ name: "SliceInsights" }],
  creator: "SliceInsights",
  metadataBase: new URL("https://sliceinsights.vercel.app"),
  manifest: "/manifest.json",
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true },
  },
  openGraph: {
    title: "SliceInsights - Encontre Sua Raquete Ideal de Pickleball",
    description:
      "Quiz inteligente para encontrar a raquete perfeita. Catálogo brasileiro com preços atualizados.",
    url: "https://sliceinsights.vercel.app",
    siteName: "SliceInsights",
    images: [
      {
        url: "/og-image.jpg",
        width: 1200,
        height: 630,
        alt: "SliceInsights - Recomendador de Raquetes de Pickleball",
      },
    ],
    locale: "pt_BR",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "SliceInsights - Encontre Sua Raquete Ideal",
    description:
      "Quiz inteligente para recomendar a raquete de pickleball perfeita para você.",
    images: ["/og-image.jpg"],
  },
  alternates: {
    canonical: "https://sliceinsights.vercel.app",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#0f172a",
};

import { Toaster } from "@/components/ui/toaster";
import { MobileLayout } from "@/components/layout/mobile-layout";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" className={`${inter.variable} ${outfit.variable} dark`}>
      <body className="min-h-screen bg-background font-sans antialiased selection:bg-blue-500/30">
        <script dangerouslySetInnerHTML={{ __html: `
          if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistrations().then(registrations => {
              for (const registration of registrations) {
                registration.unregister();
              }
            });
          }
          // Clear all caches
          if ('caches' in window) {
            caches.keys().then(names => {
              for (const name of names) caches.delete(name);
            });
          }
        ` }} />
        <MobileLayout>{children}</MobileLayout>
        <Toaster />
      </body>
    </html>
  );
}
