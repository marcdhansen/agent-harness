---
title: "Implement Multi-LLM Provider Abstraction Layer"
labels: critical, architecture, enhancement
priority: P0
---

## Problem Statement

The harness currently appears to have hardcoded LLM client integration (`llm_client=my_llm`), which prevents:
- Supporting multiple LLM providers (Anthropic, OpenAI, Google, etc.)
- Provider-specific optimizations (e.g., prompt caching for Anthropic)
- Fallback chains when one provider is unavailable
- A/B testing different models
- Switching providers without code changes

## Proposed Solution

Create a unified LLM provider abstraction with adapters for different providers:

```python
class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, messages, tools=None, **kwargs):
        """Generate completion from messages"""
        pass
    
    @abstractmethod
    async def stream(self, messages, tools=None, **kwargs):
        """Stream completion from messages"""
        pass
    
    @abstractmethod
    def supports_tool_calling(self) -> bool:
        """Whether provider supports tool calling"""
        pass

class AnthropicProvider(LLMProvider):
    """Adapter for Anthropic Claude models"""
    # Handles Anthropic-specific tool calling format
    # Supports prompt caching
    # Manages extended thinking mode
    
class OpenAIProvider(LLMProvider):
    """Adapter for OpenAI models"""
    # Handles OpenAI function calling format
    # Supports structured outputs
    
class GoogleProvider(LLMProvider):
    """Adapter for Google Gemini models"""
    # Handles Gemini tool calling format
```

## Implementation Details

1. **Create provider interface** (`src/agent_harness/providers/base.py`)
2. **Implement Anthropic adapter** with prompt caching support
3. **Implement OpenAI adapter** with function calling
4. **Implement Google/Gemini adapter**
5. **Add provider factory** for instantiation
6. **Update harness** to use provider interface
7. **Add provider configuration** (via config file or env vars)
8. **Add fallback chain support** (try provider A, fallback to B)

## Acceptance Criteria

- [ ] Can instantiate harness with any supported provider
- [ ] Tool calling works across all providers
- [ ] Provider-specific features available (e.g., Anthropic caching)
- [ ] Streaming works for all providers
- [ ] Fallback chain works (primary → secondary → tertiary)
- [ ] Configuration can specify provider via config/env
- [ ] Documentation includes provider setup for each
- [ ] Tests cover all providers

## Dependencies

None - this is foundational

## Estimated Effort

Large (1-2 weeks)

## References

- [Anthropic API Docs](https://docs.anthropic.com)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Google AI API Docs](https://ai.google.dev/docs)
