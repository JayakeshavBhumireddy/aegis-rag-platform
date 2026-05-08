# verification-service

Validates generated answers before users see them.

Responsibilities:

- citation validation
- grounding validation
- license and permission compliance
- navigation path validation
- PII and sensitive data scan
- forbidden module/action checks

Security:

- high-risk answers must be verified before streaming to the user.
