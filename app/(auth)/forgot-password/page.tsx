"use client";

import { useState } from "react";
import { requestPasswordReset } from "@/lib/supabase/client-auth";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function ForgotPasswordPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await requestPasswordReset(email);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send reset email");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="p-8">
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6">
          <h3 className="font-semibold mb-2">Check your email</h3>
          <p className="text-sm">
            We've sent a password reset link to <strong>{email}</strong>. Click the link in the email to reset your password.
          </p>
        </div>

        <div className="text-center text-sm text-gray-600">
          <Link href="/login" className="text-maps-teal hover:text-maps-teal-dark font-medium">
            Back to Sign In
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold text-maps-navy mb-2">Reset Password</h2>
      <p className="text-gray-600 text-sm mb-6">
        Enter your email address and we'll send you a link to reset your password.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="email" className="label">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input"
            placeholder="you@example.com"
            required
            disabled={loading}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Sending..." : "Send Reset Link"}
        </button>
      </form>

      <div className="mt-6 text-center text-sm text-gray-600">
        Remember your password?{" "}
        <Link href="/login" className="text-maps-teal hover:text-maps-teal-dark font-medium">
          Sign In
        </Link>
      </div>
    </div>
  );
}
