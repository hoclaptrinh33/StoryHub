const PREFIX = '[StoryHub Frontend]'
const isDevMode = import.meta.env.DEV

function prefixed(message: string): string {
  return `${PREFIX} ${message}`
}

function logWithPayload(
  loggerFn: (message?: unknown, ...optionalParams: unknown[]) => void,
  message: string,
  payload?: unknown,
): void {
  if (payload === undefined) {
    loggerFn(prefixed(message))
    return
  }
  loggerFn(prefixed(message), payload)
}

export const logger = {
  debug(message: string, payload?: unknown): void {
    if (!isDevMode) {
      return
    }
    logWithPayload(console.debug, message, payload)
  },

  info(message: string, payload?: unknown): void {
    logWithPayload(console.info, message, payload)
  },

  warn(message: string, payload?: unknown): void {
    logWithPayload(console.warn, message, payload)
  },

  error(message: string, payload?: unknown): void {
    logWithPayload(console.error, message, payload)
  },
}
