"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";
import { UserPlus, CheckCircle2, Shield } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isAuthenticated } = useAuth();

  const [firstName, setFirstName] = React.useState("");
  const [lastName, setLastName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [institutionId, setInstitutionId] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [isSuccess, setIsSuccess] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  React.useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);

  // Client-side password rules validation
  const passwordChecks = React.useMemo(() => ({
    length: password.length >= 8,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>\-_+=\[\]]/.test(password),
  }), [password]);

  const isPasswordValid = Object.values(passwordChecks).every(Boolean);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isPasswordValid) {
      setError("Please ensure your password satisfies all security requirements.");
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      await register({
        first_name: firstName,
        last_name: lastName,
        email,
        password,
        institution_id: institutionId.trim() || undefined,
      });
      setIsSuccess(true);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Registration could not be completed. Please check your connection.");
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
          <CardTitle className="text-xl">Registration Successful</CardTitle>
          <CardDescription>
            Your student account for <span className="font-semibold text-slate-800 dark:text-slate-200">{email}</span> has been created.
          </CardDescription>
          <p className="text-xs text-slate-500">
            A verification link has been recorded. You can now proceed to log in.
          </p>
          <Link href="/login">
            <Button className="w-full mt-4">Proceed to Sign In</Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center p-4">
      <Card className="w-full max-w-lg shadow-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <UserPlus className="h-5 w-5 text-indigo-600" />
              <CardTitle className="text-xl">Create Student Account</CardTitle>
            </div>
            <Badge variant="outline" className="text-xs font-mono">
              Student Registration Only
            </Badge>
          </div>
          <CardDescription>
            Self-registration on Dhruva.AI is exclusively for engineering students.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertTitle>Registration Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="First Name"
                required
                placeholder="e.g. Alex"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
              />
              <Input
                label="Last Name"
                required
                placeholder="e.g. Rivera"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
              />
            </div>

            <Input
              label="Institutional Email"
              type="email"
              autoComplete="email"
              required
              placeholder="alex.rivera@college.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                Password
              </label>
              <input
                type="password"
                autoComplete="new-password"
                required
                className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-indigo-500 dark:border-slate-700 dark:bg-slate-900"
                placeholder="Create strong password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />

              {/* Password complexity checklist */}
              <div className="grid grid-cols-2 gap-1 text-[11px] pt-1 text-slate-500">
                <div className={passwordChecks.length ? "text-emerald-600 font-medium" : ""}>
                  • Min 8 characters
                </div>
                <div className={passwordChecks.upper ? "text-emerald-600 font-medium" : ""}>
                  • At least 1 uppercase (A-Z)
                </div>
                <div className={passwordChecks.lower ? "text-emerald-600 font-medium" : ""}>
                  • At least 1 lowercase (a-z)
                </div>
                <div className={passwordChecks.number ? "text-emerald-600 font-medium" : ""}>
                  • At least 1 digit (0-9)
                </div>
                <div className={passwordChecks.special ? "text-emerald-600 font-medium" : ""}>
                  • At least 1 symbol (!@#$...)
                </div>
              </div>
            </div>

            <Input
              label="Institution Code / Campus ID (Optional)"
              placeholder="e.g. CAMPUS-BLR-01"
              value={institutionId}
              onChange={(e) => setInstitutionId(e.target.value)}
            />

            <div className="flex items-center space-x-2 rounded-md bg-slate-50 p-2.5 text-xs text-slate-500 dark:bg-slate-800/50">
              <Shield className="h-4 w-4 text-indigo-600 shrink-0" />
              <span>
                Faculty, mentor, and departmental administrator accounts are provisioned via administrative invitation.
              </span>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-4">
            <Button
              type="submit"
              className="w-full"
              isLoading={isSubmitting}
              disabled={isSubmitting || !firstName || !lastName || !email || !isPasswordValid}
            >
              Create Account
            </Button>

            <div className="text-center text-xs text-slate-500">
              Already have an account?{" "}
              <Link href="/login" className="font-semibold text-indigo-600 hover:underline dark:text-indigo-400">
                Sign In
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
