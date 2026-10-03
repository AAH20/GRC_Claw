# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: creators.spec.ts >> Creators Flow >> should display creators page
- Location: tests/creators.spec.ts:14:7

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
Error: browserContext.close: Target page, context or browser has been closed
```