import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { MobileLayout } from "@/components/layout/mobile-layout";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    default: "SliceInsights - Encontre Sua Raquete Ideal de Pickleball",
    template: "%s | SliceInsights"
  },
  description: "Encontre a raquete de pickleball perfeita para seu estilo de jogo. Quiz inteligente, catálogo brasileiro com 37+ raquetes, preços atualizados e recomendações personalizadas.",
  keywords: ["pickleball", "raquete pickleball", "paddle pickleball", "pickleball brasil", "recomendação raquete", "quiz pickleball", "comprar raquete pickleball"],
  authors: [{ name: "SliceInsights" }],
  creator: "SliceInsights",
  metadataBase: new URL("https://frontend-five-iota-18.vercel.app"),
  manifest: "/manifest.json",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
    },
  },
  openGraph: {
    title: "SliceInsights - Encontre Sua Raquete Ideal de Pickleball",
    description: "Quiz inteligente para encontrar a raquete perfeita. Catálogo brasileiro com preços atualizados.",
    url: "https://frontend-five-iota-18.vercel.app",
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
    description: "Quiz inteligente para recomendar a raquete de pickleball perfeita para você.",
    images: ["/og-image.jpg"],
  },
  alternates: {
    canonical: "https://frontend-five-iota-18.vercel.app",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#ffffff",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className={`${inter.className} antialiased`}>
        <MobileLayout>
          {children}
          <Toaster />
        </MobileLayout>
      </body>
    </html>
  );
}
