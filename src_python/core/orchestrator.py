from typing import Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import database
from core.modules import name, email, address, website, business


async def run_search(target_type: str, target_value: str) -> Dict:
    """
    Route to appropriate module (name, email, address, website, business).
    Await results from the module.
    Format results and pass to database.py for upsert and relationship creation.
    Return structured data to the caller (CLI or API).
    """
    # Initialize database if needed
    database.init_db()
    
    # Create the main entity
    main_entity_id = database.upsert_entity(target_type, target_value, source="user_input")
    
    results = {
        "target_type": target_type,
        "target_value": target_value,
        "main_entity_id": main_entity_id,
        "search_results": {},
        "entities_created": [],
        "relationships_created": []
    }
    
    # Route to appropriate module based on target_type
    try:
        if target_type.lower() == "name":
            search_results = await name.search_name(target_value)
            results["search_results"]["name"] = search_results
            
            # Process name search results and create relationships
            await _process_name_results(search_results, main_entity_id, results)
            
        elif target_type.lower() == "email":
            search_results = await email.search_email(target_value)
            results["search_results"]["email"] = search_results
            
            # Process email search results and create relationships
            await _process_email_results(search_results, main_entity_id, results)
            
        elif target_type.lower() == "address":
            search_results = await address.search_address(target_value)
            results["search_results"]["address"] = search_results
            
            # Process address search results and create relationships
            await _process_address_results(search_results, main_entity_id, results)
            
        elif target_type.lower() == "website":
            search_results = await website.search_website(target_value)
            results["search_results"]["website"] = search_results
            
            # Process website search results and create relationships
            await _process_website_results(search_results, main_entity_id, results)
            
        elif target_type.lower() == "business":
            search_results = await business.search_business(target_value)
            results["search_results"]["business"] = search_results
            
            # Process business search results and create relationships
            await _process_business_results(search_results, main_entity_id, results)
            
        else:
            results["error"] = f"Unknown target type: {target_type}"
            
    except Exception as e:
        results["error"] = f"Search failed: {str(e)}"
    
    return results


async def _process_name_results(search_results: Dict, main_entity_id: str, results: Dict) -> None:
    """Process name search results and create entities/relationships."""
    # Extract associated emails from name search
    if "associated_emails" in search_results:
        for email_data in search_results["associated_emails"]:
            email_entity_id = database.upsert_entity("email", email_data, source="name_search")
            database.create_relationship(main_entity_id, email_entity_id, "has_email", confidence=70)
            results["entities_created"].append({"id": email_entity_id, "type": "email", "value": email_data})
            results["relationships_created"].append({"source": main_entity_id, "target": email_entity_id, "type": "has_email"})
    
    # Extract associated businesses from name search
    if "associated_businesses" in search_results:
        for business_data in search_results["associated_businesses"]:
            business_entity_id = database.upsert_entity("business", business_data, source="name_search")
            database.create_relationship(main_entity_id, business_entity_id, "associated_with", confidence=60)
            results["entities_created"].append({"id": business_entity_id, "type": "business", "value": business_data})
            results["relationships_created"].append({"source": main_entity_id, "target": business_entity_id, "type": "associated_with"})


async def _process_email_results(search_results: Dict, main_entity_id: str, results: Dict) -> None:
    """Process email search results and create entities/relationships."""
    # Extract GitHub usernames from commits
    if "github_commits" in search_results:
        for commit in search_results["github_commits"]:
            author = commit.get("author")
            if author:
                author_entity_id = database.upsert_entity("name", author, source="github_commits")
                database.create_relationship(main_entity_id, author_entity_id, "github_author", confidence=90)
                results["entities_created"].append({"id": author_entity_id, "type": "name", "value": author})
                results["relationships_created"].append({"source": main_entity_id, "target": author_entity_id, "type": "github_author"})
    
    # Extract associated names from document mentions
    if "document_mentions" in search_results:
        for mention in search_results["document_mentions"]:
            if "associated_names" in mention:
                for name in mention["associated_names"]:
                    name_entity_id = database.upsert_entity("name", name, source="document_mention")
                    database.create_relationship(main_entity_id, name_entity_id, "mentioned_with", confidence=50)
                    results["entities_created"].append({"id": name_entity_id, "type": "name", "value": name})
                    results["relationships_created"].append({"source": main_entity_id, "target": name_entity_id, "type": "mentioned_with"})


async def _process_address_results(search_results: Dict, main_entity_id: str, results: Dict) -> None:
    """Process address search results and create entities/relationships."""
    # Extract associated names from property records
    if "associated_names" in search_results:
        for name in search_results["associated_names"]:
            name_entity_id = database.upsert_entity("name", name, source="address_search")
            database.create_relationship(main_entity_id, name_entity_id, "resident_at", confidence=70)
            results["entities_created"].append({"id": name_entity_id, "type": "name", "value": name})
            results["relationships_created"].append({"source": main_entity_id, "target": name_entity_id, "type": "resident_at"})
    
    # Extract nearby businesses
    if "nearby_businesses" in search_results:
        for business in search_results["nearby_businesses"]:
            business_name = business.get("name", "Unknown")
            business_entity_id = database.upsert_entity("business", business_name, source="nearby_business")
            database.create_relationship(main_entity_id, business_entity_id, "nearby", confidence=80)
            results["entities_created"].append({"id": business_entity_id, "type": "business", "value": business_name})
            results["relationships_created"].append({"source": main_entity_id, "target": business_entity_id, "type": "nearby"})


async def _process_website_results(search_results: Dict, main_entity_id: str, results: Dict) -> None:
    """Process website search results and create entities/relationships."""
    # Get the target value from the main entity in results
    target_value = results.get("target_value", "")
    
    # Extract subdomains
    if "subdomains" in search_results:
        for subdomain in search_results["subdomains"]:
            subdomain_entity_id = database.upsert_entity("website", subdomain, source="subdomain_scan")
            database.create_relationship(main_entity_id, subdomain_entity_id, "subdomain_of", confidence=95)
            results["entities_created"].append({"id": subdomain_entity_id, "type": "website", "value": subdomain})
            results["relationships_created"].append({"source": main_entity_id, "target": subdomain_entity_id, "type": "subdomain_of"})
    
    # Extract open ports
    if "open_ports" in search_results:
        for port_info in search_results["open_ports"]:
            port_entity_id = database.upsert_entity("service", f"{target_value}:{port_info['port']}", source="port_scan")
            database.create_relationship(main_entity_id, port_entity_id, "hosts_service", confidence=90)
            results["entities_created"].append({"id": port_entity_id, "type": "service", "value": f"{target_value}:{port_info['port']}"})
            results["relationships_created"].append({"source": main_entity_id, "target": port_entity_id, "type": "hosts_service"})
    
    # Extract organization information from WHOIS
    if "whois_data" in search_results and search_results["whois_data"]:
        whois = search_results["whois_data"]
        if "organization" in whois:
            org_entity_id = database.upsert_entity("business", whois["organization"], source="whois")
            database.create_relationship(main_entity_id, org_entity_id, "registered_to", confidence=85)
            results["entities_created"].append({"id": org_entity_id, "type": "business", "value": whois["organization"]})
            results["relationships_created"].append({"source": main_entity_id, "target": org_entity_id, "type": "registered_to"})


async def _process_business_results(search_results: Dict, main_entity_id: str, results: Dict) -> None:
    """Process business search results and create entities/relationships."""
    # Extract associated addresses
    if "associated_addresses" in search_results:
        for address in search_results["associated_addresses"]:
            address_entity_id = database.upsert_entity("address", address, source="business_search")
            database.create_relationship(main_entity_id, address_entity_id, "located_at", confidence=85)
            results["entities_created"].append({"id": address_entity_id, "type": "address", "value": address})
            results["relationships_created"].append({"source": main_entity_id, "target": address_entity_id, "type": "located_at"})
    
    # Extract associated personnel
    if "associated_personnel" in search_results:
        for person in search_results["associated_personnel"]:
            person_entity_id = database.upsert_entity("name", person, source="business_search")
            database.create_relationship(main_entity_id, person_entity_id, "employs", confidence=75)
            results["entities_created"].append({"id": person_entity_id, "type": "name", "value": person})
            results["relationships_created"].append({"source": main_entity_id, "target": person_entity_id, "type": "employs"})
