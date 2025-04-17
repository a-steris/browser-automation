import os
import time
import random
from datetime import datetime, timedelta
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

class StripeReportDownloader:
    def __init__(self):
        print("Initializing Stripe Report Downloader...")
        load_dotenv()
        self.email = os.getenv('STRIPE_EMAIL')
        self.password = os.getenv('STRIPE_PASSWORD')
        
        if not self.email or not self.password:
            raise ValueError("Please set STRIPE_EMAIL and STRIPE_PASSWORD in .env file")
        
        # Setup Chrome options with a custom profile
        options = uc.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Set up custom profile preferences
        prefs = {
            "download.default_directory": os.path.join(os.getcwd(), "downloads"),
            "download.prompt_for_download": False,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.images": 1,
            "profile.default_content_setting_values.cookies": 1
        }
        options.add_experimental_option("prefs", prefs)
        
        # Add additional options to make the browser more realistic
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        
        # Initialize custom Chrome instance
        print("Initializing undetected Chrome WebDriver with custom profile...")
        try:
            self.driver = uc.Chrome(
                options=options,
                headless=False
            )
        except Exception as e:
            if "Current browser version is" in str(e):
                # Extract version from error message
                version = str(e).split("Current browser version is ")[1].split(".")[0]
                print(f"Detected Chrome version: {version}, retrying with correct version...")
                self.driver = uc.Chrome(
                    options=options,
                    headless=False,
                    version_main=int(version)
                )
            else:
                raise e
        print("Chrome WebDriver initialized successfully")
        
        # Create downloads directory if it doesn't exist
        os.makedirs("downloads", exist_ok=True)

    def verify_page(self):
        """Debug helper to verify page state"""
        print("\nCurrent URL:", self.driver.current_url)
        print("Page title:", self.driver.title)
        print("\nChecking for email field...")
        try:
            email = self.driver.find_element(By.NAME, "email")
            print("Email field found")
        except:
            print("Email field not found")
        
        print("\nChecking for password field...")
        try:
            password = self.driver.find_element(By.NAME, "password")
            print("Password field found")
        except:
            print("Password field not found")
        
        print("\nChecking for submit button...")
        try:
            submit = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            print("Submit button found")
        except:
            print("Submit button not found")
        
        print("\nPage source preview:")
        print(self.driver.page_source[:500])
    
    def human_like_type(self, element, text):
        """Type text in a human-like manner with random delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
        time.sleep(random.uniform(0.5, 1.0))

    def move_to_element_with_offset(self, element):
        """Move to element with random offset to simulate human movement"""
        action = ActionChains(self.driver)
        rect = element.rect
        offset_x = random.randint(3, int(rect['width']-3))
        offset_y = random.randint(3, int(rect['height']-3))
        action.move_to_element_with_offset(element, offset_x, offset_y)
        action.perform()
        time.sleep(random.uniform(0.5, 1.0))

    def is_security_check_present(self):
        """Check if we're on a security verification page"""
        security_indicators = [
            "security check",
            "verify your identity",
            "confirm it's you",
            "verification required",
            "captcha",
            "prove you're human"
        ]
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            return any(indicator in page_text for indicator in security_indicators)
        except:
            return False

    def wait_for_page_load(self):
        """Wait for page to be fully loaded"""
        try:
            # Wait for document.readyState to be complete
            WebDriverWait(self.driver, 20).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(2)  # Additional wait for any dynamic content
            
            # Check for security verification
            if self.is_security_check_present():
                print("\nSecurity verification detected!")
                print("Please complete the security check manually.")
                print("The script will continue once verification is complete.")
        except Exception as e:
            print(f"Warning: Page load wait failed: {str(e)}")

    def wait_and_find_element(self, selectors, timeout=20):
        """Wait for and find an element using multiple selectors with enhanced error handling"""
        start_time = time.time()
        last_exception = None
        while time.time() - start_time < timeout:
            for selector_type, selector_value in selectors:
                try:
                    # First check if element exists in DOM
                    elements = self.driver.find_elements(selector_type, selector_value)
                    if not elements:
                        continue

                    # Then check if it's visible and enabled
                    element = elements[0]
                    if element.is_displayed() and element.is_enabled():
                        # Try to scroll element into view
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(0.5)
                        return element
                except Exception as e:
                    last_exception = e
                    continue
            time.sleep(0.5)
        
        # If we get here, element wasn't found
        error_msg = f"Could not find element with selectors: {selectors}"
        if last_exception:
            error_msg += f". Last error: {str(last_exception)}"
        raise Exception(error_msg)

    def wait_for_user_action(self, message, timeout=300):
        """Wait for user to complete an action"""
        print(f"\n{message}")
        print(f"You have {timeout//60} minutes to complete this action.")
        print("Press Enter in the terminal when you're ready to continue...")
        
        try:
            input()
        except:
            pass

    def login(self):
        """Simple login to Stripe Dashboard"""
        try:
            print("Navigating to Stripe login page...")
            self.driver.get("https://dashboard.stripe.com/login")
            time.sleep(2)
            
            # Find and fill email field
            print("Entering email...")
            email_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='email']")
            email_input.clear()
            email_input.send_keys(self.email)
            time.sleep(1)
            
            # Find and fill password field
            print("Entering password...")
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(1)
            
            # Click login button
            print("Clicking sign in...")
            sign_in_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            sign_in_button.click()
            
            # Wait for successful login (up to 5 minutes)
            print("\nWaiting for successful login...")
            timeout = time.time() + 300  # 5 minutes
            while time.time() < timeout:
                try:
                    # Check for dashboard elements
                    for selector in [".nav-business-name", ".nav-header__logo", "a[href*='/dashboard']"]:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if element.is_displayed():
                            print("Successfully logged in to Stripe dashboard!")
                            return True
                    time.sleep(1)
                except:
                    time.sleep(1)
                    
                # Check if still on login page
                if "login" not in self.driver.current_url.lower():
                    print("Successfully logged in to Stripe dashboard!")
                    return True
            
            print("\nLogin timeout - please try again")
            return False
            
        except Exception as e:
            print(f"\nError during login process: {str(e)}")
            return False

    def download_payout_report(self):
        """Navigate to and download the payout report"""
        try:
            # Navigate to Balance page
            self.driver.get("https://dashboard.stripe.com/balance/overview")
            time.sleep(3)  # Allow page to load
            
            # Click on Export button
            export_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test='export-button']"))
            )
            export_button.click()
            
            # Wait for export modal
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".Modal"))
            )
            
            # Select date range (last 30 days)
            date_selector = self.driver.find_element(By.CSS_SELECTOR, "[data-test='date-range-selector']")
            date_selector.click()
            
            last_30_days = self.driver.find_element(By.CSS_SELECTOR, "[data-test='last-30-days']")
            last_30_days.click()
            
            # Click download button
            download_button = self.driver.find_element(By.CSS_SELECTOR, "[data-test='download-report-button']")
            download_button.click()
            
            # Wait for download to complete
            time.sleep(5)
            print("Payout report downloaded successfully")
            return True
            
        except Exception as e:
            print(f"Failed to download payout report: {str(e)}")
            return False

    def cleanup(self):
        """Close the browser"""
        self.driver.quit()

def main():
    downloader = StripeReportDownloader()
    try:
        if downloader.login():
            downloader.download_payout_report()
    finally:
        downloader.cleanup()

if __name__ == "__main__":
    main()
