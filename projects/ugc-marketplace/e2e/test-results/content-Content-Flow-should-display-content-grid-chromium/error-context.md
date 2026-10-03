# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: content.spec.ts >> Content Flow >> should display content grid
- Location: tests/content.spec.ts:19:7

# Error details

```
Error: Channel closed
```

```
Error: page.fill: Target page, context or browser has been closed
Call log:
  - waiting for locator('input[name="email"]')

```

```
Error: browserContext.close: Protocol error (Target.disposeBrowserContext): Failed to find context with id 8B4A0F0766403A0892387392ADC4D266
```