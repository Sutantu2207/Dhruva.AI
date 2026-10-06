"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { verifyEmail, ApiError } from "@/lib/api";
import { MailCheck, CheckCircle2 } from "lucide-react";

function VerifyEmailForm() {
  const searchParams = useSearchParams();
  const queryToken = searchParams.get("token") || "";

  const [token, setToken] = React.useState(queryToken);
  const [error, setError] = React.useState<string | null>(null);
  const [isSuccess, setIsSuccess] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await verifyEmail(token);
      setIsSuccess(true);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Verification link is invalid or has expired.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-md text-center p-6 space-y-4">
          <div className="flex justify-center">
            <CheckCircle2 className="h-12 w-12 text-emerald-600" />
          </div>
          <CardTitle className="text-xl">Email Address Verified</CardTitle>
          <CardDescription>
            Your account email has been verified. Full access to platform modules is now unlocked.
          </CardDescription>
          <Link href="/login">
            <Button className="w-full mt-4">Continue to Platform</Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center space-x-2">
            <MailCheck className="h-5 w-5 text-indigo-600" />
            <CardTitle className="text-xl">Verify Account Email</CardTitle>
          </div>
          <CardDescription>
            Confirm your institutional email address to complete verification.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertTitle>Verification Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Input
              label="Verification Token"
              required
              placeholder="Paste token from email"
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
          </CardContent>

          <CardFooter className="flex flex-col space-y-4">
            <Button
              type="submit"
              className="w-full"
              isLoading={isSubmitting}
              disabled={isSubmitting || !token}
            >
              Verify Email Address
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <React.Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Loading...</div>}>
      <VerifyEmailForm />
    </React.Suspense>
  );
}
