import httpx
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import urllib.parse
import re


async def search_business(business_name: str) -> Dict:
    """
    Search for business information using multiple data sources.
    
    Args:
        business_name: The business name to search for
        
    Returns:
        Dictionary containing SEC filings, corporate registry data,
        state registry information, LinkedIn data, and associated details
    """
    results = {
        "business_name": business_name,
        "sec_filings": [],
        "opencorporates_data": None,
        "state_registry": [],
        "linkedin_data": None,
        "associated_addresses": [],
        "associated_personnel": [],
        "sources": []
    }
    
    # Search SEC EDGAR for public filings
    sec_data = await _search_sec_edgar(business_name)
    results["sec_filings"] = sec_data
    if sec_data:
        results["sources"].append("SEC EDGAR")
    
    # Search OpenCorporates for corporate registry data
    opencorporates_data = await _search_opencorporates(business_name)
    results["opencorporates_data"] = opencorporates_data
    if opencorporates_data:
        results["sources"].append("OpenCorporates")
    
    # Search state registry pages via search engine dorks
    state_registry_data = await _search_state_registry(business_name)
    results["state_registry"] = state_registry_data
    if state_registry_data:
        results["sources"].append("State Registry Search")
    
    # Search LinkedIn for company page
    linkedin_data = await _search_linkedin_company(business_name)
    results["linkedin_data"] = linkedin_data
    if linkedin_data:
        results["sources"].append("LinkedIn")
    
    # Extract associated addresses from all sources
    results["associated_addresses"] = _extract_addresses(results)
    
    # Extract associated personnel from all sources
    results["associated_personnel"] = _extract_personnel(results)
    
    return results


async def _search_sec_edgar(business_name: str) -> List[Dict]:
    """
    Search SEC EDGAR for public company filings.
    
    Args:
        business_name: The business name to search for
        
    Returns:
        List of SEC filing information
    """
    sec_filings = []
    
    try:
        # Clean the business name for search
        clean_name = re.sub(r'[^\w\s]', '', business_name).strip()
        
        # Search SEC EDGAR database
        search_url = "https://www.sec.gov/cgi-bin/browse-edgar"
        params = {
            "company": clean_name,
            "action": "getcompany",
            "type": "10-K,10-Q,8-K",
            "count": "10",
            "output": "atom"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(search_url, params=params, headers={
                "User-Agent": "OSINT-Tool/1.0"
            })
            response.raise_for_status()
            
            # Parse XML response
            soup = BeautifulSoup(response.text, 'xml')
            entries = soup.find_all('entry')
            
            for entry in entries[:10]:
                filing_info = {
                    "title": entry.find('title').get_text() if entry.find('title') else "Unknown",
                    "link": entry.find('link').get('href') if entry.find('link') else "",
                    "filing_type": entry.find('filing-type').get_text() if entry.find('filing-type') else "Unknown",
                    "filing_date": entry.find('filing-date').get_text() if entry.find('filing-date') else "Unknown",
                    "company_name": entry.find('company-name').get_text() if entry.find('company-name') else ""
                }
                sec_filings.append(filing_info)
                
    except Exception as e:
        print(f"Error searching SEC EDGAR: {e}")
    
    return sec_filings


async def _search_opencorporates(business_name: str) -> Optional[Dict]:
    """
    Search OpenCorporates for corporate registry data.
    
    Args:
        business_name: The business name to search for
        
    Returns:
        Dictionary with corporate registry information if found, None otherwise
    """
    try:
        # OpenCorporates search API (free tier available)
        search_url = "https://api.opencorporates.com/companies/search"
        params = {
            "q": business_name,
            "format": "json",
            "per_page": "1"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(search_url, params=params, headers={
                "User-Agent": "OSINT-Tool/1.0"
            })
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", {}).get("companies", [])
            
            if results and len(results) > 0:
                company = results[0]["company"]
                return {
                    "name": company.get("name"),
                    "company_number": company.get("company_number"),
                    "jurisdiction": company.get("jurisdiction_code"),
                    "incorporation_date": company.get("incorporation_date"),
                    "dissolution_date": company.get("dissolution_date"),
                    "registered_address": company.get("registered_address_in_full"),
                    "current_status": company.get("current_status"),
                    "opencorporates_url": company.get("opencorporates_url")
                }
                    
    except Exception as e:
        print(f"Error searching OpenCorporates: {e}")
    
    return None


async def _search_state_registry(business_name: str) -> List[Dict]:
    """
    Search state registry public search pages using search engine dorks.
    
    Args:
        business_name: The business name to search for
        
    Returns:
        List of state registry information
    """
    state_registry = []
    
    # Create search queries for state business registries
    search_queries = [
        f'"{business_name}" "business registry"',
        f'"{business_name}" "secretary of state"',
        f'"{business_name}" "corporation division"',
        f'"{business_name}" "entity search"',
        f'"{business_name}" "llc" "registered"'
    ]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for query in search_queries:
                # Using DuckDuckGo HTML results
                search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                
                response = await client.get(search_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('a', class_='result__a')
                
                for result in results[:3]:  # Limit results per query
                    href = result.get('href', '')
                    title = result.get_text()
                    
                    if href and title:
                        state_registry.append({
                            "title": title,
                            "url": href,
                            "query": query
                        })
                        
                        # Try to extract additional info from the snippet
                        snippet_div = result.find_parent('div', class_='result__body')
                        if snippet_div:
                            snippet = snippet_div.find('a', class_='result__snippet')
                            if snippet:
                                state_registry[-1]["snippet"] = snippet.get_text()
                
                # Add delay to respect rate limits
                import asyncio
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"Error searching state registry: {e}")
    
    return state_registry[:10]  # Limit total results


async def _search_linkedin_company(business_name: str) -> Optional[Dict]:
    """
    Search LinkedIn for company page information.
    
    Args:
        business_name: The business name to search for
        
    Returns:
        Dictionary with LinkedIn company information if found, None otherwise
    """
    try:
        # Use search engine to find LinkedIn company page
        query = f'"{business_name}" site:linkedin.com/company'
        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(search_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('a', class_='result__a')
            
            linkedin_url = None
            for result in results[:5]:
                href = result.get('href', '')
                if 'linkedin.com/company' in href:
                    linkedin_url = href
                    break
            
            if linkedin_url:
                # Try to fetch the LinkedIn company page
                try:
                    linkedin_response = await client.get(linkedin_url, headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    })
                    linkedin_response.raise_for_status()
                    
                    linkedin_soup = BeautifulSoup(linkedin_response.text, 'html.parser')
                    
                    # Extract available information
                    company_data = {
                        "linkedin_url": linkedin_url,
                        "name": business_name,
                        "address": None,
                        "employees": [],
                        "industry": None,
                        "website": None
                    }
                    
                    # Try to extract address
                    address_elem = linkedin_soup.find('div', class_='org-top-card-summary-info-list__info-item')
                    if address_elem:
                        company_data["address"] = address_elem.get_text().strip()
                    
                    # Try to extract industry
                    industry_elem = linkedin_soup.find('p', class_='org-top-card-summary-info-list__info-item')
                    if industry_elem:
                        company_data["industry"] = industry_elem.get_text().strip()
                    
                    # Try to extract website
                    website_elem = linkedin_soup.find('a', class_='org-top-card-primary-actions__company-link')
                    if website_elem:
                        company_data["website"] = website_elem.get('href', '')
                    
                    return company_data
                    
                except Exception as e:
                    print(f"Error fetching LinkedIn company page: {e}")
                    # Return partial data if we at least found the URL
                    return {
                        "linkedin_url": linkedin_url,
                        "name": business_name,
                        "address": None,
                        "employees": [],
                        "industry": None,
                        "website": None
                    }
                    
    except Exception as e:
        print(f"Error searching LinkedIn: {e}")
    
    return None


def _extract_addresses(results: Dict) -> List[str]:
    """
    Extract addresses from all data sources.
    
    Args:
        results: The aggregated results dictionary
        
    Returns:
        List of unique addresses found
    """
    addresses = set()
    
    # Extract from OpenCorporates
    if results.get("opencorporates_data") and results["opencorporates_data"].get("registered_address"):
        addresses.add(results["opencorporates_data"]["registered_address"])
    
    # Extract from LinkedIn
    if results.get("linkedin_data") and results["linkedin_data"].get("address"):
        addresses.add(results["linkedin_data"]["address"])
    
    # Extract from SEC filings (if addresses are mentioned)
    for filing in results.get("sec_filings", []):
        # Simple extraction - in real implementation, would parse filing content
        if "address" in filing.get("title", "").lower():
            addresses.add(filing["title"])
    
    return list(addresses)


def _extract_personnel(results: Dict) -> List[str]:
    """
    Extract personnel information from all data sources.
    
    Args:
        results: The aggregated results dictionary
        
    Returns:
        List of personnel names
    """
    personnel = set()
    
    # Extract from LinkedIn (employee list would need more sophisticated scraping)
    if results.get("linkedin_data") and results["linkedin_data"].get("employees"):
        # If employees is a list of dicts with 'name' field
        for employee in results["linkedin_data"]["employees"]:
            if isinstance(employee, dict):
                name = employee.get("name")
                if name:
                    personnel.add(name)
            elif isinstance(employee, str):
                personnel.add(employee)
    
    # Extract from SEC filings (officers/directors mentioned in filings)
    for filing in results.get("sec_filings", []):
        # Simple extraction - in real implementation, would parse filing content
        if "officer" in filing.get("title", "").lower() or "director" in filing.get("title", "").lower():
            # Use the title as a proxy for the person's name
            personnel.add(filing.get("title", ""))
    
    return list(personnel)
