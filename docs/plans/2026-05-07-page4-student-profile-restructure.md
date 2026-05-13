# Page 4 Student Profile Restructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild report page 4 so it reads as three clear sections with profile-first ordering, analysis-first hierarchy, and reduced repetition.

**Architecture:** Keep the change scoped to the existing `student_profile` module. Add HTML-structure regression coverage first, then refactor the Jinja template into three semantic section groups, and finally rebalance CSS spacing/hierarchy so the PDF reads in the order “who the student is → current analysis → what to do next”.

**Tech Stack:** Python `unittest`, Jinja2 templates, CSS for Playwright PDF rendering

---

### Task 1: Add failing regression tests for page 4 information architecture

**Files:**
- Modify: `scripts/test_report_density_layout.py`
- Test: `scripts/test_report_density_layout.py`

**Step 1: Write the failing test**

Add tests that verify:
- page 4 contains three major section wrappers in order
- the profile card appears before the quick overview card in the top row
- the analysis section surfaces the progress block before the metric cards
- the metric tags render in the order: 当前水平 → 当前状态 → 目标差距 → 突破口

**Step 2: Run test to verify it fails**

Run:
```bash
python3 -m unittest scripts.test_report_density_layout.ReportDensityLayoutTest.test_sample_01_page4_uses_three_section_information_architecture -v
```
Expected: FAIL because the current template does not yet have the new wrappers/order.

**Step 3: Write minimal implementation**

No production implementation yet. Only the test code should be added in this task.

**Step 4: Run test to verify it fails for the intended reason**

Run the same command again and confirm the failure is caused by missing structure/order, not a typo.

**Step 5: Commit**

```bash
git add scripts/test_report_density_layout.py
git commit -m "test(report): capture page 4 layout structure"
```

### Task 2: Refactor `student_profile.jinja2` into three non-redundant sections

**Files:**
- Modify: `templates/pages/student_profile.jinja2`
- Test: `scripts/test_report_density_layout.py`

**Step 1: Write the failing test**

Reuse the test added in Task 1 as the red state for this task.

**Step 2: Run test to verify it fails**

Run:
```bash
python3 -m unittest scripts.test_report_density_layout.ReportDensityLayoutTest.test_sample_01_page4_uses_three_section_information_architecture -v
```
Expected: FAIL.

**Step 3: Write minimal implementation**

Refactor the template to:
- wrap content in three major groups: overall summary, overall analysis, intervention focus
- move `学生档案` to the left of the top row
- place `学习画像速览` to the right of the top row
- move `学习画像结论` into the first major section instead of keeping it as a competing parallel block in the analysis area
- place the progress block before the metric cards in the analysis section
- reorder the metric cards to 当前水平 / 当前状态 / 目标差距 / 突破口
- keep weak-domain detail inside the analysis section
- keep bottom cards action-oriented so they do not restate the same diagnosis

**Step 4: Run test to verify it passes**

Run:
```bash
python3 -m unittest scripts.test_report_density_layout.ReportDensityLayoutTest.test_sample_01_page4_uses_three_section_information_architecture -v
```
Expected: PASS.

**Step 5: Commit**

```bash
git add templates/pages/student_profile.jinja2 scripts/test_report_density_layout.py
git commit -m "feat(report): restructure page 4 information flow"
```

### Task 3: Rebalance CSS spacing, grouping, and visual hierarchy for PDF readability

**Files:**
- Modify: `templates/css/student_profile.css`
- Test: `scripts/test_report_density_layout.py`

**Step 1: Write the failing test**

Use the existing HTML structure test as the safety net, and add/verify class hooks needed for section grouping if required.

**Step 2: Run test to verify baseline still passes/fails appropriately**

Run:
```bash
python3 -m unittest scripts.test_report_density_layout -v
```
Expected: existing tests pass except any structure tests not yet satisfied.

**Step 3: Write minimal implementation**

Update CSS to:
- create obvious gaps between the three major sections
- strengthen the analysis section visual anchor around the progress block
- reduce equal-weight styling across all blocks
- preserve print-safe layout and density variants
- keep cards within page-break-safe rules

**Step 4: Run tests to verify they pass**

Run:
```bash
python3 -m unittest scripts.test_report_density_layout -v
```
Expected: PASS.

**Step 5: Commit**

```bash
git add templates/css/student_profile.css scripts/test_report_density_layout.py
git commit -m "style(report): improve page 4 section hierarchy"
```

### Task 4: Verify rendered output with the reference sample

**Files:**
- Modify: none required unless verification reveals issues
- Test: rendered HTML/PDF artifacts from sample 01

**Step 1: Render the reference sample HTML**

Run:
```bash
python3 scripts/render_standalone.py samples/json/sample_01_math_25q.json -o samples/output/page4_restructure_check.html
```
Expected: HTML generated successfully.

**Step 2: Render the reference sample PDF**

Run:
```bash
python3 scripts/render_standalone.py samples/json/sample_01_math_25q.json -o samples/output/page4_restructure_check.html --pdf
```
Expected: PDF generated successfully.

**Step 3: Inspect page count and page-4 text markers**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
import fitz
pdf = Path('samples/output/page4_restructure_check.pdf')
doc = fitz.open(pdf)
print('pages=', doc.page_count)
print(doc.load_page(3).get_text('text')[:1200])
PY
```
Expected: 16-page PDF remains valid and page 4 contains the new section markers/order.

**Step 4: Run broader regression check**

Run:
```bash
python3 -m unittest scripts.test_report_density_layout scripts.test_report_data_consistency -v
```
Expected: PASS.

**Step 5: Commit**

```bash
git add samples/output/page4_restructure_check.html samples/output/page4_restructure_check.pdf
git commit -m "test(report): verify page 4 restructure against sample 01"
```
