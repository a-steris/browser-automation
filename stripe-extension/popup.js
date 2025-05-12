document.addEventListener('DOMContentLoaded', function() {
  const downloadButton = document.getElementById('downloadInvoices');
  const statusBox = document.getElementById('statusBox');

  function updateStatus(message, type = 'info') {
    statusBox.textContent = message;
    statusBox.className = `status-box ${type}`;
  }

  // Check if we're on Stripe.com and ensure content script
  chrome.tabs.query({active: true, currentWindow: true}, async function(tabs) {
    // First check if we have any tabs
    if (!tabs || !tabs.length) {
      downloadButton.disabled = true;
      updateStatus('Error: No active tab found', 'error');
      return;
    }

    // Then check if we're on Stripe.com
    if (!tabs[0].url || !tabs[0].url.includes('stripe.com')) {
      downloadButton.disabled = true;
      updateStatus('Please navigate to Stripe.com to use this extension', 'error');
      return;
    }

    // Ensure content script is loaded
    chrome.runtime.sendMessage({ action: 'ensureContentScript' }, function(response) {
      if (!response?.success) {
        downloadButton.disabled = true;
        updateStatus('Error: Could not initialize extension', 'error');
        return;
      }
      updateStatus('Ready to download invoices', 'success');
    });
  });

  downloadButton.addEventListener('click', async function() {
    try {
      // Get the active tab
      const tabs = await new Promise(resolve => chrome.tabs.query({active: true, currentWindow: true}, resolve));
      if (!tabs[0]?.id) {
        throw new Error('No active tab found');
      }

      // Check if we're on the invoices page
      if (!tabs[0].url?.includes('/invoices')) {
        const result = confirm('You need to be on the invoices page to download invoices.\n\nClick OK to navigate to the invoices page, or Cancel to stay here.');
        if (!result) {
          updateStatus('Navigation cancelled', 'error');
          return;
        }
      }

      downloadButton.disabled = true;
      updateStatus('Starting download process...');

      // Ensure content script is loaded
      const scriptResponse = await new Promise(resolve => {
        chrome.runtime.sendMessage({ action: 'ensureContentScript' }, resolve);
      });
      if (!scriptResponse?.success) {
        throw new Error('Could not initialize extension');
      }

      // Send download message
      console.log('Sending download message to tab:', tabs[0].id);
      const response = await new Promise((resolve, reject) => {
        chrome.tabs.sendMessage(tabs[0].id, { action: 'downloadInvoices' }, response => {
          if (chrome.runtime.lastError) {
            reject(chrome.runtime.lastError);
          } else {
            resolve(response);
          }
        });
      });

      console.log('Received response:', response);
      if (!response) {
        throw new Error('No response from content script');
      }

      if (response.success) {
        updateStatus(response.message || 'Download started!', 'success');
        // Re-enable button after 3 seconds
        setTimeout(() => {
          downloadButton.disabled = false;
          updateStatus('Ready to download invoices', 'success');
        }, 3000);
      } else {
        throw new Error(response.error || 'Unknown error');
      }

    } catch (error) {
      console.error('Error:', error);
      updateStatus('Error: ' + error.message, 'error');
      downloadButton.disabled = false;
    }
  });
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.action === 'updateStatus') {
    const statusBox = document.getElementById('statusBox');
    if (statusBox) {
      statusBox.textContent = request.message;
      statusBox.className = `status-box ${request.type || 'info'}`;
    }
  }
});
