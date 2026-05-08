# Error Contracts V1

Status: draft  
Version: error-contracts-v1

## Standard Error Shape

```json
{
  "requestId": "req_01",
  "status": "error",
  "error": {
    "code": "POLICY_DENIED",
    "message": "The request cannot be answered with the current permissions.",
    "retryable": false,
    "safeUserMessage": "I cannot answer that with your current access.",
    "details": {}
  }
}
```

## Error Codes

| Code | Retryable | User Visible | Meaning |
|---|---:|---:|---|
| `INVALID_REQUEST` | false | yes | request failed validation |
| `AUTH_REQUIRED` | false | yes | user is not authenticated |
| `ENTITLEMENT_UNAVAILABLE` | true | yes | entitlement could not be resolved |
| `POLICY_DENIED` | false | yes | policy denied the request |
| `PII_BLOCKED` | false | yes | sensitive data policy blocked the request |
| `RETRIEVAL_EMPTY` | false | yes | no approved context found |
| `LLM_TIMEOUT` | true | yes | model provider timed out |
| `VERIFICATION_FAILED` | false | yes | draft answer did not pass verification |
| `DEPENDENCY_UNAVAILABLE` | true | yes | required dependency unavailable |

## Security Rule

Internal details must not be exposed in `safeUserMessage`.

