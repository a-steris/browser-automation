// Listen for installation
chrome.runtime.onInstalled.addListener(function() {
  console.log('Stripe Invoice Downloader installed');
});

// Inject content script when needed
async function injectContentScript(tabId) {
  try {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ['content.js']
    });
    console.log('Content script injected successfully');
    return true;
  } catch (error) {
    console.error('Failed to inject content script:', error);
    return false;
  }
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Background received message:', message);

  if (message.action === 'ensureContentScript') {
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      try {
        // Check if we have any tabs
        if (!tabs || !tabs.length) {
          throw new Error('No active tab found');
        }

        // Check if tab has an ID
        if (!tabs[0].id) {
          throw new Error('Invalid tab');
        }

        // Check if we're on Stripe.com
        if (!tabs[0].url || !tabs[0].url.includes('stripe.com')) {
          throw new Error('Not on Stripe.com');
        }

        const success = await injectContentScript(tabs[0].id);
        if (!success) {
          throw new Error('Failed to inject content script');
        }

        sendResponse({ success: true });
      } catch (error) {
        console.error('Error in ensureContentScript:', error);
        sendResponse({ success: false, error: error.message });
      }
    });
    return true; // Will respond asynchronously
  }
});

// Listen for tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url?.includes('stripe.com')) {
    injectContentScript(tabId);
  }
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.action === 'downloadStarted') {
    // Could add notification or other feedback here
    console.log('Invoice download started');
  }
});
