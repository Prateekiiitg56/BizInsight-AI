import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center">
      <p className="muted text-sm font-medium">404</p>
      <h1 className="text-2xl font-semibold tracking-tight">Page not found</h1>
      <p className="muted max-w-sm text-sm">The page you&apos;re looking for doesn&apos;t exist or has been moved.</p>
      <Link href="/" className="btn-primary mt-2">
        Back to home
      </Link>
    </main>
  );
}
