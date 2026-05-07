import time
import streamlit as st
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class LinkedInBot:
    """Assistant for semi-automated LinkedIn job applications"""
    
    def __init__(self, driver, profile):
        self.driver = driver
        self.profile = profile
        self.wait = WebDriverWait(self.driver, 10)

    def login(self):
        """Log in to LinkedIn using profile credentials"""
        try:
            email = self.profile.get('li_email')
            password = self.profile.get('li_password')
            
            if not email or not password:
                st.warning("LinkedIn credentials missing in profile. Please add them in the 'My Profile' tab.")
                return False
                
            st.info("Logging in to LinkedIn...")
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)
            
            # Fill username
            username_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_field.send_keys(email)
            
            # Fill password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(password)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            time.sleep(5)
            
            # Check for verification (Security Check)
            if "checkpoint" in self.driver.current_url:
                st.error("LinkedIn requested a Security Check/Captcha. Please resolve it in the browser window or try logging in manually first.")
                return False
                
            return True
        except Exception as e:
            st.error(f"Login failed: {str(e)}")
            return False

    def fill_easy_apply(self, job_url):
        """Attempt to fill out a LinkedIn Easy Apply form"""
        try:
            # First, attempt to login if not already
            if not self.login():
                return False
                
            self.driver.get(job_url)
            time.sleep(3)
            
            # 1. Look for the Easy Apply button
            try:
                apply_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".jobs-apply-button")))
                apply_button.click()
                st.info("Initiated Easy Apply...")
            except TimeoutException:
                st.error("Could not find an active Easy Apply button on this page. Make sure you are logged in to LinkedIn in this session.")
                return False

            # 2. Iterate through form steps
            max_steps = 10
            for step in range(max_steps):
                time.sleep(2)
                
                # Check for common fields and fill them
                self._fill_common_fields()
                
                # Look for 'Next', 'Review', or 'Submit' buttons
                button_selectors = [
                    "button[aria-label='Continue to next step']",
                    "button[aria-label='Review your application']",
                    "button[aria-label='Submit application']"
                ]
                
                button_found = False
                for selector in button_selectors:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if buttons and buttons[0].is_displayed():
                        # If it's a submit button, we let the user click it manually for safety
                        if 'Submit' in buttons[0].text or 'Submit' in buttons[0].get_attribute('aria-label'):
                            st.success("🎉 Forms pre-filled! Please review and click 'Submit' yourself.")
                            return True
                        
                        buttons[0].click()
                        button_found = True
                        st.info(f"Completed step {step+1}...")
                        break
                
                if not button_found:
                    # Check if we are stuck on a question we can't answer
                    st.warning("Manual input required for this step. Please check the browser window.")
                    break
                    
            return True
            
        except Exception as e:
            st.error(f"Application Assistant encountered an error: {str(e)}")
            return False

    def _fill_common_fields(self):
        """Detect and fill common LinkedIn form fields"""
        # Map profile keys to possible field identifiers
        field_mappings = {
            'full_name': ['name', 'fullname', 'first'],
            'email': ['email'],
            'phone': ['phone', 'mobile', 'contact'],
            'location': ['location', 'city', 'address']
        }
        
        # Look for input fields
        inputs = self.driver.find_elements(By.TAG_NAME, "input")
        for inp in inputs:
            try:
                name = (inp.get_attribute('name') or '').lower()
                id_attr = (inp.get_attribute('id') or '').lower()
                label = (inp.get_attribute('aria-label') or '').lower()
                
                # Only fill if empty
                if inp.get_attribute('value'):
                    continue
                
                for key, patterns in field_mappings.items():
                    if any(p in name or p in id_attr or p in label for p in patterns):
                        val = self.profile.get(key, '')
                        if val:
                            inp.send_keys(val)
                            break
            except:
                continue
