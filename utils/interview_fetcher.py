import time
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.llm_orchestrator import LLMOrchestrator
from jobs.webdriver_utils import setup_webdriver
import json
import re

class InterviewFetcher:
    """Class to dynamically search and scrape real interview questions"""
    
    def __init__(self, driver=None):
        self.driver = driver
        self.llm = LLMOrchestrator()
        self.sources = [
            {"name": "AmbitionBox", "domain": "ambitionbox.com"},
            {"name": "GeeksforGeeks", "domain": "geeksforgeeks.org"},
            {"name": "Glassdoor", "domain": "glassdoor.co.in"},
            {"name": "Indeed", "domain": "indeed.com"},
            {"name": "LeetCode", "domain": "leetcode.com"}
        ]

    def get_company_context(self, company, role):
        """Use LLM to identify company tier and suggest peers"""
        prompt = f"""
        Identify the industry tier and domain for the company '{company}'.
        Then suggest 5 same-tier competitor companies that would have a similar interview process for a '{role}' role.
        
        Return the result in strictly valid JSON format:
        {{
            "tier": "String description of tier (e.g. FAANG, FinTech Unicorn, Early-stage AI Startup)",
            "domain": "Industry domain (e.g. E-commerce, Cybersecurity)",
            "peers": ["Peer1", "Peer2", "Peer3", "Peer4", "Peer5"]
        }}
        """
        try:
            response, _ = self.llm.generate_content(prompt)
            # Find the JSON block in the response if the LLM added extra text
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"tier": "Unknown", "domain": "General", "peers": []}
        except Exception:
            return {"tier": "Unknown", "domain": "General", "peers": []}

    def generalize_role(self, role):
        """Simplify specific roles into more searchable versions"""
        # Remove common prefixes like 'Associate', 'Junior', 'Senior', etc.
        generalized = re.sub(r'^(Associate|Junior|Senior|Lead|Staff|Principal|Trainee|Graduate|Entry Level)\s+', '', role, flags=re.IGNORECASE)
        # Handle specific common mappings
        mappings = {
            "SDE": "Software Development Engineer",
            "SDE 1": "Software Software Development Engineer",
            "SDE 2": "Senior Software Development Engineer",
            "DevOps": "DevOps Engineer",
            "PM": "Product Manager"
        }
        return mappings.get(generalized, generalized)

    def _ensure_driver(self):
        """Ensure a webdriver is available"""
        if not self.driver:
            self.driver = setup_webdriver()
        return self.driver

    def search_for_questions(self, company, role):
        """Search Google for interview question pages"""
        driver = self._ensure_driver()
        search_query = f'"{role}" interview questions "{company}" site:ambitionbox.com OR site:geeksforgeeks.org OR site:leetcode.com'
        
        urls = []
        try:
            driver.get(f"https://www.google.com/search?q={search_query.replace(' ', '+')}")
            # Wait for search results
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "search")))
            
            # Extract top links
            containers = driver.find_elements(By.CSS_SELECTOR, "div.g")
            for container in containers[:5]:
                link_elem = container.find_element(By.TAG_NAME, "a")
                url = link_elem.get_attribute("href")
                if url and any(source["domain"] in url for source in self.sources):
                    urls.append(url)
        except Exception as e:
            print(f"Search failed: {str(e)}")
            
        return urls

    def scrape_url(self, url):
        """Scrape content using Hybrid method (Requests -> Selenium)"""
        # Try fast Requests first (works for GFG, LeetCode, etc.)
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text()
                # If we got substantial text, use it
                if len(text) > 1000:
                    return text
        except Exception:
            pass

        # Fallback to slow Selenium for JS-heavy sites (AmbitionBox)
        driver = self._ensure_driver()
        try:
            driver.get(url)
            time.sleep(2)
            return driver.find_element(By.TAG_NAME, "body").text
        except Exception as e:
            print(f"Scraping failed for {url}: {str(e)}")
            return ""

    def process_and_filter(self, raw_data_list, target_company, target_role, context):
        """Use LLM to filter top 20 questions from raw text data"""
        combined_text = "\n\n--- SOURCE ---\n\n".join(raw_data_list)
        
        prompt = f"""
        Below is raw text scraped from multiple interview experience websites for the company '{target_company}' and its peers in the '{context['tier']}' tier (domain: {context['domain']}).
        
        YOUR TASK:
        1. Extract exactly 20 REAL interview questions that were actually asked in interviews.
        2. Prioritize questions from '{target_company}' if available.
        3. Identify 'Rare' vs 'Common/Important' questions.
        4. For each question, mention the company where it was asked (if known from the text).
        
        Context:
        Role: {target_role}
        Tier: {context['tier']}
        
        RAW TEXT:
        {combined_text[:15000]} # Limit text length for token limits
        
        Return the result in strictly valid JSON format:
        [
            {{
                "question": "The actual question asked",
                "importance": "Rare" or "High",
                "company": "Company Name",
                "reason": "Why this is important or rare"
            }},
            ... (exactly 20 items)
        ]
        """
        
        try:
            response, provider = self.llm.generate_content(prompt)
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                return json.loads(match.group()), provider
            return [], "Unknown"
        except Exception as e:
            print(f"LLM filtering failed: {str(e)}")
            return [], "Unknown"

    def generate_fallback_questions(self, company, role, context):
        """Use LLM to generate high-quality targeted questions when scraping fails"""
        prompt = f"""
        Scraping for real-world interview questions for '{role}' at '{company}' yielded no direct results.
        
        As an expert recruiter in the '{context['tier']}' tier and '{context['domain']}' domain, generate exactly 20 HIGHLY REALISTIC interview questions that are typically asked for this role.
        
        Guidelines:
        1. 10 questions should be 'Rare/Expert' level.
        2. 10 questions should be 'Critical/Fundamental' for the {role} role.
        3. Since we don't have scraped data, base these on industry standards for {company} or its competitors like {', '.join(context['peers'][:3])}.
        
        Return the result in strictly valid JSON format:
        [
            {{
                "question": "The realistic question",
                "importance": "Rare" or "High",
                "company": "Company Name (Target or Peer)",
                "reason": "Why this specific question is relevant for this company/tier"
            }},
            ... (exactly 20 items)
        ]
        """
        try:
            response, provider = self.llm.generate_content(prompt)
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                return json.loads(match.group()), provider
            return [], "Unknown"
        except Exception:
            return [], "Unknown"

    def fetch_all(self, company, role):
        """Complete pipeline: context -> search -> scrape -> filter"""
        # Use child function for caching to avoid 'self' persistence issues
        return self._cached_fetch_all(company, role)

    @st.cache_data(ttl=86400) # Cache for 24 hours
    def _cached_fetch_all(_self, company, role):
        status_text = st.empty()
        
        # 1. Get Context
        status_text.info(f"✨ Preparing tailored interview questions for {company}...")
        context = _self.get_company_context(company, role)
        
        # 2. Search Target Company
        urls = _self.search_for_questions(company, role)
        
        # 3. Role Generalization Fallback
        if not urls:
            generalized_role = _self.generalize_role(role)
            if generalized_role != role:
                urls = _self.search_for_questions(company, generalized_role)
        
        # 4. Fallback to Peer Search if needed
        if len(urls) < 1 and context['peers']:
            for peer in context['peers'][:2]: # Reduced peer count for speed
                urls.extend(_self.search_for_questions(peer, role))
        
        # Deduplicate URLs
        urls = list(dict.fromkeys(urls))
        
        # 5. Scrape with Early Exit
        scraped_data = []
        if urls:
            for i, url in enumerate(urls[:3]): # Reduced scrape count to 3
                content = _self.scrape_url(url)
                if content:
                    scraped_data.append(content)
                    # Early Exit: If we have enough data from 2 strong sources, stop
                    if len(scraped_data) >= 2 and sum(len(d) for d in scraped_data) > 10000:
                        break
        
        # 6. Filter or Generate Fallback (Silent Fallback)
        if not scraped_data:
            questions, provider = _self.generate_fallback_questions(company, role, context)
        else:
            questions, provider = _self.process_and_filter(scraped_data, company, role, context)
        
        status_text.empty()
        return questions, provider, context
