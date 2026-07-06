chrome.runtime.onInstalled.addListener(() => {
  void chrome.storage.local.set({
    trusttabInstalledAt: new Date().toISOString(),
  })
})
