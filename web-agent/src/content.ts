const AD_SELECTOR = [
  'ins.adsbygoogle',
  'iframe[src*="doubleclick"]',
  'iframe[src*="googlesyndication"]',
  'iframe[src*="adservice"]',
  'iframe[src*="/ads"]',
  'iframe[id*="ad"]',
  'iframe[class*="ad"]',
  '[data-ad]',
  '[data-ad-slot]',
  '[data-ad-client]',
  '[data-google-query-id]',
  '[id^="ad-"]',
  '[id*="-ad-"]',
  '[id*="ads"]',
  '[class~="ad"]',
  '[class*=" ad-"]',
  '[class*="-ad "]',
  '[class*="ads"]',
  '[class*="advert"]',
  '[class*="sponsor"]',
  '[class*="promo"]',
  '[aria-label*="advertisement" i]',
].join(',')

const wait = (milliseconds: number) =>
  new Promise((resolve) => {
    window.setTimeout(resolve, milliseconds)
  })

const AD_ATTRIBUTE_PATTERN = /(^|[-_\s])(ad|ads|advert|advertisement|sponsored|sponsor|promo)([-_\s]|$)/i

const countAds = () => {
  const elements = new Set<Element>()
  document.querySelectorAll(AD_SELECTOR).forEach((element) => elements.add(element))
  document
    .querySelectorAll('iframe, ins, aside, [id], [class], [aria-label], [data-ad], [data-ad-slot], [data-ad-client]')
    .forEach((element) => {
      const candidate = [
        element.id,
        element.className,
        element.getAttribute('aria-label'),
        element.getAttribute('src'),
        element.getAttribute('data-ad'),
        element.getAttribute('data-ad-slot'),
        element.getAttribute('data-ad-client'),
      ]
        .filter(Boolean)
        .join(' ')

      if (AD_ATTRIBUTE_PATTERN.test(candidate)) {
        elements.add(element)
      }
    })

  return elements.size
}

const getMetadata = async () => {
  try {
    await wait(document.readyState === 'complete' ? 500 : 900)

    return {
      title: document.title || '',
      url: location.href || '',
      pageText: (document.body?.innerText || '').substring(0, 5000),
      forms: document.forms?.length ?? 0,
      scripts: document.scripts?.length ?? 0,
      passwordFields: document.querySelectorAll('input[type="password"]')?.length ?? 0,
      iframes: document.querySelectorAll('iframe')?.length ?? 0,
      ads: countAds(),
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
      ads: 0,
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
      void getMetadata().then(sendResponse).catch((error) => {
        console.error('Error collecting metadata:', error)
        sendResponse({ error: String(error) })
      })
      return true
    }
  } catch (error) {
    console.error('Error handling message:', error)
    sendResponse({ error: String(error) })
    return true
  }
})
