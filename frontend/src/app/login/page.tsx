import type { Metadata } from "next";
import { AuthForm } from "@/components/AuthForm";

export const metadata: Metadata = { title: "Sign in · RAG Assistant" };

export default function LoginPage() {
  return <AuthForm mode="login" />;
}
