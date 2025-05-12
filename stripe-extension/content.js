// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Received message:', request);
  
  if (request.action === 'downloadInvoices') {
    downloadInvoices()
      .then(result => {
        console.log('Download result:', result);
        sendResponse(result);
      })
      .catch(error => {
        console.error('Download error:', error);
        sendResponse({ success: false, error: error.message });
      });
    return true; // Will respond asynchronously
  }
  
  // Send immediate response for unknown actions
  sendResponse({ success: false, error: 'Unknown action' });
  return false;
});

function showNotification(message, type = 'info') {
  // Remove existing notification if any
  const existingNotification = document.querySelector('.stripe-invoice-downloader-notification');
  if (existingNotification) {
    existingNotification.remove();
  }

  // Create notification element
  const notification = document.createElement('div');
  notification.className = `stripe-invoice-downloader-notification ${type}`;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 24px;
    background: ${type === 'error' ? '#fee2e2' : '#ecfdf5'};
    border: 1px solid ${type === 'error' ? '#fca5a5' : '#6ee7b7'};
    color: ${type === 'error' ? '#dc2626' : '#059669'};
    border-radius: 6px;
    z-index: 9999;
    font-family: system-ui, -apple-system, sans-serif;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  `;
  notification.textContent = message;

  document.body.appendChild(notification);

  // Remove notification after 5 seconds
  setTimeout(() => notification.remove(), 5000);
}

// Function to ensure we're on the correct page
async function ensureInvoicesPage() {
  if (!window.location.href.includes('/invoices')) {
    showNotification('Navigating to invoices page...');
    window.location.href = 'https://dashboard.stripe.com/invoices';
    return false;
  }
  return true;
}

// Function to wait for page load after navigation
async function waitForPageLoad() {
  await new Promise(resolve => {
    if (document.readyState === 'complete') {
      resolve();
    } else {
      window.addEventListener('load', resolve);
    }
  });
  // Additional wait to ensure JS frameworks have initialized
  await new Promise(resolve => setTimeout(resolve, 2000));
}

async function downloadInvoices() {
  try {
    // Ensure we're on the invoices page
    if (!window.location.href.includes('/invoices')) {
      showNotification('Navigating to invoices page...');
      window.location.href = 'https://dashboard.stripe.com/invoices';
      // Wait for navigation and page load
      await new Promise(resolve => {
        window.addEventListener('load', resolve, { once: true });
      });
      await new Promise(resolve => setTimeout(resolve, 3000)); // Wait for page to stabilize
    }
    
    // Wait for page load
    await new Promise(resolve => {
      if (document.readyState === 'complete') {
        resolve();
      } else {
        window.addEventListener('load', resolve);
      }
    });
    
    // Additional wait to ensure JS frameworks have initialized
    await new Promise(resolve => setTimeout(resolve, 2000));

    showNotification('Looking for export button...');

    // Wait for the export button with retries
    const openModalButton = await waitForElement(
      '[data-testid="export-modal-button"]',
      5, // 5 attempts
      20000 // 20 second timeout per attempt
    );

    showNotification('Found export button, starting download...');
    
    // Click the export button and wait for modal
    openModalButton.click();
    showNotification('Waiting for export modal...');
    
    await findAndClickExportButton();
    console.log('Export button clicked successfully');
    
    // Wait longer for the download to initialize
    showNotification('Waiting for download to start...');
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    showNotification('Download started successfully!', 'success');
    console.log('Download process completed');

    // Wait a bit more to ensure download has started
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Refresh the page
    console.log('Refreshing page...');
    showNotification('Refreshing page...');
    window.location.reload();

    return { success: true };
  } catch (error) {
    console.error('Error downloading invoices:', error);
    showNotification(error.message, 'error');
    return { success: false, error: error.message };
  }
}

// Function to wait for an element using XPath
async function waitForElementXPath(xpath, maxAttempts = 10, timeout = 10000) {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const start = Date.now();
      
      while (Date.now() - start < timeout) {
        const element = document.evaluate(
          xpath,
          document,
          null,
          XPathResult.FIRST_ORDERED_NODE_TYPE,
          null
        ).singleNodeValue;

        if (element && element.offsetParent !== null) { // Check if element is visible
          return element;
        }
        await new Promise(resolve => setTimeout(resolve, 500)); // Increased polling interval
      }
      
      console.log(`Attempt ${attempt}: Element not found, retrying...`);
      // Wait between attempts
      await new Promise(resolve => setTimeout(resolve, 1000));
      
    } catch (error) {
      console.error(`Attempt ${attempt} failed:`, error);
    }
  }
  
  throw new Error(`Element with XPath ${xpath} not found after ${maxAttempts} attempts`);
}

// Function to find and click the export button in the modal
async function findAndClickExportButton() {
  showNotification('Waiting for modal to fully load...');
  
  // Wait longer for modal to fully render
  await new Promise(resolve => setTimeout(resolve, 3000));

  console.log('Scanning page for export button...');

  // Log all buttons and their text content
  const allButtons = document.querySelectorAll('button, [role="button"]');
  console.log('All clickable elements found:', allButtons.length);
  allButtons.forEach((btn, index) => {
    console.log(`Element ${index}:`, {
      text: btn.textContent,
      type: btn.tagName,
      role: btn.getAttribute('role'),
      visible: btn.offsetParent !== null,
      classes: btn.className
    });
  });

  // Try multiple methods to find the export button
  const methods = [
    // Method 1: By XPath
    async () => {
      const xpath = '//*[@id="merch"]/div[5]/div[3]/div/span[2]/div/div/div/div/div[3]/div/div/div/div[2]/div/div[1]/button';
      const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
      console.log('XPath method result:', result);
      return result;
    },
    // Method 2: By text content (case insensitive)
    async () => {
      const buttons = Array.from(document.querySelectorAll('button'));
      console.log('Searching through', buttons.length, 'buttons');
      const found = buttons.find(btn => {
        const hasExport = btn.textContent.toLowerCase().includes('export');
        const isVisible = btn.offsetParent !== null;
        console.log('Button text:', btn.textContent, 'hasExport:', hasExport, 'isVisible:', isVisible);
        return hasExport && isVisible;
      });
      return found;
    },
    // Method 3: By role and text
    async () => {
      const elements = Array.from(document.querySelectorAll('[role="button"]'));
      console.log('Searching through', elements.length, 'elements with role=button');
      return elements.find(el => el.textContent.toLowerCase().includes('export') && el.offsetParent !== null);
    },
    // Method 4: By class name containing 'export'
    async () => {
      const elements = Array.from(document.querySelectorAll('*'));
      return elements.find(el => {
        const hasExportClass = el.className.toLowerCase().includes('export');
        const isVisible = el.offsetParent !== null;
        const isClickable = el.tagName === 'BUTTON' || el.getAttribute('role') === 'button';
        return hasExportClass && isVisible && isClickable;
      });
    }
  ];

  // Try each method until we find the button
  let exportButton = null;
  for (const method of methods) {
    try {
      exportButton = await method();
      if (exportButton) {
        console.log('Found export button using method:', method.toString());
        break;
      }
    } catch (error) {
      console.log('Method failed:', error);
    }
  }

  if (!exportButton) {
    throw new Error('Could not find Export button using any method');
  }

  // Log button details
  console.log('Export button found:', {
    text: exportButton.textContent,
    visible: exportButton.offsetParent !== null,
    disabled: exportButton.disabled,
    classes: exportButton.className,
    tagName: exportButton.tagName
  });

  showNotification('Found export button, attempting to click...');
  exportButton.click();
  
  // Wait for export to process
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Look for the Close button or link
  console.log('Looking for Close button...');
  
  // Try to find any element (button, link, or div) with 'Close' text
  const closeElements = Array.from(document.querySelectorAll('button, a, div[role="button"]'));
  console.log('Found potential close elements:', closeElements.length);
  
  closeElements.forEach((el, i) => {
    console.log(`Element ${i}:`, {
      text: el.textContent,
      tag: el.tagName,
      classes: el.className,
      visible: el.offsetParent !== null
    });
  });

  const closeButton = closeElements.find(el => {
    const hasCloseText = el.textContent.toLowerCase().includes('Close');
    const isVisible = el.offsetParent !== null;
    return hasCloseText && isVisible;
  });

  if (closeButton) {
    console.log('Found Close element:', {
      text: closeButton.textContent,
      tag: closeButton.tagName,
      classes: closeButton.className
    });
    closeButton.click();
    await new Promise(resolve => setTimeout(resolve, 1000));
  } else {
    console.log('Close button/link not found');
  }
}

// Function to wait for an element to appear with retries
async function waitForElement(selector, maxAttempts = 10, timeout = 10000) {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const start = Date.now();
      
      while (Date.now() - start < timeout) {
        const element = document.querySelector(selector);
        if (element && element.offsetParent !== null) { // Check if element is visible
          return element;
        }
        await new Promise(resolve => setTimeout(resolve, 500)); // Increased polling interval
      }
      
      console.log(`Attempt ${attempt}: Element not found, retrying...`);
      // Wait between attempts
      await new Promise(resolve => setTimeout(resolve, 1000));
      
    } catch (error) {
      console.error(`Attempt ${attempt} failed:`, error);
    }
  }
  
  throw new Error(`Element ${selector} not found after ${maxAttempts} attempts`);
}
