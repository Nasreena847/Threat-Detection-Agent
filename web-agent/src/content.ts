const getMetadata = () => {
  try {
    return {
      title: document.title || '',
      url: location.href || '',
      pageText: (document.body?.innerText || '').substring(0, 5000),
      forms: document.forms?.length ?? 0,
      scripts: document.scripts?.length ?? 0,
      passwordFields: document.querySelectorAll('input[type="password"]')?.length ?? 0,
      iframes: document.querySelectorAll('iframe')?.length ?? 0,
    }
  } catch (error) {
    console.error('Error collecting metadata:', error)
    return {
      title: document.title || '',
      url: location.href || '',
      pageText: '',
      forms: 0,
      scripts: 0,
      passwordFields: 0,
      iframes: 0,
    }
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  try {
    if (
      typeof message === 'object' &&
      message !== null &&
      'type' in message &&
      message.type === 'TRUSTTAB_PAGE_METADATA'
    ) {
      sendResponse(getMetadata())
      return true
    }
  } catch (error) {
    console.error('Error handling message:', error)
    sendResponse({ error: String(error) })
    return true
  }
})