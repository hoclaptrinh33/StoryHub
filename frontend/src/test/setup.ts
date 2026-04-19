import { afterEach, vi } from "vitest";

// Reset spies and timers so polling/reconnect tests remain isolated.
afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});
