import httpx
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import urllib.parse
import re


async def search_name(name: str) -> Dict:
    """
    Construct search dorks for DuckDuckGo/Bing.
    Scrape SERPs for LinkedIn profiles, public records, news mentions.
    Extract associated emails, phone numbers, or businesses.
    Return structured JSON of findings.
    """
    results = {
        "name": name,
        "linkedin_profiles": [],
        "public_records": [],
        "news_mentions": [],
        "associated_emails": [],
        "associated_businesses": [],
        "sources": []
    }
    
    # Search for LinkedIn profiles
    linkedin_data = await _search_linkedin_profiles(name)
    results["linkedin_profiles"] = linkedin_data
    if linkedin_data:
        results["sources"].append("LinkedIn")
    
    # Search for public records
    public_records_data = await _search_public_records(name)
    results["public_records"] = public_records_data
    if public_records_data:
        results["sources"].append("Public Records")
    
    # Search for news mentions
    news_data = await _search_news_mentions(name)
    results["news_mentions"] = news_data
    if news_data:
        results["sources"].append("News")
    
    # Extract associated emails from all sources
    results["associated_emails"] = _extract_emails(results)
    
    # Extract associated businesses from all sources
    results["associated_businesses"] = _extract_businesses(results)
    
    return results


async def _search_linkedin_profiles(name: str) -> List[Dict]:
    """Search for LinkedIn profiles using search engine dorks."""
    profiles = []
    
    try:
        # Create LinkedIn-specific search queries
        search_queries = [
            f'site:linkedin.com/in/ "{name}"',
            f'site:linkedin.com/pub/ "{name}"',
            f'"{name}" LinkedIn profile'
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for query in search_queries:
                search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                
                response = await client.get(search_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('a', class_='result__a')
                
                for result in results[:5]:
                    href = result.get('href', '')
                    title = result.get_text()
                    
                    if 'linkedin.com' in href and title:
                        profiles.append({
                            "name": title,
                            "url": href,
                            "source": "linkedin"
                        })
                
                # Add delay to respect rate limits
                import asyncio
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"Error searching LinkedIn profiles: {e}")
    
    return profiles[:10]  # Limit total results


async def _search_public_records(name: str) -> List[Dict]:
    """Search for public records using search engine dorks."""
    records = []
    
    try:
        # Create public record search queries
        search_queries = [
            f'"{name}" "public records"',
            f'"{name}" "court records"',
            f'"{name}" "property records"',
            f'"{name}" "voter registration"'
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for query in search_queries:
                search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                
                response = await client.get(search_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('a', class_='result__a')
                
                for result in results[:3]:
                    href = result.get('href', '')
                    title = result.get_text()
                    
                    if href and title:
                        records.append({
                            "title": title,
                            "url": href,
                            "query": query
                        })
                
                # Add delay to respect rate limits
                import asyncio
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"Error searching public records: {e}")
    
    return records[:10]  # Limit total results


async def _search_news_mentions(name: str) -> List[Dict]:
    """Search for news mentions of the name."""
    mentions = []
    
    try:
        # Create news-specific search query
        query = f'"{name}" news'
        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}&kd=news"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(search_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('a', class_='result__a')
            
            for result in results[:10]:
                href = result.get('href', '')
                title = result.get_text()
                
                if href and title:
                    mention_data = {
                        "title": title,
                        "url": href
                    }
                    
                    # Try to extract snippet
                    snippet_div = result.find_parent('div', class_='result__body')
                    if snippet_div:
                        snippet = snippet_div.find('a', class_='result__snippet')
                        if snippet:
                            mention_data["snippet"] = snippet.get_text()
                    
                    mentions.append(mention_data)
                    
    except Exception as e:
        print(f"Error searching news mentions: {e}")
    
    return mentions


def _extract_emails(results: Dict) -> List[str]:
    """Extract email addresses from all sources."""
    emails = set()
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Check LinkedIn profiles for emails
    for profile in results.get("linkedin_profiles", []):
        found_emails = re.findall(email_pattern, profile.get("name", "") + " " + profile.get("url", ""))
        emails.update(found_emails)
    
    # Check public records for emails
    for record in results.get("public_records", []):
        found_emails = re.findall(email_pattern, record.get("title", "") + " " + record.get("url", ""))
        emails.update(found_emails)
    
    # Check news mentions for emails
    for mention in results.get("news_mentions", []):
        text = mention.get("title", "") + " " + mention.get("snippet", "")
        found_emails = re.findall(email_pattern, text)
        emails.update(found_emails)
    
    return list(emails)


def _extract_businesses(results: Dict) -> List[str]:
    """Extract business names from all sources."""
    businesses = set()
    
    # Check LinkedIn profiles for companies
    for profile in results.get("linkedin_profiles", []):
        name = profile.get("name", "")
        # Try to extract company names from LinkedIn profile names
        if "at " in name.lower() or "works at" in name.lower():
            parts = re.split(r'(at|works at)', name, flags=re.IGNORECASE)
            if len(parts) > 1:
                company = parts[-1].strip()
                if company:
                    businesses.add(company)
    
    # Check news mentions for business names
    for mention in results.get("news_mentions", []):
        text = mention.get("title", "") + " " + mention.get("snippet", "")
        # Look for common business indicators
        business_indicators = ['inc', 'llc', 'corp', 'ltd', 'company', 'corporation']
        for indicator in business_indicators:
            if indicator in text.lower():
                # Extract potential business name around the indicator
                words = text.split()
                for i, word in enumerate(words):
                    if indicator in word.lower():
                        # Get surrounding words as potential business name
                        start = max(0, i - 2)
                        end = min(len(words), i + 3)
                        potential_business = ' '.join(words[start:end])
                        businesses.add(potential_business)
    
    return list(businesses)
