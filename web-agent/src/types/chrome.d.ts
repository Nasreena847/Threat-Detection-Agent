type ChromeTab = {
  id?: number
  title?: string
  url?: string
  favIconUrl?: string
}

type ChromeTabChangeInfo = {
  status?: 'loading' | 'complete'
}

type ChromeQueryInfo = {
  active?: boolean
  currentWindow?: boolean
}

type ChromeMessageSender = Record<string, unknown>

type ChromeSendResponse = (response?: unknown) => void

declare const chrome: {
  runtime: {
    getURL(path: string): string
    onInstalled: {
      addListener(callback: () => void): void
    }
    onMessage: {
      addListener(
        callback: (
          message: unknown,
          sender: ChromeMessageSender,
          sendResponse: ChromeSendResponse,
        ) => void,
      ): void
    }
  }
  storage: {
    local: {
      get(keys?: string | string[] | Record<string, unknown> | null): Promise<Record<string, unknown>>
      set(items: Record<string, unknown>): Promise<void>
    }
  }
  tabs: {
    query(queryInfo: ChromeQueryInfo): Promise<ChromeTab[]>
    sendMessage(tabId: number, message: unknown): Promise<unknown>
    create(createProperties: { url: string }): Promise<ChromeTab>
    onUpdated: {
      addListener(callback: (tabId: number, changeInfo: ChromeTabChangeInfo, tab: ChromeTab) => void): void
    }
  }
}
