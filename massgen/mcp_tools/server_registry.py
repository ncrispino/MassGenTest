# -*- coding: utf-8 -*-
"""
MCP Server Registry

Centralized registry of curated MCP servers for MassGen.
When auto_discover_custom_tools is enabled, these servers are automatically
included in the agent's MCP configuration (if API keys are available).

Available servers:
- Context7: Up-to-date documentation for libraries and frameworks
- Brave Search: Web search via Brave API (requires API key)
- Alpha Vantage: Financial market data (requires API key)
- Yahoo Finance: Stock prices, financials, options (no API key required)
- SEC EDGAR: Company filings and insider trading data (requires user-agent)
- Pexels: Stock photos and videos search/download (requires API key)
- Google Sheets: Spreadsheet automation (requires service account)

Categories:
- development: Developer tools and documentation
- search: Web search and research
- finance: Financial data and market analysis
- media: Images, videos, and media assets
- productivity: Spreadsheets, documents, and workflow automation
"""

import os
from copy import deepcopy
from typing import Any, Dict, List, Optional

# Registry category definitions for UI display
MCP_CATEGORIES: Dict[str, Dict[str, str]] = {
    "development": {
        "name": "Development",
        "description": "Developer tools and documentation",
    },
    "search": {
        "name": "Search",
        "description": "Web search and research",
    },
    "finance": {
        "name": "Finance",
        "description": "Financial data and market analysis",
    },
    "media": {
        "name": "Media",
        "description": "Images, videos, and media assets",
    },
    "productivity": {
        "name": "Productivity",
        "description": "Spreadsheets, documents, and workflow automation",
    },
}

# Registry of curated MCP servers
MCP_SERVER_REGISTRY: Dict[str, Dict[str, Any]] = {
    "context7": {
        "name": "context7",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp"],
        "description": "Up-to-date code documentation for libraries/frameworks. Outputs large content - recommend writing to files.",
        "category": "development",
        "requires_api_key": False,
        "optional_api_key_env_var": "CONTEXT7_API_KEY",
        "signup_url": "https://context7.com/dashboard",
        "free_tier_info": "Rate-limited without API key",
        "notes": "Optional API key for higher rate limits. Write large outputs to files for easier parsing.",
        "security": {
            "level": "moderate",
        },
    },
    "brave_search": {
        "name": "brave_search",
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@brave/brave-search-mcp-server"],
        "env": {
            "BRAVE_API_KEY": "${BRAVE_API_KEY}",
        },
        "description": "Web search via Brave API. Free tier provides 2000 queries/month.",
        "category": "search",
        "requires_api_key": True,
        "api_key_env_var": "BRAVE_API_KEY",
        "signup_url": "https://brave.com/search/api/",
        "free_tier_info": "2000 queries/month",
        "rate_limit_warning": "Free tier limited to 2000 queries/month. Avoid parallel queries to prevent rate limiting.",
        "notes": "Consider sequential execution for multiple queries.",
        "security": {
            "level": "moderate",
        },
    },
    "alpha_vantage": {
        "name": "alpha_vantage",
        "type": "streamable-http",
        "url": "https://mcp.alphavantage.co/mcp?apikey=${ALPHA_VANTAGE_API_KEY}",
        "description": "Financial market data: stocks, forex, crypto, technical indicators.",
        "category": "finance",
        "requires_api_key": True,
        "api_key_env_var": "ALPHA_VANTAGE_API_KEY",
        "signup_url": "https://www.alphavantage.co/support/#api-key",
        "free_tier_info": "25 requests/day",
        "notes": "HTTP transport - no local installation required. Free API key available.",
        "security": {
            "level": "moderate",
        },
    },
    "yahoo_finance": {
        "name": "yahoo_finance",
        "type": "stdio",
        "command": "uvx",
        "args": ["mcp-yahoo-finance"],
        "description": "Yahoo Finance: stock prices, company info, financials, options, news.",
        "category": "finance",
        "requires_api_key": False,
        "signup_url": None,
        "free_tier_info": "Free (unofficial API)",
        "notes": "No API key required. Uses unofficial yfinance library. May be rate-limited for heavy use.",
        "security": {
            "level": "moderate",
        },
    },
    "sec_edgar": {
        "name": "sec_edgar",
        "type": "stdio",
        "command": "uvx",
        "args": ["sec-edgar-mcp"],
        "env": {
            "SEC_EDGAR_USER_AGENT": "${SEC_EDGAR_USER_AGENT}",
        },
        "description": "SEC EDGAR: company filings, financial statements, insider trading data.",
        "category": "finance",
        "requires_api_key": True,
        "api_key_env_var": "SEC_EDGAR_USER_AGENT",
        "signup_url": None,
        "free_tier_info": "Free (set User-Agent with your email)",
        "notes": "Requires SEC_EDGAR_USER_AGENT in format: 'Your Name (your@email.com)'. No registration needed.",
        "security": {
            "level": "moderate",
        },
    },
    "pexels": {
        "name": "pexels",
        "type": "stdio",
        "command": "uvx",
        "args": ["pexels-mcp-server"],
        "env": {
            "PEXELS_API_KEY": "${PEXELS_API_KEY}",
        },
        "description": "Pexels: search and download stock photos and videos.",
        "category": "media",
        "requires_api_key": True,
        "api_key_env_var": "PEXELS_API_KEY",
        "signup_url": "https://www.pexels.com/api/",
        "free_tier_info": "200 req/hr, 20k/month",
        "notes": "Search photos, videos, curated collections. Instant API key approval.",
        "security": {
            "level": "moderate",
        },
    },
    "google_sheets": {
        "name": "google_sheets",
        "type": "stdio",
        "command": "uvx",
        "args": ["mcp-google-sheets@latest"],
        "env": {
            "SERVICE_ACCOUNT_PATH": "${GOOGLE_SERVICE_ACCOUNT_PATH}",
            "DRIVE_FOLDER_ID": "${GOOGLE_DRIVE_FOLDER_ID}",
        },
        "description": "Google Sheets: create, read, update spreadsheets and cells.",
        "category": "productivity",
        "requires_api_key": True,
        "api_key_env_var": "GOOGLE_SERVICE_ACCOUNT_PATH",
        "signup_url": "https://console.cloud.google.com/apis/credentials",
        "free_tier_info": "Free (Google Cloud free tier)",
        "notes": "Requires GCP service account JSON. Enable Sheets & Drive APIs. Set DRIVE_FOLDER_ID for folder access.",
        "security": {
            "level": "moderate",
        },
    },
}


def is_api_key_available(env_var_name: str) -> bool:
    """Check if an API key environment variable is set and non-empty.

    Args:
        env_var_name: Name of environment variable to check

    Returns:
        True if env var exists and is non-empty, False otherwise
    """
    value = os.environ.get(env_var_name)
    return value is not None and value.strip() != ""


def get_server_config(server_name: str, apply_api_key_logic: bool = True) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific MCP server from registry.

    Args:
        server_name: Name of the server (e.g., "context7", "serena", "brave_search")
        apply_api_key_logic: If True, adds optional API keys when available (e.g., Context7)

    Returns:
        Deep copy of server configuration dict, or None if server not found

    Example:
        >>> config = get_server_config("context7")
        >>> config['name']
        'context7'
    """
    if server_name not in MCP_SERVER_REGISTRY:
        return None

    # Deep copy to avoid modifying the registry
    config = deepcopy(MCP_SERVER_REGISTRY[server_name])

    # Handle optional API key for Context7
    if apply_api_key_logic and server_name == "context7":
        optional_key_var = config.get("optional_api_key_env_var")
        if optional_key_var and is_api_key_available(optional_key_var):
            # Add --api-key argument with the API key value
            api_key_value = os.environ.get(optional_key_var)
            config["args"].extend(["--api-key", api_key_value])

    return config


def get_available_servers(check_api_keys: bool = True) -> List[str]:
    """Get list of registry server names that are available for use.

    Args:
        check_api_keys: If True, only include servers where required API keys are available.
                       If False, return all servers regardless of API key status.

    Returns:
        List of server names that can be used

    Example:
        >>> # If BRAVE_API_KEY is not set:
        >>> get_available_servers(check_api_keys=True)
        ['context7']

        >>> # If BRAVE_API_KEY is set:
        >>> get_available_servers(check_api_keys=True)
        ['context7', 'brave_search']
    """
    available = []

    for server_name, config in MCP_SERVER_REGISTRY.items():
        if not check_api_keys:
            # Include all servers
            available.append(server_name)
        else:
            # Check if required API key is available
            if config.get("requires_api_key", False):
                api_key_var = config.get("api_key_env_var")
                if api_key_var and is_api_key_available(api_key_var):
                    available.append(server_name)
            else:
                # No API key required
                available.append(server_name)

    return available


def get_auto_discovery_servers() -> List[Dict[str, Any]]:
    """Get list of MCP server configurations to include when auto-discovery is enabled.

    Only includes servers where:
    - No API key is required, OR
    - Required API key is available in environment

    Returns:
        List of server configuration dicts ready to merge into mcp_servers

    Example:
        >>> servers = get_auto_discovery_servers()
        >>> len(servers) >= 1  # At least context7 (no API key required)
        True
    """
    available_server_names = get_available_servers(check_api_keys=True)

    # Get full configurations for available servers
    configs = []
    for server_name in available_server_names:
        config = get_server_config(server_name, apply_api_key_logic=True)
        if config:
            configs.append(config)

    return configs


def get_missing_api_keys() -> Dict[str, str]:
    """Get information about registry servers that require missing API keys.

    Returns:
        Dict mapping server name to missing API key environment variable name

    Example:
        >>> missing = get_missing_api_keys()
        >>> # If BRAVE_API_KEY not set:
        >>> missing.get('brave_search')
        'BRAVE_API_KEY'
    """
    missing = {}

    for server_name, config in MCP_SERVER_REGISTRY.items():
        if config.get("requires_api_key", False):
            api_key_var = config.get("api_key_env_var")
            if api_key_var and not is_api_key_available(api_key_var):
                missing[server_name] = api_key_var

    return missing


def get_registry_info() -> Dict[str, Any]:
    """Get summary information about the MCP server registry.

    Returns:
        Dict with registry statistics and status

    Example:
        >>> info = get_registry_info()
        >>> info['total_servers']
        3
        >>> 'context7' in info['available_servers']
        True
    """
    return {
        "total_servers": len(MCP_SERVER_REGISTRY),
        "available_servers": get_available_servers(check_api_keys=True),
        "unavailable_servers": list(get_missing_api_keys().keys()),
        "missing_api_keys": get_missing_api_keys(),
        "server_names": list(MCP_SERVER_REGISTRY.keys()),
    }


def get_servers_by_category() -> Dict[str, List[str]]:
    """Group servers by category for UI display.

    Returns:
        Dict mapping category name to list of server names in that category.

    Example:
        >>> by_category = get_servers_by_category()
        >>> 'context7' in by_category.get('development', [])
        True
        >>> 'alpha_vantage' in by_category.get('finance', [])
        True
    """
    result: Dict[str, List[str]] = {}

    for server_name, config in MCP_SERVER_REGISTRY.items():
        category = config.get("category", "other")
        if category not in result:
            result[category] = []
        result[category].append(server_name)

    return result


def get_signup_url(server_name: str) -> Optional[str]:
    """Get API key signup URL for a server.

    Args:
        server_name: Name of the server

    Returns:
        URL string where user can obtain an API key, or None if not applicable

    Example:
        >>> get_signup_url("alpha_vantage")
        'https://www.alphavantage.co/support/#api-key'
    """
    config = MCP_SERVER_REGISTRY.get(server_name)
    if config:
        return config.get("signup_url")
    return None


def get_free_tier_info(server_name: str) -> Optional[str]:
    """Get free tier information for a server.

    Args:
        server_name: Name of the server

    Returns:
        Free tier description string, or None if not available

    Example:
        >>> get_free_tier_info("alpha_vantage")
        '25 requests/day'
    """
    config = MCP_SERVER_REGISTRY.get(server_name)
    if config:
        return config.get("free_tier_info")
    return None


def get_category_display_name(category: str) -> str:
    """Get display name for a category.

    Args:
        category: Category key (e.g., 'development', 'finance')

    Returns:
        Human-readable category name

    Example:
        >>> get_category_display_name("development")
        'Development'
    """
    cat_info = MCP_CATEGORIES.get(category, {})
    return cat_info.get("name", category.title())
