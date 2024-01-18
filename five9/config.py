SETTINGS = {
    "FIVENINE_VCC_LOGIN_URL": "https://app.five9.com/appsvcs/rs/svc/auth/login",
    "FIVENINE_VCC_METADATA_URL": "https://app.five9.com/appsvcs/rs/svc/metadata",
    "logging_level": "DEBUG",
}

CONTEXT_PATHS = {
    # Agent REST API Services
    "agent_rest": "/appsvcs/rs/svc",
    # Agent call recordings and email message attachments"
    "agent_str": "/strsvcs/rs/svc",
    # Supervisor REST API Services
    "sup_rest": "/supsvcs/rs/svc",
    
    "websocket_agent": "/appsvcs/ws/${this.randomSocketKey}_agent",
    "websocket_super": "/supsvcs/sws/${this.randomSocketKey}_super",
}
