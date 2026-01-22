"""
Security Controls Module
=========================
Implements security controls for safe consumption of third-party APIs

Key Controls:
1. Output Encoding - HTML entity encoding to neutralize XSS
2. Logging - Security event logging for audit trails
3. Vendor Error Handling - Graceful handling of vendor failures
"""

import html
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

# Dangerous patterns that indicate potential XSS
DANGEROUS_PATTERNS = [
    r'<script',
    r'<img[^>]+onerror',
    r'<svg[^>]+onload',
    r'onclick\s*=',
    r'javascript:',
    r'<iframe',
    r'<object',
    r'<embed'
]

def detect_dangerous_content(text: str) -> bool:
    """
    Detect if text contains potentially dangerous HTML/JavaScript
    
    Args:
        text: String to analyze
        
    Returns:
        True if dangerous patterns detected, False otherwise
    """
    if not text:
        return False
    
    text_lower = text.lower()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False

def encode_html(text: str) -> str:
    """
    HTML entity encode text to neutralize XSS payloads
    
    This is the PRIMARY SECURITY CONTROL that prevents XSS attacks
    by converting dangerous characters to their HTML entity equivalents.
    
    Conversions:
        < → &lt;
        > → &gt;
        & → &amp;
        " → &quot;
        ' → &#x27;
    
    Args:
        text: Raw text that may contain XSS payloads
        
    Returns:
        HTML-encoded safe text
    """
    if not text:
        return text
    
    # Use Python's built-in html.escape for proper encoding
    # quote=True ensures both single and double quotes are encoded
    return html.escape(text, quote=True)

def get_control_state(is_safe_flow: bool, dangerous_detected: bool) -> str:
    """
    Determine three-state control status
    
    States:
        - "Not Available" - Unsafe flow, control disabled
        - "Applied" - Safe flow AND dangerous content detected
        - "Not Applied" - Safe flow but no dangerous content detected
    
    Args:
        is_safe_flow: Whether this is the safe endpoint
        dangerous_detected: Whether dangerous content was found
        
    Returns:
        Control state string
    """
    if not is_safe_flow:
        return "Not Available"
    
    if dangerous_detected:
        return "Applied"
    else:
        return "Not Applied"

def log_security_event(event_type: str, details: Dict[str, Any]) -> None:
    """
    Log security events to audit file
    
    Creates logs/security-events.log if it doesn't exist.
    Appends timestamped security events for compliance and forensics.
    
    Args:
        event_type: Type of security event (e.g., "encoded_vendor_html")
        details: Dictionary of event details
    """
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "security-events.log"
    
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {event_type}"
    
    # Add details to log entry
    for key, value in details.items():
        log_entry += f" {key}={value}"
    
    log_entry += "\n"
    
    # Append to log file
    with open(log_file, "a") as f:
        f.write(log_entry)

def get_log_tail(lines: int = 10) -> list:
    """
    Get last N lines from security log
    
    Args:
        lines: Number of lines to retrieve
        
    Returns:
        List of log lines (newest first)
    """
    log_file = Path(__file__).parent / "logs" / "security-events.log"
    
    if not log_file.exists():
        return []
    
    try:
        with open(log_file, "r") as f:
            all_lines = f.readlines()
            return all_lines[-lines:] if all_lines else []
    except Exception:
        return []

def sanitize_vendor_data(data: Dict[str, Any], is_safe_flow: bool) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Main security control function - sanitizes vendor data
    
    This function implements the core security controls:
    1. Detects dangerous content
    2. Applies HTML encoding in safe flow
    3. Logs security events
    4. Returns control states
    
    Args:
        data: Raw vendor data (potentially malicious)
        is_safe_flow: Whether to apply security controls
        
    Returns:
        Tuple of (sanitized_data, control_states)
    """
    # Check if title contains dangerous content
    title = data.get("title", "")
    dangerous_detected = detect_dangerous_content(title)
    
    # Initialize control states
    controls = {
        "output_encoding": get_control_state(is_safe_flow, dangerous_detected),
        "logging": get_control_state(is_safe_flow, dangerous_detected),
        "vendor_error_handling": "Not Triggered"
    }
    
    # Apply security controls in safe flow
    if is_safe_flow:
        # Encode HTML in title field
        sanitized_data = data.copy()
        sanitized_data["title"] = encode_html(title)
        
        # Log security event if dangerous content detected
        if dangerous_detected:
            log_security_event("encoded_vendor_html", {
                "id": data.get("id"),
                "variant": data.get("variant"),
                "original_length": len(title),
                "encoded_length": len(sanitized_data["title"])
            })
        
        return sanitized_data, controls
    else:
        # Unsafe flow - return data unmodified
        return data, controls
