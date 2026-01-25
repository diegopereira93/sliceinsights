import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { MobileLayout } from "@/components/layout/mobile-layout";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SliceInsights - Encontre Sua Raquete Ideal",
  description: "Insights precisos para sua melhor jogada. Encontre a raquete ideal usando nossa análise de dados avançada para Padel.",
  manifest: "/manifest.json",
  openGraph: {
    title: "SliceInsights - Intelligent Padel Insights",
    description: "Encontre a raquete ideal para seu estilo de jogo com SliceInsights.",
    url: "https://sliceinsights.com.br",
    siteName: "SliceInsights",
    images: [
      {
        url: "/og-image.jpg",
        width: 1200,
        height: 630,
      },
    ],
    locale: "pt_BR",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "SliceInsights",
    description: "Insights precisos para sua melhor jogada.",
    images: ["/og-image.jpg"],
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
