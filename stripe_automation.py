from playwright.sync_api import sync_playwright
import time
import os
import random
from datetime import datetime
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless

class StripeHandler:
    def __init__(self, email, password, anticaptcha_key=None):
        self.email = email
        self.password = password
        self.anticaptcha_key = anticaptcha_key
        self.download_dir = os.path.join(os.getcwd(), 'downloads')
        os.makedirs(self.download_dir, exist_ok=True)
        
    def _solve_captcha(self, page):
        """Solve reCAPTCHA if present using anti-captcha.com"""
        try:
            # Check if captcha is present
            captcha_frame = page.locator('iframe[title*="recaptcha"]')
            if captcha_frame.count() == 0:
                return True
                
            if not self.anticaptcha_key:
                print("Captcha detected but no anti-captcha key provided")
                return False
                
            # Get the site key
            site_key = page.evaluate('''() => {
                const iframe = document.querySelector('iframe[title*="recaptcha"]');
                return iframe.getAttribute('src').match(/k=([^&]*)/)[1];
            }''')
            
            solver = recaptchaV2Proxyless()
            solver.set_verbose(1)
            solver.set_key(self.anticaptcha_key)
            solver.set_website_url(page.url)
            solver.set_website_key(site_key)
            
            # Solve captcha
            response = solver.solve_and_return_solution()
            if response:
                # Input the solution
                page.evaluate(f'document.getElementById("g-recaptcha-response").innerHTML = "{response}";')
                return True
                
            return False
        except Exception as e:
            print(f"Error solving captcha: {str(e)}")
            return False
    
    def sync_and_download_invoices(self):
        """Download invoices from Stripe Dashboard using browser automation"""
        with sync_playwright() as p:
            # Launch browser with enhanced stealth mode
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials'
                ]
            )
            
            # Configure browser context with realistic properties
            context = browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/Los_Angeles',
                permissions=['geolocation'],
                color_scheme='light',
            )
            
            # Add comprehensive stealth scripts
            context.add_init_script("""
                // Override automation-related properties
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                
                // Add missing chrome properties
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Add plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [{
                        0: {
                            type: 'application/x-google-chrome-pdf',
                            suffixes: 'pdf',
                            description: 'Portable Document Format',
                            enabledPlugin: true
                        },
                        description: 'Chrome PDF Plugin',
                        filename: 'internal-pdf-viewer',
                        length: 1,
                        name: 'Chrome PDF Plugin'
                    }]
                });
            """)
            
            # Create a new page
            page = context.new_page()
            
            try:
                # Go to Stripe login page
                print("Navigating to Stripe login...")
                page.goto('https://dashboard.stripe.com/login')
                
                # Wait for the login form and fill credentials
                print("Logging in...")
                # Add more human-like behavior before typing
                page.wait_for_timeout(random.randint(500, 1500))  # Random initial wait
                
                # Move mouse to email field naturally
                email_field = page.locator('input[name="email"]')
                email_field.hover()
                page.wait_for_timeout(random.randint(100, 300))
                email_field.click()
                
                # Type email with realistic delays
                for char in self.email:
                    page.type('input[name="email"]', char)
                    time.sleep(random.uniform(0.1, 0.4))
                
                # Move mouse to password field naturally
                page.wait_for_timeout(random.randint(300, 700))
                password_field = page.locator('input[name="password"]')
                password_field.hover()
                page.wait_for_timeout(random.randint(100, 300))
                password_field.click()
                
                # Type password with realistic delays
                for char in self.password:
                    page.type('input[name="password"]', char)
                    time.sleep(random.uniform(0.1, 0.4))
                
                # Handle captcha if present
                if not self._solve_captcha(page):
                    raise Exception("Failed to solve captcha")
                    
                page.click('button[type="submit"]')
                
                # Wait for either dashboard or error message
                print("Waiting for page to load after login...")
                try:
                    # First check for any error messages
                    error_selector = 'text=Invalid email or password, text=Authentication failed'
                    has_error = page.wait_for_selector(error_selector, timeout=5000, state='visible')
                    if has_error:
                        raise Exception("Invalid email or password")
                except:
                    # No error found, wait for dashboard
                    try:
                        print("Waiting for dashboard to load...")
                        # Wait for any of these common dashboard elements
                        success = False
                        for selector in [
                            '.Dashboard',  # Classic dashboard
                            '.dashboard',  # Modern dashboard
                            '[data-testid="nav-sidebar"]',  # Nav sidebar
                            '[data-testid="main-header"]',  # Main header
                            '.db-NavHeader',  # Another dashboard header variant
                            '.nav-header'  # Yet another variant
                        ]:
                            try:
                                page.wait_for_selector(selector, timeout=10000)
                                success = True
                                break
                            except:
                                continue
                        
                        if not success:
                            raise Exception("Could not detect dashboard elements")
                            
                    except Exception as e:
                        print("Dashboard not found. Checking for 2FA...")
                        # Check if we're on 2FA page
                        if page.url.find('2fa') != -1 or page.url.find('mfa') != -1:
                            raise Exception("2FA required - please disable 2FA on your Stripe account first")
                        raise Exception(f"Login failed: {str(e)}")
                
                # Navigate to Invoices page
                print("Navigating to Invoices...")
                try:
                    # Try modern dashboard invoice link
                    page.click('[data-testid="nav-link-invoices"], a[href*="/invoices"]')
                    # Wait for invoice list with multiple possible selectors
                    success = False
                    for selector in ['.InvoicesList', '[data-testid="invoice-list"]', '.db-InvoiceList']:
                        try:
                            page.wait_for_selector(selector, timeout=10000)
                            success = True
                            break
                        except:
                            continue
                            
                    if not success:
                        raise Exception("Could not find invoice list")
                except Exception as e:
                    raise Exception(f"Failed to navigate to invoices: {str(e)}")
                
                # Set date range to All time
                print("Setting date range...")
                page.click('button[data-testid="date-range-trigger"]')
                page.click('text=All time')
                page.wait_for_load_state('networkidle')
                
                # Click Export button
                print("Starting export...")
                page.click('button:has-text("Export")')
                
                # Wait for download to start
                print("Waiting for download...")
                download = page.wait_for_download()
                
                # Save the file with current timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                download_path = os.path.join(self.download_dir, f'stripe_invoices_{timestamp}.csv')
                download.save_as(download_path)
                
                print(f"Download completed: {download_path}")
                return download_path
                
            except Exception as e:
                print(f"Error during automation: {str(e)}")
                raise
                
            finally:
                # Close browser
                browser.close()

if __name__ == "__main__":
    # Get credentials from environment variables
    email = os.getenv('STRIPE_EMAIL')
    password = os.getenv('STRIPE_PASSWORD')
    
    if not email or not password:
        print("Please set STRIPE_EMAIL and STRIPE_PASSWORD environment variables")
        exit(1)
    
    try:
        handler = StripeHandler(email, password)
        download_path = handler.sync_and_download_invoices()
        print(f"Successfully downloaded invoices to: {download_path}")
    except Exception as e:
        print(f"Failed to download invoices: {str(e)}")
