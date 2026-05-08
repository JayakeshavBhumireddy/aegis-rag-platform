# Data Classification V1

Status: draft

## Classes

| Class | Examples | Default Handling |
|---|---|---|
| public | public docs, public benchmark datasets | may be indexed after license review |
| internal | synthetic corpora, architecture docs | internal access only |
| tenant-confidential | tenant config, licenses, role mappings | tenant-scoped access |
| restricted | personal, financial, regulated, application-record data | do not use in V1 product-guidance mode |
| secret | API keys, tokens, credentials | never send to LLM, never log |

## V1 Data Access Boundary

V1 defaults to:

```text
product_guidance_only
```

This means:

- answer product/help/navigation questions
- do not answer customer-record-specific questions
- do not query tenant operational records
- do not persist sensitive data as long-term memory

