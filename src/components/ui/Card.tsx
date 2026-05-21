import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padded?: boolean;
  children: ReactNode;
}

export function Card({
  padded = true,
  className = "",
  children,
  ...rest
}: CardProps) {
  return (
    <div
      {...rest}
      className={[
        "bg-white border border-slate-200/80 rounded-2xl shadow-[0_1px_2px_rgba(15,23,42,0.04)]",
        padded ? "p-6 sm:p-7" : "",
        className,
      ].join(" ")}
    >
      {children}
    </div>
  );
}

interface SectionHeaderProps {
  eyebrow?: string;
  title: string;
  description?: string;
  className?: string;
}

export function SectionHeader({
  eyebrow,
  title,
  description,
  className = "",
}: SectionHeaderProps) {
  return (
    <div className={["mb-6", className].join(" ")}>
      {eyebrow ? (
        <p className="mb-2 text-xs font-medium uppercase tracking-[0.14em] text-blue-600">
          {eyebrow}
        </p>
      ) : null}
      <h2 className="text-2xl sm:text-[28px] font-semibold tracking-tight text-slate-900">
        {title}
      </h2>
      {description ? (
        <p className="mt-2 max-w-2xl text-sm sm:text-base text-slate-500">
          {description}
        </p>
      ) : null}
    </div>
  );
}
