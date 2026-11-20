// All interface text comes from translation files. English only for now;
// Norwegian (bokmål) is added later as another file with the same keys.

import en from "./en.json";

export type MessageKey = keyof typeof en;

const messages: Record<MessageKey, string> = en;

/** The text for `key`, with `{name}` placeholders filled from `values`. */
export function t(key: MessageKey, values: Record<string, string | number> = {}): string {
  return messages[key].replace(/\{(\w+)\}/g, (match, name: string) =>
    name in values ? String(values[name]) : match,
  );
}
