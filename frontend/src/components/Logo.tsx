import Link from "next/link";

export function Logo({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="flex items-center gap-2 rounded-md" aria-label="BizInsight AI home">
      <svg width="22" height="22" viewBox="0 0 32 32" aria-hidden="true">
        <rect width="32" height="32" rx="7" className="fill-zinc-900 dark:fill-white" />
        <rect x="8" y="17" width="4" height="7" rx="1" className="fill-white dark:fill-zinc-900" />
        <rect x="14" y="12" width="4" height="12" rx="1" className="fill-white dark:fill-zinc-900" />
        <rect x="20" y="8" width="4" height="16" rx="1" fill="#34d399" />
      </svg>
      <span className="text-base font-semibold tracking-tight">BizInsight AI</span>
    </Link>
  );
}
