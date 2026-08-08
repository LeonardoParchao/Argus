import subprocess
import json
import httpx
import dns.resolver
from typing import Dict, List, Optional
import re


async def search_website(domain: str) -> Dict:
    """
    Call RDAP/WHOIS API directly via httpx for registrar data.
    Perform DNS lookups (A, MX, TXT) using Python dns library.
    Call Rust binary (osint_binary) as subprocess for subdomain enumeration and port scanning.
    Parse stdout JSON lines from Rust binary.
    Return aggregated infrastructure data.
    """
    results = {
        "domain": domain,
        "whois_data": None,
        "dns_records": {
            "A": [],
            "MX": [],
            "TXT": [],
            "NS": []
        },
        "subdomains": [],
        "open_ports": [],
        "sources": []
    }
    
    # Get WHOIS/RDAP data
    whois_data = await _get_whois_data(domain)
    results["whois_data"] = whois_data
    if whois_data:
        results["sources"].append("WHOIS/RDAP")
    
    # Get DNS records
    dns_data = _get_dns_records(domain)
    results["dns_records"] = dns_data
    if any(dns_data.values()):
        results["sources"].append("DNS")
    
    # Call Rust binary for subdomain enumeration and port scanning
    rust_data = _call_rust_binary(domain)
    if rust_data:
        results["subdomains"] = rust_data.get("subdomains", [])
        results["open_ports"] = rust_data.get("open_ports", [])
        if results["subdomains"] or results["open_ports"]:
            results["sources"].append("Rust Network Scanner")
    
    return results


async def _get_whois_data(domain: str) -> Optional[Dict]:
    """Get WHOIS/RDAP data for the domain."""
    try:
        # Use RDAP (Registration Data Access Protocol)
        # First, get the TLD's RDAP service
        tld = domain.split('.')[-1]
        
        # Use a simple RDAP lookup for common TLDs
        # For .com, .net, .org, we can use the default RDAP services
        rdap_url = f"https://rdap.org/domain/{domain}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(rdap_url, headers={
                "User-Agent": "OSINT-Tool/1.0",
                "Accept": "application/rdap+json"
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant WHOIS information
                whois_info = {
                    "domain": domain,
                    "registrar": None,
                    "organization": None,
                    "created_date": None,
                    "expired_date": None,
                    "status": [],
                    "nameservers": []
                }
                
                # Extract registrar/organization
                entities = data.get("entities", [])
                for entity in entities:
                    roles = entity.get("roles", [])
                    if "registrar" in roles:
                        registrar_info = entity.get("vcardArray", [])
                        if registrar_info:
                            whois_info["registrar"] = _extract_vcard_value(registrar_info, "fn")
                            whois_info["organization"] = _extract_vcard_value(registrar_info, "org")
                
                # Extract dates
                events = data.get("events", [])
                for event in events:
                    event_action = event.get("eventAction")
                    if event_action == "registration":
                        whois_info["created_date"] = event.get("eventDate")
                    elif event_action == "expiration":
                        whois_info["expired_date"] = event.get("eventDate")
                
                # Extract status
                whois_info["status"] = data.get("status", [])
                
                # Extract nameservers
                nameservers = data.get("nameservers", [])
                for ns in nameservers:
                    ns_name = ns.get("ldhName")
                    if ns_name:
                        whois_info["nameservers"].append(ns_name)
                
                return whois_info
            else:
                # Fallback to WHOIS if RDAP fails
                return await _get_whois_fallback(domain)
                
    except Exception as e:
        print(f"Error getting WHOIS/RDAP data: {e}")
        # Try fallback
        return await _get_whois_fallback(domain)
    
    return None


def _extract_vcard_value(vcard_array, field_name):
    """Extract value from vCard array."""
    try:
        if vcard_array and len(vcard_array) > 1:
            for item in vcard_array[1]:
                if item[0] == field_name and len(item) > 3:
                    return item[3]
    except Exception:
        pass
    return None


async def _get_whois_fallback(domain: str) -> Optional[Dict]:
    """Fallback WHOIS lookup using whois.com API."""
    try:
        # Use whois.com's API as a fallback
        url = f"https://www.whois.com/whois/{domain}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            
            if response.status_code == 200:
                # Parse the HTML response
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to extract basic information
                whois_info = {
                    "domain": domain,
                    "registrar": None,
                    "organization": None,
                    "created_date": None,
                    "expired_date": None,
                    "status": [],
                    "nameservers": []
                }
                
                # Look for data rows
                data_rows = soup.find_all('div', class_='df-block')
                for row in data_rows:
                    label = row.find('div', class_='df-label')
                    value = row.find('div', class_='df-value')
                    
                    if label and value:
                        label_text = label.get_text().strip().lower()
                        value_text = value.get_text().strip()
                        
                        if "registrar" in label_text:
                            whois_info["registrar"] = value_text
                        elif "registrant" in label_text or "organization" in label_text:
                            whois_info["organization"] = value_text
                        elif "created" in label_text or "registration" in label_text:
                            whois_info["created_date"] = value_text
                        elif "expiry" in label_text or "expiration" in label_text:
                            whois_info["expired_date"] = value_text
                        elif "name server" in label_text or "nameserver" in label_text:
                            whois_info["nameservers"].append(value_text)
                
                return whois_info
                
    except Exception as e:
        print(f"Error in WHOIS fallback: {e}")
    
    return None


def _get_dns_records(domain: str) -> Dict[str, List[str]]:
    """Get DNS records for the domain."""
    dns_data = {
        "A": [],
        "MX": [],
        "TXT": [],
        "NS": []
    }
    
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 10
        resolver.lifetime = 10
        
        # A records
        try:
            answers = resolver.resolve(domain, 'A')
            dns_data["A"] = [str(rdata) for rdata in answers]
        except Exception:
            pass
        
        # MX records
        try:
            answers = resolver.resolve(domain, 'MX')
            dns_data["MX"] = [str(rdata.exchange) for rdata in answers]
        except Exception:
            pass
        
        # TXT records
        try:
            answers = resolver.resolve(domain, 'TXT')
            dns_data["TXT"] = [str(rdata).replace('"', '') for rdata in answers]
        except Exception:
            pass
        
        # NS records
        try:
            answers = resolver.resolve(domain, 'NS')
            dns_data["NS"] = [str(rdata) for rdata in answers]
        except Exception:
            pass
        
    except Exception as e:
        print(f"Error getting DNS records: {e}")
    
    return dns_data


def _call_rust_binary(domain: str) -> Optional[Dict]:
    """Call Rust binary for subdomain enumeration and port scanning."""
    try:
        # Determine the path to the Rust binary
        import os
        import platform
        
        # Add .exe extension on Windows
        binary_name = 'osint_binary.exe' if platform.system() == 'Windows' else 'osint_binary'
        
        binary_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'src_rust', 'target', 'release', binary_name
        )
        
        # If release binary doesn't exist, try debug
        if not os.path.exists(binary_path):
            binary_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'src_rust', 'target', 'debug', binary_name
            )
        
        # If binary still doesn't exist, return empty results
        if not os.path.exists(binary_path):
            print(f"Rust binary not found at {binary_path}")
            return {"subdomains": [], "open_ports": []}
        
        # Call the Rust binary
        result = subprocess.run(
            [binary_path, '--target', domain, '--mode', 'scan'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            # Parse JSON lines from stdout
            rust_data = {
                "subdomains": [],
                "open_ports": []
            }
            
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        json_line = json.loads(line)
                        if json_line.get("type") == "subdomain":
                            rust_data["subdomains"].append(json_line.get("value"))
                        elif json_line.get("type") == "port":
                            rust_data["open_ports"].append({
                                "port": json_line.get("port"),
                                "service": json_line.get("service", "unknown")
                            })
                    except json.JSONDecodeError:
                        continue
            
            return rust_data
        else:
            print(f"Rust binary failed with return code {result.returncode}")
            print(f"Error: {result.stderr}")
            return {"subdomains": [], "open_ports": []}
            
    except subprocess.TimeoutExpired:
        print("Rust binary timed out")
        return {"subdomains": [], "open_ports": []}
    except Exception as e:
        print(f"Error calling Rust binary: {e}")
        return {"subdomains": [], "open_ports": []}
