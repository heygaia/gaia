"use client";
import { ReactNode } from "react";

import Footer from "@/components/navigation/Footer";
import Navbar from "@/components/navigation/Navbar";

export default function LandingLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <div className="relative">
        {/* Backdrop blur overlay */}
        <div
          id="navbar-backdrop"
          className="pointer-events-none fixed inset-0 z-40 bg-black/20 opacity-0 backdrop-blur-sm transition-opacity duration-300 ease-in-out"
        />

        <Navbar />

        {children}

        <Footer />
      </div>
    </>
  );
}
