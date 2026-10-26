# Automated regression tests

Tests are run automatically by GitHub Actions on every push and pull request.

## Backend / API tests

```bash
python -m pip install -r requirements.txt
python -m pytest -q tests/test_api.py
```

These check homepage rendering, static JS delivery, JSON validation, regional data provenance, and actual PDF responses (including blank notes).

## Browser / UI tests

Requires Node.js and Chromium for Playwright:

```bash
npm install
npx playwright install chromium
npm run test:ui
```

Playwright starts its own Uvicorn server on port 8765. It checks that the page initializes **without JavaScript exceptions**, that the regional preview renders, segmental inputs can be edited and expanded, wizard navigation preserves data, all advanced sections open, PDF download works, history is populated, and DEXA mode switches correctly.

Use `npm run test:ui:headed` to watch the browser.

**Important:** Backend unit tests cannot detect browser initialization failures. The Playwright tests are essential and specifically catch the earlier `esc()` initialization-order bug.

## Before considering a change complete

Both the **api** and **browser** GitHub Actions jobs must be green. A pushed commit is not proof of a passing test. Check [GitHub Actions](https://github.com/jimilinuxguy/body-composition-report-studio/actions) for the actual result.
