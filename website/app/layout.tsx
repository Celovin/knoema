import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://luvoire.celovin.com"),
  title: "Luvoire — Agent simulation that remembers.",
  description:
    "City-scale multi-agent simulation with deterministic replay, a layered memory stack, and 28 research-grounded personality archetypes.",
  openGraph: {
    title: "Luvoire",
    description:
      "City-scale multi-agent simulation with deterministic replay and 28 research-grounded personality archetypes.",
    url: "/",
    siteName: "Luvoire",
    images: ["/og-image.png"],
  },
  twitter: {
    card: "summary_large_image",
    title: "Luvoire",
    description:
      "City-scale multi-agent simulation with deterministic replay and 28 research-grounded personality archetypes.",
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: "/",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  colorScheme: "light",
  themeColor: "#A8753A",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,300..700;1,8..60,300..700&family=JetBrains+Mono:wght@400;500&display=swap"
        />
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
