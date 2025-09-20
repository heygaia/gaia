import type { Metadata } from "next";

import { RedirectLoader } from "@/components/shared/RedirectLoader";
import { apiauth } from "@/lib";

// import LoginForm from "@/features/auth/components/LoginForm";

export const metadata: Metadata = {
  title: "login",
  description:
    "Access your personal AI assistant account on GAIA. login now to manage your tasks and boost your productivity.",
  openGraph: {
    title: "login",
    description: "Access your personal AI assistant account on GAIA.",
    url: "https://heygaia.io/login",
    images: ["/images/screenshot.webp"],
    siteName: "GAIA - Your Personal Assistant",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "login",
    description: "Access your personal AI assistant account on GAIA.",
    images: ["/images/screenshot.webp"],
  },
};

// Redirect to the OAuth login endpoint directly
export default function LoginPage() {
  // return <LoginForm />;

  return (
    <div className="h-screen">
      <RedirectLoader url={`${apiauth.getUri()}oauth/login/workos`} replace />
    </div>
  );
}
