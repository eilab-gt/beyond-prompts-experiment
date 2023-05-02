"""
CreativeContextConfig.py

Configurations (default values, etc.) used by creative contexts.

Environment specific: need to change them for installation.

"""

# To configure the creative context to use any other locations for API calls,
# Add entry in the following dictionaries.

available_configs = {
    "local":
        {
            "default_server_addr": "http://localhost:8765",
            "generate_api_route": "/api/pnb"
        }
}

available_carp_configs = {
    "local":
        {
            "default_server_addr": "http://localhost:8765",
            "carp_api_route": "/api/carp"
        }
}
