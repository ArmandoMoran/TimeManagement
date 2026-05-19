import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate, useRouter } from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { useLogin } from "./useAuth";

const loginSchema = z.object({
  email: z.string().email("enter a valid email"),
  password: z.string().min(1, "password is required"),
});

type LoginValues = z.infer<typeof loginSchema>;

export function LoginPage(): React.ReactElement {
  const navigate = useNavigate();
  const router = useRouter();
  const { mutateAsync, isPending, error } = useLogin();

  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const submit = form.handleSubmit(async (values) => {
    await mutateAsync(values);
    await router.invalidate();
    await navigate({ to: "/" });
  });

  function onSubmit(event: React.SyntheticEvent<HTMLFormElement>): void {
    void submit(event);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm space-y-4 rounded-lg border bg-card p-6 shadow"
        aria-label="Login"
      >
        <h2 className="text-xl font-semibold">Sign in to TimeTrack</h2>

        <div className="space-y-1.5">
          <label htmlFor="email" className="text-sm font-medium">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            className="w-full rounded-md border px-3 py-2 text-sm"
            {...form.register("email")}
          />
          {form.formState.errors.email && (
            <p role="alert" className="text-xs text-red-600">
              {form.formState.errors.email.message}
            </p>
          )}
        </div>

        <div className="space-y-1.5">
          <label htmlFor="password" className="text-sm font-medium">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            className="w-full rounded-md border px-3 py-2 text-sm"
            {...form.register("password")}
          />
          {form.formState.errors.password && (
            <p role="alert" className="text-xs text-red-600">
              {form.formState.errors.password.message}
            </p>
          )}
        </div>

        {error && (
          <p role="alert" className="text-sm text-red-600">
            {error.code === "authentication_required"
              ? "Invalid email or password."
              : error.message}
          </p>
        )}

        <button
          type="submit"
          disabled={isPending}
          className="w-full rounded-md bg-foreground px-3 py-2 text-sm font-medium text-background disabled:opacity-50"
        >
          {isPending ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
