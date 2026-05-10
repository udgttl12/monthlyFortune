export function normalizeBirthDateInput(value: string): string {
  return value.replace(/\D/g, "").slice(0, 8);
}

export function parseBirthDateInput(value: string): string | null {
  const digits = normalizeBirthDateInput(value);

  if (!/^\d{8}$/.test(digits)) {
    return null;
  }

  const year = digits.slice(0, 4);
  const month = digits.slice(4, 6);
  const day = digits.slice(6, 8);
  const isoDate = `${year}-${month}-${day}`;
  const parsed = new Date(`${isoDate}T00:00:00.000Z`);

  if (Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== isoDate) {
    return null;
  }

  return isoDate;
}
