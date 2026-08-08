use pyo3::prelude::*;
use pyo3::types::PyDict;
use regex::Regex;
use serde_json::Value;

/// Extract email addresses from HTML content
#[pyfunction]
fn extract_emails_from_html(html: String) -> Vec<String> {
    let email_regex = Regex::new(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}").unwrap();
    let mut emails = Vec::new();
    
    for capture in email_regex.find_iter(&html) {
        let email = capture.as_str().to_string();
        if !emails.contains(&email) {
            emails.push(email);
        }
    }
    
    emails
}

/// Extract names from HTML content using common patterns
#[pyfunction]
fn extract_names_from_html(html: String) -> Vec<String> {
    let mut names = Vec::new();
    
    // Common name patterns (simplified)
    let name_patterns = vec![
        r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b",  // First Last
        r"\b([A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+)\b",  // First M. Last
        r"\b([A-Z][a-z]+-[A-Z][a-z]+)\b",  // Hyphenated names
    ];
    
    for pattern in name_patterns {
        let regex = Regex::new(pattern).unwrap();
        for capture in regex.find_iter(&html) {
            let name = capture.as_str().to_string();
            if !names.contains(&name) && name.len() > 3 {
                names.push(name);
            }
        }
    }
    
    names
}

/// Parse JSON string quickly and return as Python object
#[pyfunction]
fn parse_json_fast(json_str: String, py: Python) -> PyResult<PyObject> {
    match serde_json::from_str::<Value>(&json_str) {
        Ok(value) => {
            // Convert JSON value to Python object
            let py_obj = json_value_to_py(value, py)?;
            Ok(py_obj)
        }
        Err(e) => {
            Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("Failed to parse JSON: {}", e)
            ))
        }
    }
}

/// Helper function to convert JSON Value to Python object
fn json_value_to_py(value: Value, py: Python) -> PyResult<PyObject> {
    match value {
        Value::Null => Ok(py.None()),
        Value::Bool(b) => Ok(b.into_py(py)),
        Value::Number(n) => {
            if n.is_i64() {
                Ok(n.as_i64().unwrap().into_py(py))
            } else {
                Ok(n.as_f64().unwrap().into_py(py))
            }
        }
        Value::String(s) => Ok(s.into_py(py)),
        Value::Array(arr) => {
            let py_list = pyo3::types::PyList::empty(py);
            for item in arr {
                py_list.append(json_value_to_py(item, py)?)?;
            }
            Ok(py_list.into())
        }
        Value::Object(obj) => {
            let py_dict = PyDict::new(py);
            for (key, value) in obj {
                py_dict.set_item(key, json_value_to_py(value, py)?)?;
            }
            Ok(py_dict.into())
        }
    }
}

/// Extract URLs from HTML content
#[pyfunction]
fn extract_urls_from_html(html: String) -> Vec<String> {
    let url_regex = Regex::new("https?://[^\\s<>\"']+\\.[^\\s<>\"']+").unwrap();
    let mut urls = Vec::new();
    
    for capture in url_regex.find_iter(&html) {
        let url = capture.as_str().to_string();
        if !urls.contains(&url) {
            urls.push(url);
        }
    }
    
    urls
}

/// Extract phone numbers from HTML content
#[pyfunction]
fn extract_phone_numbers(html: String) -> Vec<String> {
    let phone_patterns = vec![
        "\\d{3}-\\d{3}-\\d{4}",      // 123-456-7890
        "\\(\\d{3}\\)\\s*\\d{3}-\\d{4}", // (123) 456-7890
        "\\d{10}",                 // 1234567890
        "\\+?\\d{1,3}[-.\\s]?\\(?\\d{3}\\)?[-.\\s]?\\d{3}[-.\\s]?\\d{4}", // International format
    ];
    
    let mut phones = Vec::new();
    
    for pattern in phone_patterns {
        let regex = Regex::new(pattern).unwrap();
        for capture in regex.find_iter(&html) {
            let phone = capture.as_str().to_string();
            if !phones.contains(&phone) {
                phones.push(phone);
            }
        }
    }
    
    phones
}

/// Extract IP addresses from HTML content
#[pyfunction]
fn extract_ip_addresses(html: String) -> Vec<String> {
    let ip_regex = Regex::new("\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}").unwrap();
    let mut ips = Vec::new();
    
    for capture in ip_regex.find_iter(&html) {
        let ip = capture.as_str().to_string();
        // Validate IP address components
        let parts: Vec<&str> = ip.split('.').collect();
        let valid = parts.iter().all(|part| {
            if let Ok(_num) = part.parse::<u8>() {
                true
            } else {
                false
            }
        });
        
        if valid && !ips.contains(&ip) {
            ips.push(ip);
        }
    }
    
    ips
}

/// Extract domains from HTML content
#[pyfunction]
fn extract_domains(html: String) -> Vec<String> {
    let domain_regex = Regex::new("[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\\.[a-zA-Z]{2,}").unwrap();
    let mut domains = Vec::new();
    
    for capture in domain_regex.find_iter(&html) {
        let domain = capture.as_str().to_string().to_lowercase();
        if !domains.contains(&domain) {
            domains.push(domain);
        }
    }
    
    domains
}

#[pymodule]
fn osint_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(extract_emails_from_html, m)?)?;
    m.add_function(wrap_pyfunction!(extract_names_from_html, m)?)?;
    m.add_function(wrap_pyfunction!(parse_json_fast, m)?)?;
    m.add_function(wrap_pyfunction!(extract_urls_from_html, m)?)?;
    m.add_function(wrap_pyfunction!(extract_phone_numbers, m)?)?;
    m.add_function(wrap_pyfunction!(extract_ip_addresses, m)?)?;
    m.add_function(wrap_pyfunction!(extract_domains, m)?)?;
    Ok(())
}
