# context-service

Controls context, memory, and state.

Responsibilities:

- load session state
- load safe user preferences
- load tenant context
- select relevant conversation history
- redact and compress context
- decide which memory updates are allowed

Rule:

- Do not store personal, customer, financial, regulated, application-record, credential, or secret data as long-term memory.
