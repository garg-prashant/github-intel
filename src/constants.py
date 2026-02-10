"""Default categories used when CATEGORIES env is not set.

Each category can include an optional "search_topic" used for GitHub topic search
when scraping for that category (e.g. pipeline run with category filter).
"""

from __future__ import annotations

DEFAULT_CATEGORIES: list[dict[str, str | list[str]]] = [
    {
        "slug": "ai-ml",
        "name": "AI & Machine Learning",
        "description": "Machine learning frameworks, training, and inference tooling",
        "keywords": ["pytorch", "tensorflow", "neural", "machine learning", "deep learning", "training", "inference", "transformers"],
        "search_topic": "AI",
    },
    {
        "slug": "llms-agents",
        "name": "LLMs & Agents",
        "description": "Large language models, agents, RAG, and orchestration",
        "keywords": ["llm", "agent", "RAG", "retrieval", "langchain", "openai", "anthropic", "orchestration", "prompt"],
        "search_topic": "agent",
    },
    {
        "slug": "mcp-tooling",
        "name": "MCP & Tooling",
        "description": "Model Context Protocol, MCP servers, and AI tooling",
        "keywords": ["mcp", "model context protocol", "mcp server", "tool", "plugin"],
        "search_topic": "MCP",
    },
    {
        "slug": "backend",
        "name": "Backend",
        "description": "API frameworks, services, and backend infrastructure",
        "keywords": ["api", "backend", "framework", "rest", "graphql", "server", "microservice"],
        "search_topic": "backend",
    },
    {
        "slug": "python-libs",
        "name": "Python Libraries",
        "description": "Popular Python libraries and utilities",
        "keywords": ["python", "library", "package", "pip", "pypi"],
        "search_topic": "python",
    },
    {
        "slug": "web3-crypto",
        "name": "Web3 & Crypto",
        "description": "Blockchain, smart contracts, and crypto tooling",
        "keywords": ["blockchain", "ethereum", "smart contract", "web3", "crypto", "defi", "solidity"],
        "search_topic": "crypto",
    },
    {
        "slug": "devops-mlops",
        "name": "DevOps & MLOps",
        "description": "CI/CD, deployment, and ML operations",
        "keywords": ["devops", "mlops", "ci/cd", "deploy", "kubernetes", "docker", "pipeline", "monitoring"],
        "search_topic": "devops",
    },
    {
        "slug": "deepfake",
        "name": "Deepfake & Synthetic Media",
        "description": "Tools and libraries for creating, detecting, and analyzing deepfakes and synthetic media",
        "keywords": ["deepfake", "face swap", "synthetic media", "media manipulation", "deep learning", "detection", "forensics", "GAN", "voice cloning"],
        "search_topic": "deepfake",
    }
]
