const number = new Intl.NumberFormat("en");

export function amount(value: number): string {
  return number.format(value);
}

/** A budget change with its sign, e.g. "+200" or "−100". */
export function signedAmount(value: number): string {
  if (value > 0) return `+${number.format(value)}`;
  if (value < 0) return `−${number.format(-value)}`;
  return "0";
}
