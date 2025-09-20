import type { Metadata } from "next";

import { RedirectLoader } from "@/components/shared/RedirectLoader";
import { apiauth } from "@/lib";
// import SignupForm from "@/features/auth/components/SignupForm";

export const metadata: Metadata = {
  title: "Sign Up",
  description:
    "Create your GAIA account today and unlock the power of your personal AI assistant. Get started now!",
  openGraph: {
    title: "Sign Up",
    description: "Create your GAIA account today and unlock the power of AI.",
    url: "https://heygaia.io/signup",
    images: ["/images/screenshot.webp"],
    siteName: "GAIA - Your Personal Assistant",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Sign Up",
    description: "Create your GAIA account today and unlock the power of AI.",
    images: ["/images/screenshot.webp"],
  },
};

// Redirect to the OAuth signup endpoint directly
export default function SignupPage() {
  // return <SignupForm />;

  return (
    <div className="h-screen">
      <RedirectLoader url={`${apiauth.getUri()}oauth/login/workos`} replace />
    </div>
  );
}
