# Rebuild-from-Reference-Website Pattern

When the user says "build X like website Y" or "rebuild X to match Y's functionality", follow this systematic approach BEFORE writing code.

## 1. Scrape the reference website for feature extraction

When browser tools time out (common with ad-heavy sites), use curl + Python parsing:

```bash
# Extract form fields and section headers
curl -s "URL" | python3 -c "
import sys, re
html = sys.stdin.read()
# Input fields
inputs = re.findall(r'<input[^>]*name=\"([^\"]+)\"[^>]*>', html)
# Section headers  
sections = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', html)
# Dropdown options
selects = re.findall(r'<select[^>]*name=\"([^\"]+)\"', html)
"

# For JavaScript-heavy sites: find the JS source
curl -s "URL" | grep -o 'src="[^"]*\.js[^"]*"'
# Try to read the JS for formulas
curl -s "JS_URL" | python3 -c "..." 
```

## 2. Map features to inputs/outputs

Create a table:
- Input → parameter name → range → default value
- Output → display name → calculation type

## 3. Verify formulas against the reference

Find authoritative data points from the reference (screenshots, sample calculations, or visible results in the HTML) and use them as ground truth.

For financial calculators, use standard TVM formulas and verify:
- Run calculator.net with known inputs, record outputs
- Reproduce those inputs in your code
- Tolerance: < 0.1% for large values, < ±1 for small values

## 4. Competitive analysis (optional but recommended)

- Check 3-5 competitors in the target ecosystem (e.g., WeChat mini-programs)
- Identify gaps: what combination of features does NO competitor offer?
- This forms your differentiation angle

## 5. Write the plan

Structure:
```
1. Requirements (from reference)
2. Competitive landscape  
3. Verified formulas (with test cases)
4. UI information architecture
5. Module/component split
6. Phase-by-phase task list
7. Acceptance criteria
8. YAGNI (explicitly list what NOT to build)
```

## Common pitfalls

- **Ext4 path length limits**: When cloning repos with long Chinese filenames, ext4 can hit 255-byte filename or 4096-byte path limits. Workaround: `git clone --no-checkout` then selective checkout, or use `git archive` to extract.
- **Ad-blocked browser**: Reference sites with Google AdSense may load slowly in headless browsers. Fall back to curl.
- **Minified JS**: When formulas are buried in minified JS, fall back to domain knowledge (e.g., standard TVM formulas for financial calculators) and verify against the reference's visible outputs rather than trying to extract source code.
