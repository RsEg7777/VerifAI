"""
Source Transparency Data
Contains bias labels and credibility scores for news sources
"""

# Source bias categories: left, center-left, center, center-right, right
# Credibility levels: high, medium, low

SOURCE_DATA = {
    # Major International Sources
    "bbc.com": {
        "name": "BBC News",
        "bias": "center",
        "credibility": "high",
        "description": "British public broadcaster known for factual reporting"
    },
    "reuters.com": {
        "name": "Reuters",
        "bias": "center",
        "credibility": "high",
        "description": "International wire service with strict editorial standards"
    },
    "apnews.com": {
        "name": "Associated Press",
        "bias": "center",
        "credibility": "high",
        "description": "Non-profit news cooperative, highly factual"
    },
    "npr.org": {
        "name": "NPR",
        "bias": "center-left",
        "credibility": "high",
        "description": "US public radio network with strong fact-checking"
    },
    "theguardian.com": {
        "name": "The Guardian",
        "bias": "center-left",
        "credibility": "high",
        "description": "UK broadsheet with investigative journalism focus"
    },
    "nytimes.com": {
        "name": "The New York Times",
        "bias": "center-left",
        "credibility": "high",
        "description": "Major US newspaper with extensive fact-checking"
    },
    "washingtonpost.com": {
        "name": "Washington Post",
        "bias": "center-left",
        "credibility": "high",
        "description": "US newspaper known for political coverage"
    },
    "wsj.com": {
        "name": "Wall Street Journal",
        "bias": "center-right",
        "credibility": "high",
        "description": "Business-focused US newspaper"
    },
    "economist.com": {
        "name": "The Economist",
        "bias": "center",
        "credibility": "high",
        "description": "UK news magazine with global perspective"
    },
    "cnn.com": {
        "name": "CNN",
        "bias": "center-left",
        "credibility": "medium",
        "description": "24-hour US news network"
    },
    "foxnews.com": {
        "name": "Fox News",
        "bias": "right",
        "credibility": "medium",
        "description": "US cable news with conservative perspective"
    },
    "msnbc.com": {
        "name": "MSNBC",
        "bias": "left",
        "credibility": "medium",
        "description": "US cable news with progressive perspective"
    },
    "aljazeera.com": {
        "name": "Al Jazeera",
        "bias": "center-left",
        "credibility": "high",
        "description": "Qatar-based international news network"
    },
    
    # Indian News Sources
    "thehindu.com": {
        "name": "The Hindu",
        "bias": "center-left",
        "credibility": "high",
        "description": "Major Indian English-language newspaper"
    },
    "indianexpress.com": {
        "name": "Indian Express",
        "bias": "center",
        "credibility": "high",
        "description": "Indian English-language daily newspaper"
    },
    "timesofindia.indiatimes.com": {
        "name": "Times of India",
        "bias": "center",
        "credibility": "medium",
        "description": "Largest-selling English newspaper in India"
    },
    "hindustantimes.com": {
        "name": "Hindustan Times",
        "bias": "center",
        "credibility": "medium",
        "description": "Major Indian English-language newspaper"
    },
    "ndtv.com": {
        "name": "NDTV",
        "bias": "center-left",
        "credibility": "high",
        "description": "Indian television news network"
    },
    "indiatoday.in": {
        "name": "India Today",
        "bias": "center",
        "credibility": "medium",
        "description": "Indian news magazine and website"
    },
    "news18.com": {
        "name": "News18",
        "bias": "center-right",
        "credibility": "medium",
        "description": "Indian news network"
    },
    "zeenews.india.com": {
        "name": "Zee News",
        "bias": "center-right",
        "credibility": "medium",
        "description": "Indian Hindi news channel"
    },
    "aajtak.in": {
        "name": "Aaj Tak",
        "bias": "center-right",
        "credibility": "medium",
        "description": "Indian Hindi news channel"
    },
    "livemint.com": {
        "name": "Mint",
        "bias": "center",
        "credibility": "high",
        "description": "Indian business newspaper"
    },
    "economictimes.indiatimes.com": {
        "name": "Economic Times",
        "bias": "center",
        "credibility": "high",
        "description": "Indian financial newspaper"
    },
    "scroll.in": {
        "name": "Scroll.in",
        "bias": "center-left",
        "credibility": "high",
        "description": "Indian digital news publication"
    },
    "thewire.in": {
        "name": "The Wire",
        "bias": "center-left",
        "credibility": "high",
        "description": "Indian non-profit news publication"
    },
    "opindia.com": {
        "name": "OpIndia",
        "bias": "right",
        "credibility": "low",
        "description": "Indian right-wing news website"
    },
    "swarajyamag.com": {
        "name": "Swarajya",
        "bias": "right",
        "credibility": "medium",
        "description": "Indian right-wing magazine"
    },
    
    # Marathi News Sources
    "lokmat.com": {
        "name": "Lokmat",
        "bias": "center",
        "credibility": "medium",
        "description": "Marathi language newspaper from Maharashtra"
    },
    "loksatta.com": {
        "name": "Loksatta",
        "bias": "center",
        "credibility": "high",
        "description": "Marathi daily newspaper"
    },
    "maharashtratimes.com": {
        "name": "Maharashtra Times",
        "bias": "center",
        "credibility": "medium",
        "description": "Marathi language newspaper"
    },
    "divyamarathi.bhaskar.com": {
        "name": "Divya Marathi",
        "bias": "center",
        "credibility": "medium",
        "description": "Marathi language newspaper"
    },
    "abpmajha.abplive.in": {
        "name": "ABP Majha",
        "bias": "center",
        "credibility": "medium",
        "description": "Marathi news channel"
    },
    
    # Technology & Fact-Checking Sources
    "snopes.com": {
        "name": "Snopes",
        "bias": "center",
        "credibility": "high",
        "description": "Fact-checking website"
    },
    "politifact.com": {
        "name": "PolitiFact",
        "bias": "center",
        "credibility": "high",
        "description": "Political fact-checking website"
    },
    "factcheck.org": {
        "name": "FactCheck.org",
        "bias": "center",
        "credibility": "high",
        "description": "Non-partisan fact-checking organization"
    },
    "altnews.in": {
        "name": "Alt News",
        "bias": "center",
        "credibility": "high",
        "description": "Indian fact-checking website"
    },
    "boomlive.in": {
        "name": "BOOM",
        "bias": "center",
        "credibility": "high",
        "description": "Indian fact-checking organization"
    },
    
    # Default for unknown sources
    "unknown": {
        "name": "Unknown Source",
        "bias": "unknown",
        "credibility": "unknown",
        "description": "Source credibility not yet evaluated"
    }
}

# Bias color coding for UI
BIAS_COLORS = {
    "left": "#3b82f6",        # Blue
    "center-left": "#06b6d4", # Cyan
    "center": "#10b981",      # Green
    "center-right": "#f59e0b", # Amber
    "right": "#ef4444",       # Red
    "unknown": "#6b7280"      # Gray
}

# Credibility color coding
CREDIBILITY_COLORS = {
    "high": "#10b981",    # Green
    "medium": "#f59e0b",  # Amber
    "low": "#ef4444",     # Red
    "unknown": "#6b7280"  # Gray
}


def get_source_info(domain):
    """
    Get source information by domain name
    
    Args:
        domain: The domain name (e.g., 'bbc.com')
        
    Returns:
        dict: Source information including bias and credibility
    """
    # Clean the domain
    domain = domain.lower().strip()
    
    # Remove www. prefix if present
    if domain.startswith('www.'):
        domain = domain[4:]
    
    # Check for exact match
    if domain in SOURCE_DATA:
        return SOURCE_DATA[domain]
    
    # Check for partial match (subdomain handling)
    for source_domain, info in SOURCE_DATA.items():
        if domain.endswith(source_domain) or source_domain.endswith(domain):
            return info
    
    # Return unknown if not found
    return SOURCE_DATA["unknown"]


def get_bias_label(bias):
    """Get human-readable bias label"""
    labels = {
        "left": "Left-Leaning",
        "center-left": "Center-Left",
        "center": "Centrist",
        "center-right": "Center-Right",
        "right": "Right-Leaning",
        "unknown": "Unknown Bias"
    }
    return labels.get(bias, "Unknown Bias")


def get_credibility_label(credibility):
    """Get human-readable credibility label"""
    labels = {
        "high": "High Credibility",
        "medium": "Medium Credibility",
        "low": "Low Credibility",
        "unknown": "Unverified"
    }
    return labels.get(credibility, "Unverified")
