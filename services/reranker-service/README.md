# reranker-service

Low-latency ranking and small-model inference service.

Responsibilities:

- cross-encoder reranking
- intent classification where needed
- risk classification where needed
- lightweight safety classification

Preferred runtime:

- ONNX Runtime, NVIDIA Triton, or SageMaker real-time endpoints.
