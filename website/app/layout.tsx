import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://luvoire.celovin.com"),
  title: "Luvoire",
  description:
    "LLM-based multi-agent social simulation engine for games, fictional public-safety replay research, and academic simulation.",
  openGraph: {
    title: "Luvoire",
    description:
      "One engine for persistent NPCs, synthetic replay research, and reproducible social simulation.",
    url: "/",
    siteName: "Luvoire",
    images: ["/og-image.png"],
  },
  twitter: {
    card: "summary_large_image",
    title: "Luvoire",
    description:
      "One engine for persistent NPCs, synthetic replay research, and reproducible social simulation.",
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
  themeColor: "#0c6b4d",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
