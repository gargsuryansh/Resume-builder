import logging
import time
import numpy as np
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Import our custom webdriver utility
from .webdriver_utils import setup_webdriver

class LinkedInScraper:
    """Class for scraping job listings from LinkedIn"""

    @staticmethod
    def webdriver_setup():
        """Set up and configure the Chrome webdriver"""
        # Use our custom webdriver setup utility with multiple fallback options
        return setup_webdriver()

    @staticmethod
    def build_url(job_title, job_location):
        """Build LinkedIn search URL from job title and location"""
        # Format job titles
        formatted_titles = []
        for title in job_title:
            if title.strip():  # Skip empty titles
                words = title.strip().split()
                formatted_title = '%20'.join(words)
                formatted_titles.append(formatted_title)
        
        # If no valid titles, use a default
        if not formatted_titles:
            formatted_titles = ["jobs"]
        
        # Join multiple job titles
        job_title_param = '%2C%20'.join(formatted_titles)
        
        # Format location
        location_param = job_location.replace(' ', '%20')
        
        # Build the LinkedIn search URL
        link = f"https://in.linkedin.com/jobs/search?keywords={job_title_param}&location={location_param}&geoId=102713980&f_TPR=r604800&position=1&pageNum=0"
        
        return link

    @staticmethod
    def open_link(driver, link):
        """Open LinkedIn link and wait for page to load"""
        max_attempts = 3
        attempts = 0
        
        while attempts < max_attempts:
            try:
                driver.get(link)
                driver.implicitly_wait(5)
                time.sleep(3)
                
                # Check if page loaded correctly
                if "LinkedIn" in driver.title:
                    return True
                    
                # Alternative check for elements
                try:
                    driver.find_element(by=By.CSS_SELECTOR, value='.jobs-search-results')
                    return True
                except:
                    pass
                    
                try:
                    driver.find_element(by=By.CSS_SELECTOR, value='.jobs-search-results-list')
                    return True
                except:
                    pass
                
                # One more attempt with a different selector
                try:
                    driver.find_element(by=By.CSS_SELECTOR, value='.base-search-card')
                    return True
                except:
                    pass
                
                attempts += 1
                if attempts >= max_attempts:
                    logger.warning("Could not load LinkedIn jobs page. Please try again.")
                    return False
                    
                time.sleep(2)
                
            except Exception as e:
                attempts += 1
                if attempts >= max_attempts:
                    logger.warning("Error loading LinkedIn page: %s", e)
                    return False
                time.sleep(2)
                
        return False

    @staticmethod
    def link_open_scrolldown(driver, link, job_count):
        """Open LinkedIn link and scroll down to load more jobs"""
        # Open the link
        if not LinkedInScraper.open_link(driver, link):
            return False
        
        # Scroll down to load more jobs
        scroll_attempts = min(job_count + 5, 15)  # Add extra scrolls to ensure we get enough jobs
        
        for i in range(scroll_attempts):
            try:
                # Handle sign-in modal if it appears
                try:
                    dismiss_buttons = driver.find_elements(
                        by=By.CSS_SELECTOR, 
                        value="button[data-tracking-control-name='public_jobs_contextual-sign-in-modal_modal_dismiss']"
                    )
                    if dismiss_buttons:
                        dismiss_buttons[0].click()
                except:
                    pass
                
                # Scroll down to load more content
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                
                # Try to click "See more jobs" button if present
                try:
                    see_more_buttons = driver.find_elements(
                        by=By.CSS_SELECTOR, 
                        value="button[aria-label='See more jobs']"
                    )
                    if see_more_buttons:
                        see_more_buttons[0].click()
                        time.sleep(2)
                except:
                    pass
                
            except Exception as e:
                continue
        
        return True

    @staticmethod
    def job_title_filter(scrap_job_title, user_job_title_input):
        """Filter job titles based on user input"""
        # Skip filtering if job title input is empty or contains only empty strings
        if not user_job_title_input or all(not title.strip() for title in user_job_title_input):
            return scrap_job_title
        
        # User job titles converted to lowercase
        user_input = [title.lower().strip() for title in user_job_title_input if title.strip()]
        
        # If no valid user input after cleaning, return the original title
        if not user_input:
            return scrap_job_title
        
        # Scraped job title converted to lowercase
        scrap_title = scrap_job_title.lower().strip()
        
        # Check if any user job title matches the scraped job title
        for user_title in user_input:
            # Check if all words in user title are in scraped title
            if all(word in scrap_title for word in user_title.split()):
                return scrap_job_title
        
        # No match found
        return np.nan

    @staticmethod
    def scrap_company_data(driver, job_title_input, job_location):
        """Scrape company data from LinkedIn job listings"""
        try:
            # Scrape company names
            company_elements = driver.find_elements(
                by=By.CSS_SELECTOR, 
                value='h4.base-search-card__subtitle'
            )
            company_names = [element.text for element in company_elements if element.text.strip()]
            
            # Scrape job locations
            location_elements = driver.find_elements(
                by=By.CSS_SELECTOR, 
                value='span.job-search-card__location'
            )
            company_locations = [element.text for element in location_elements if element.text.strip()]
            
            # Scrape job titles
            title_elements = driver.find_elements(
                by=By.CSS_SELECTOR, 
                value='h3.base-search-card__title'
            )
            job_titles = [element.text for element in title_elements if element.text.strip()]
            
            # Scrape job URLs
            url_elements = driver.find_elements(
                by=By.XPATH, 
                value='//a[contains(@href, "/jobs/view/")]'
            )
            job_urls = [element.get_attribute('href') for element in url_elements if element.get_attribute('href')]
            
            # Check if we have any data
            if not company_names or not job_titles or not company_locations or not job_urls:
                logger.warning("No job listings found on LinkedIn. Try different search terms.")
                return pd.DataFrame()
            
            # Ensure all arrays have the same length by truncating to the shortest length
            min_length = min(len(company_names), len(job_titles), len(company_locations), len(job_urls))
            
            if min_length == 0:
                logger.warning("No job listings found on LinkedIn. Try different search terms.")
                return pd.DataFrame()
                
            company_names = company_names[:min_length]
            job_titles = job_titles[:min_length]
            company_locations = company_locations[:min_length]
            job_urls = job_urls[:min_length]
            
            # Create DataFrame
            df = pd.DataFrame({
                'Company Name': company_names,
                'Job Title': job_titles,
                'Location': company_locations,
                'Website URL': job_urls
            })
            
            # Filter job titles based on user input if provided
            if job_title_input and job_title_input != ['']:
                filtered_titles = []
                for title in df['Job Title']:
                    if any(user_title.lower().strip() in title.lower() for user_title in job_title_input if user_title.strip()):
                        filtered_titles.append(title)
                    else:
                        filtered_titles.append(np.nan)
                df['Job Title'] = filtered_titles
            
            # Filter locations based on user input if provided and not "India"
            if job_location and job_location.lower() != "india":
                filtered_locations = []
                for loc in df['Location']:
                    if job_location.lower() in loc.lower():
                        filtered_locations.append(loc)
                    else:
                        filtered_locations.append(np.nan)
                df['Location'] = filtered_locations
            
            # Drop rows with NaN values and reset index
            df = df.dropna()
            df = df.reset_index(drop=True)
            
            return df
            
        except Exception as e:
            logger.error("Error scraping company data: %s", e)
            return pd.DataFrame()

    @staticmethod
    def scrap_job_description(driver, df, job_count):
        """Scrape job descriptions for each job listing"""
        if df.empty:
            return df
        
        # Get job URLs
        job_urls = df['Website URL'].tolist()
        
        # Limit to requested job count
        job_urls = job_urls[:min(len(job_urls), job_count)]
        
        # Initialize list for job descriptions
        job_descriptions = []
        
        for i, url in enumerate(job_urls):
            try:
                logger.info("Scraping job description %s/%s", i + 1, len(job_urls))
                
                # Open job listing page
                driver.get(url)
                driver.implicitly_wait(5)
                time.sleep(2)
                
                # Try to click "Show more" button to expand job description
                try:
                    show_more_buttons = driver.find_elements(
                        by=By.CSS_SELECTOR, 
                        value='button[data-tracking-control-name="public_jobs_show-more-html-btn"]'
                    )
                    if show_more_buttons:
                        show_more_buttons[0].click()
                        time.sleep(1)
                except:
                    pass
                
                # Get job description
                description_elements = driver.find_elements(
                    by=By.CSS_SELECTOR, 
                    value='div.show-more-less-html__markup'
                )
                
                if description_elements and description_elements[0].text.strip():
                    description_text = description_elements[0].text
                    
                    # Process and structure the job description
                    processed_description = LinkedInScraper.process_job_description(description_text)
                    job_descriptions.append(processed_description)
                else:
                    # Try alternative selectors
                    alt_description = driver.find_elements(
                        by=By.CSS_SELECTOR, 
                        value='div.description__text'
                    )
                    if alt_description and alt_description[0].text.strip():
                        description_text = alt_description[0].text
                        processed_description = LinkedInScraper.process_job_description(description_text)
                        job_descriptions.append(processed_description)
                    else:
                        job_descriptions.append("Description not available")
                    
            except Exception as e:
                job_descriptions.append("Description not available")
                logger.warning("Error scraping job description %s: %s", i + 1, e)
        
        # Filter DataFrame to include only rows with descriptions
        df = df.iloc[:len(job_descriptions), :]
        
        # Add job descriptions to DataFrame
        df['Job Description'] = job_descriptions
        
        # Filter out rows with unavailable descriptions
        df['Job Description'] = df['Job Description'].apply(
            lambda x: np.nan if x == "Description not available" else x
        )
        df = df.dropna()
        df = df.reset_index(drop=True)
        
        return df

    @staticmethod
    def process_job_description(text):
        """Process and structure job description text"""
        if not text or text == "Description not available":
            return text
            
        # Split into sections
        sections = text.split('\n\n')
        processed_sections = []
        
        # Common section headers to identify
        section_headers = [
            "responsibilities", "requirements", "qualifications", "skills", 
            "about the job", "about the role", "what you'll do", "what you'll need",
            "about us", "about the company", "who we are", "benefits", "perks",
            "job description", "role description", "experience", "education", 
            "job summary", "job overview", "job requirements", "job responsibilities",
            "job qualifications", "job skills", "job benefits", "job perks",
            "job description", "role description", "experience", "education",
            "job summary", "job overview", "job requirements", "job responsibilities",
            "job qualifications", "job skills", "job benefits", "job perks",
            "Education Qualification and Experience", "Required Skills", "Preferred Qualifications", "Key Responsibilities",
            "About Us", "About the Company", "About the Role", "About the Job",
            "About the Team", "About the Organization", "About the Industry", "About the Location",
            "Position", "Job Description", "Job Summary", "Job Overview"
        ]
        
        # Process each section
        current_section = ""
        for section in sections:
            if not section.strip():
                continue
                
            # Check if this is a new section header
            is_header = False
            section_lower = section.lower().strip()
            
            # Check if section starts with a header
            for header in section_headers:
                if section_lower.startswith(header) or section_lower.startswith("• " + header) or section_lower.startswith("- " + header):
                    # Format as a header
                    current_section = section.strip()
                    is_header = True
                    processed_sections.append(f"\n**{current_section}**\n")
                    break
            
            if not is_header:
                # Check if it's a bullet point list
                if section.strip().startswith('•') or section.strip().startswith('-') or section.strip().startswith('*'):
                    lines = section.split('\n')
                    formatted_lines = []
                    
                    for line in lines:
                        line = line.strip()
                        if line:
                            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                                # Format as bullet point
                                formatted_lines.append(f"• {line.lstrip('•').lstrip('-').lstrip('*').strip()}")
                            else:
                                formatted_lines.append(line)
                    
                    processed_sections.append('\n'.join(formatted_lines))
                else:
                    # Regular paragraph
                    processed_sections.append(section.strip())
        
        # Join all processed sections
        return '\n\n'.join(processed_sections)

    @staticmethod
    def search_jobs_headless(
        job_title_input: list,
        job_location: str,
        job_count: int,
    ) -> dict:
        """
        Run the LinkedIn scraper without Streamlit (for FastAPI / headless use).
        Returns ``{"jobs": [...], "count": N}`` or ``{"error": "...", "jobs": [], "count": 0}``.
        Each job row uses the same column names as the scraper DataFrame.
        """
        driver = None
        try:
            jc = max(1, min(int(job_count), 10))
            driver = LinkedInScraper.webdriver_setup()
            if not driver:
                return {
                    "error": "Failed to initialize Chrome webdriver.",
                    "jobs": [],
                    "count": 0,
                }
            link = LinkedInScraper.build_url(job_title_input, job_location)
            if not LinkedInScraper.link_open_scrolldown(driver, link, jc):
                return {
                    "error": "Failed to load LinkedIn jobs page.",
                    "jobs": [],
                    "count": 0,
                }
            df = LinkedInScraper.scrap_company_data(driver, job_title_input, job_location)
            if df.empty:
                return {"error": "No job listings found.", "jobs": [], "count": 0}
            df_final = LinkedInScraper.scrap_job_description(driver, df, jc)
            if df_final.empty:
                return {
                    "error": "Could not retrieve job descriptions.",
                    "jobs": [],
                    "count": 0,
                }
            df_clean = df_final.replace({np.nan: None})
            records = df_clean.to_dict(orient="records")
            return {"jobs": records, "count": len(records)}
        except Exception as e:
            logger.exception("search_jobs_headless failed")
            return {"error": str(e), "jobs": [], "count": 0}
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass