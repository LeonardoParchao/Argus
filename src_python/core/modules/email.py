import hashlib
import httpx
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import urllib.parse
import re


async def search_email(email: str) -> Dict:
    """
    Search for email information using multiple data sources.
    
    Args:
        email: The email address to search for
        
    Returns:
        Dictionary containing Gravatar profile, GitHub commits, PGP keys,
        and exposed paste/document information if publicly available
    """
    results = {
        "email": email,
        "gravatar_profile": None,
        "github_commits": [],
        "pgp_keys": [],
        "exposed_pastes": [],
        "document_mentions": [],
        "sources": []
    }
    
    # Check Gravatar for profile existence
    gravatar_data = await _check_gravatar(email)
    if gravatar_data:
        results["gravatar_profile"] = gravatar_data
        results["sources"].append("Gravatar")
    
    # Search GitHub public commits for email
    github_data = await _search_github_commits(email)
    results["github_commits"] = github_data
    if github_data:
        results["sources"].append("GitHub")
    
    # Check PGP keyservers
    pgp_data = await _search_pgp_keyservers(email)
    results["pgp_keys"] = pgp_data
    if pgp_data:
        results["sources"].append("PGP Keyservers")
    
    # Search for exposed pastes (pastebin, etc.)
    paste_data = await _search_exposed_pastes(email)
    results["exposed_pastes"] = paste_data
    if paste_data:
        results["sources"].append("Paste Sites")
    
    # Search for document mentions
    document_data = await _search_document_mentions(email)
    results["document_mentions"] = document_data
    if document_data:
        results["sources"].append("Document Search")
    
    return results


async def _check_gravatar(email: str) -> Optional[Dict]:
    """
    Check Gravatar for profile existence using MD5 hash.
    
    Args:
        email: The email address to check
        
    Returns:
        Dictionary with profile information if found, None otherwise
    """
    try:
        # Generate MD5 hash of email (lowercase, trimmed)
        email_clean = email.strip().lower()
        md5_hash = hashlib.md5(email_clean.encode()).hexdigest()
        
        # Check Gravatar endpoint with d=404 (return 404 if not found)
        gravatar_url = f"https://www.gravatar.com/avatar/{md5_hash}?d=404"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(gravatar_url, headers={
                "User-Agent": "OSINT-Tool/1.0"
            })
            
            # If we get a 200, the profile exists
            if response.status_code == 200:
                # Try to get profile data
                profile_url = f"https://www.gravatar.com/{md5_hash}.json"
                profile_response = await client.get(profile_url, headers={
                    "User-Agent": "OSINT-Tool/1.0"
                })
                
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    entry = profile_data.get("entry", [{}])[0]
                    
                    return {
                        "profile_exists": True,
                        "hash": md5_hash,
                        "display_name": entry.get("displayName"),
                        "preferred_username": entry.get("preferredUsername"),
                        "location": entry.get("location"),
                        "about_me": entry.get("aboutMe"),
                        "photos": [photo.get("value") for photo in entry.get("photos", [])],
                        "urls": [url.get("value") for url in entry.get("urls", [])]
                    }
                else:
                    return {
                        "profile_exists": True,
                        "hash": md5_hash,
                        "note": "Profile exists but detailed data not accessible"
                    }
            else:
                return None
                
    except Exception as e:
        print(f"Error checking Gravatar: {e}")
    
    return None


async def _search_github_commits(email: str) -> List[Dict]:
    """
    Search GitHub public commits for the email address.
    
    Args:
        email: The email address to search for
        
    Returns:
        List of commit information containing the email
    """
    commits = []
    
    try:
        # Use GitHub search API for commits
        search_url = "https://api.github.com/search/commits"
        params = {
            "q": f"author-email:{email}",
            "per_page": 10
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(search_url, params=params, headers={
                "User-Agent": "OSINT-Tool/1.0",
                "Accept": "application/vnd.github.cloak-preview"
            })
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                for item in items:
                    commit_info = {
                        "repository": item.get("repository", {}).get("full_name"),
                        "author": item.get("author", {}).get("login"),
                        "commit_sha": item.get("sha"),
                        "message": item.get("commit", {}).get("message", "")[:100],
                        "date": item.get("commit", {}).get("author", {}).get("date"),
                        "url": item.get("html_url")
                    }
                    commits.append(commit_info)
                    
    except Exception as e:
        print(f"Error searching GitHub commits: {e}")
    
    return commits


async def _search_pgp_keyservers(email: str) -> List[Dict]:
    """
    Search PGP keyservers for the email address.
    
    Args:
        email: The email address to search for
        
    Returns:
        List of PGP key information
    """
    pgp_keys = []
    
    try:
        # Search keys.openpgp.org
        search_url = f"https://keys.openpgp.org/search/{urllib.parse.quote(email)}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(search_url, headers={
                "User-Agent": "OSINT-Tool/1.0"
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for key information
                key_elements = soup.find_all('div', class_='key')
                
                for key_elem in key_elements[:10]:
                    key_info = {
                        "key_id": key_elem.get('data-key-id', ''),
                        "fingerprint": key_elem.get('data-fingerprint', ''),
                        "url": key_elem.find('a')['href'] if key_elem.find('a') else ''
                    }
                    
                    if key_info["key_id"] or key_info["fingerprint"]:
                        pgp_keys.append(key_info)
                        
    except Exception as e:
        print(f"Error searching PGP keyservers: {e}")
    
    return pgp_keys


async def _search_exposed_pastes(email: str) -> List[Dict]:
    """
    Search paste sites for exposed email addresses.
    
    Args:
        email: The email address to search for
        
    Returns:
        List of paste information containing the email
    """
    pastes = []
    
    try:
        # Create search queries for paste sites
        search_queries = [
            f'site:pastebin.com "{email}"',
            f'site:paste.ee "{email}"',
            f'site:justpaste.it "{email}"',
            f'"{email}" paste leak dump'
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for query in search_queries:
                search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                
                response = await client.get(search_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results = soup.find_all('a', class_='result__a')
                    
                    for result in results[:3]:
                        href = result.get('href', '')
                        title = result.get_text()
                        
                        if href and title:
                            pastes.append({
                                "title": title,
                                "url": href,
                                "query": query
                            })
                
                # Add delay to respect rate limits
                import asyncio
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"Error searching exposed pastes: {e}")
    
    return pastes[:10]


async def _search_document_mentions(email: str) -> List[Dict]:
    """
    Search for documents containing the email address.
    
    Args:
        email: The email address to search for
        
    Returns:
        List of document information containing the email
    """
    documents = []
    
    try:
        # Create search queries for documents
        search_queries = [
            f'"{email}" filetype:pdf',
            f'"{email}" filetype:doc',
            f'"{email}" filetype:docx',
            f'"{email}" filetype:xls',
            f'"{email}" filetype:xlsx'
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for query in search_queries:
                search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                
                response = await client.get(search_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results = soup.find_all('a', class_='result__a')
                    
                    for result in results[:3]:
                        href = result.get('href', '')
                        title = result.get_text()
                        
                        if href and title:
                            documents.append({
                                "title": title,
                                "url": href,
                                "query": query
                            })
                
                # Add delay to respect rate limits
                import asyncio
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"Error searching document mentions: {e}")
    
    return documents[:10]
