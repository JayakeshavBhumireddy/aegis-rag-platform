# entitlement-service

Builds the entitlement envelope for each authenticated user.

Responsibilities:

- tenant resolution
- licensed modules
- enabled features
- product version
- user roles and permissions
- license and permission hash generation

Security:

- fail closed if an entitlement envelope cannot be created
- cache only short-lived envelopes
