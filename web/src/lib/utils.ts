import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
export const percent = (n: number, digits = 0) =>
  `${(n * 100).toFixed(digits)}%`;
