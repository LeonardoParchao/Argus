import httpx
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import urllib.parse


async def search_address(address: str) -> Dict:
    """
    Search for address information using multiple data sources.
    
    Args:
        address: The address string to search for
        
    Returns:
        Dictionary containing geocoordinates, nearby businesses, property records,
        and associated names if publicly available
    """
    results = {
        "address": address,
        "geocoordinates": None,
        "nearby_businesses": [],
        "property_records": [],
        "news_mentions": [],
        "associated_names": [],
        "sources": []
    }
    
    # Get geocoordinates from OpenStreetMap Nominatim API
    geo_data = await _get_nominatim_data(address)
    if geo_data:
        results["geocoordinates"] = geo_data
        results["sources"].append("OpenStreetMap Nominatim")
        
        # Get nearby businesses if we have coordinates
        if geo_data.get("lat") and geo_data.get("lon"):
            nearby = await _get_nearby_businesses(geo_data["lat"], geo_data["lon"])
            results["nearby_businesses"] = nearby
            if nearby:
                results["sources"].append("OpenStreetMap Overpass")
    
    # Search for property records and tax assessor data
    property_data = await _search_property_records(address)
    results["property_records"] = property_data
    if property_data:
        results["sources"].append("Property Record Search")
    
    # Search for news mentions
    news_data = await _search_news_mentions(address)
    results["news_mentions"] = news_data
    if news_data:
        results["sources"].append("News Search")
    
    # Extract associated names from all sources
    results["associated_names"] = _extract_associated_names(results)
    
    return results


async def _get_nominatim_data(address: str) -> Optional[Dict]:
    """
    Query OpenStreetMap Nominatim API for geocoordinates.
    
    Args:
        address: The address string to geocode
        
    Returns:
        Dictionary with lat, lon, and display_name if found, None otherwise
    """
    try:
        base_url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "addressdetails": 1,
            "limit": 1
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(base_url, params=params, headers={
                "User-Agent": "OSINT-Tool/1.0"
            })
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                return {
                    "lat": data[0].get("lat"),
                    "lon": data[0].get("lon"),
                    "display_name": data[0].get("display_name"),
                    "address_details": data[0].get("address", {})
                }
    except Exception as e:
        print(f"Error querying Nominatim API: {e}")
    
    return None


async def _get_nearby_businesses(lat: str, lon: str) -> List[Dict]:
    """
    Query OpenStreetMap Overpass API for nearby businesses.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        
    Returns:
        List of nearby business information
    """
    try:
        overpass_query = f"""
        [out:json];
        (
          node["shop"](around:500,{lat},{lon});
          node["amenity"](around:500,{lat},{lon});
          node["office"](around:500,{lat},{lon});
        );
        out body;
        """
        
        base_url = "https://overpass-api.de/api/interpreter"
        params = {"data": overpass_query}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(base_url, params=params, headers={
                "User-Agent": "OSINT-Tool/1.0"
            })
            response.raise_for_status()
            
            data = response.json()
            businesses = []
            
            for element in data.get("elements", []):
                tags = element.get("tags", {})
                business_info = {
                    "name": tags.get("name", "Unknown"),
                    "type": tags.get("shop") or tags.get("amenity") or tags.get("office", "Unknown"),
                    "lat": element.get("lat"),
                    "lon": element.get("lon")
                }
                businesses.append(business_info)
            
            return businesses[:20]  # Limit to 20 results
            
    except Exception as e:
        print(f"Error querying Overpass API: {e}")
    
    return []


async def _search_property_records(address: str) -> List[Dict]:
    """
    Search for property records using search engine queries.
    
    Args:
        address: The address string to search for
        
    Returns:
        List of property record information
    """
    property_records = []
    
    # Create search queries for property records
    search_queries = [
        f'"{address}" property records',
        f'"{address}" tax assessor',
        f'"{address}" owner',
        f'"{address}" real estate'
    ]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for query in search_queries:
                # Using DuckDuckGo HTML results (no API key required)
                search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                
                response = await client.get(search_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('a', class_='result__a')
                
                for result in results[:5]:  # Limit results per query
                    href = result.get('href', '')
                    title = result.get_text()
                    
                    if href and title:
                        property_records.append({
                            "title": title,
                            "url": href,
                            "query": query
                        })
                        
                        # Try to extract additional info from the snippet
                        snippet_div = result.find_parent('div', class_='result__body')
                        if snippet_div:
                            snippet = snippet_div.find('a', class_='result__snippet')
                            if snippet:
                                property_records[-1]["snippet"] = snippet.get_text()
                
                # Add delay to respect rate limits
                import asyncio
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"Error searching property records: {e}")
    
    return property_records[:10]  # Limit total results


async def _search_news_mentions(address: str) -> List[Dict]:
    """
    Search for news mentions of the address.
    
    Args:
        address: The address string to search for
        
    Returns:
        List of news mention information
    """
    news_mentions = []
    
    try:
        # Create news-specific search query
        query = f'"{address}" news'
        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}&kd=news"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(search_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('a', class_='result__a')
            
            for result in results[:10]:
                href = result.get('href', '')
                title = result.get_text()
                
                if href and title:
                    news_mentions.append({
                        "title": title,
                        "url": href
                    })
                    
                    # Try to extract date/source from snippet
                    snippet_div = result.find_parent('div', class_='result__body')
                    if snippet_div:
                        snippet = snippet_div.find('a', class_='result__snippet')
                        if snippet:
                            news_mentions[-1]["snippet"] = snippet.get_text()
            
    except Exception as e:
        print(f"Error searching news mentions: {e}")
    
    return news_mentions


def _extract_associated_names(results: Dict) -> List[str]:
    """
    Extract associated business or resident names from search results.
    
    Args:
        results: The complete search results dictionary
        
    Returns:
        List of unique associated names
    """
    names = set()
    
    # Extract from nearby businesses
    for business in results.get("nearby_businesses", []):
        name = business.get("name")
        if name and name != "Unknown":
            names.add(name)
    
    # Extract from property record titles/snippets
    for record in results.get("property_records", []):
        title = record.get("title", "")
        snippet = record.get("snippet", "")
        
        # Simple extraction - look for common name patterns
        # This is a basic implementation and could be enhanced with NLP
        for text in [title, snippet]:
            if "owner:" in text.lower():
                parts = text.split("owner:")
                if len(parts) > 1:
                    potential_name = parts[1].strip().split()[0:3]  # First 2-3 words
                    names.add(" ".join(potential_name))
    
    # Extract from news mentions
    for news in results.get("news_mentions", []):
        title = news.get("title", "")
        # Basic name extraction from news titles
        words = title.split()
        # Look for capitalized words that might be names
        for i, word in enumerate(words):
            if word[0].isupper() and i > 0 and words[i-1][0].isupper():
                # Consecutive capitalized words might be a name
                names.add(f"{words[i-1]} {word}")
    
    return sorted(list(names))
