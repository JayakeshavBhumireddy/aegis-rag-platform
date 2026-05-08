# bedrock-access module

Purpose:

- IAM access needed by the LLM Gateway to call managed model providers.

Rule:

- application services must not call foundation models directly.
- only the LLM Gateway should receive model invocation permissions.

