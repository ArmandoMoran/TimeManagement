import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// Tailwind class-merge helper used throughout the UI; matches shadcn's `cn` convention.
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
