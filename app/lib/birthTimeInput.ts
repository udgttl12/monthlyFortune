export function normalizeBirthTimeInput(value: string): string {
  return value.replace(/\D/g, "").slice(0, 4);
}

export function parseBirthTimeInput(value: string): string | null {
  const digits = normalizeBirthTimeInput(value);

  if (!/^\d{4}$/.test(digits)) {
    return null;
  }

  const hour = Number(digits.slice(0, 2));
  const minute = Number(digits.slice(2, 4));

  if (hour > 23 || minute > 59) {
    return null;
  }

  return `${digits.slice(0, 2)}:${digits.slice(2, 4)}`;
}
