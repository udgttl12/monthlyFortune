"use client";

import { useState } from "react";

type Props = {
  onSubmit: (values: Record<string, string>) => Promise<void>;
  buttonLabel: string;
};

const defaultValues = {
  name: "Ava",
  birth_date: "1994-07-18",
  birth_time: "08:30",
  latitude: "40.7128",
  longitude: "-74.0060",
  timezone: "UTC",
};

export function BirthForm({ onSubmit, buttonLabel }: Props) {
  const [values, setValues] = useState(defaultValues);
  const [loading, setLoading] = useState(false);

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    await onSubmit(values);
    setLoading(false);
  };

  return (
    <form onSubmit={submit}>
      {Object.keys(values).map((field) => (
        <input
          key={field}
          name={field}
          value={values[field as keyof typeof values]}
          onChange={(e) => setValues((prev) => ({ ...prev, [field]: e.target.value }))}
          placeholder={field}
          required
        />
      ))}
      <button type="submit" style={{ gridColumn: "1 / -1" }}>
        {loading ? "Analyzing planets..." : buttonLabel}
      </button>
    </form>
  );
}
