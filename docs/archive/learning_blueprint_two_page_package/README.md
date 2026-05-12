# Learning Blueprint Two-Page Package

This package implements two opening blueprint pages for a student learning analysis report:

1. `m00_student_diagnostic_blueprint.jinja2` — Page 1: student diagnostic panorama.
2. `m01_tutoring_execution_blueprint.jinja2` — Page 2: tutoring execution and tracking panorama.

The implementation uses:

- Jinja2 templates for structure and dynamic fields.
- CSS Grid and existing report design tokens for layout and style.
- Inline SVG for the math ability map, AI engine, and collaboration diagrams.
- A Python builder that converts the existing RenderPayload into stable view-models.

## Package structure

```text
src_v2/services/learning_blueprint_builder.py
templates_v2/m00_student_diagnostic_blueprint.jinja2
templates_v2/m01_tutoring_execution_blueprint.jinja2
templates_v2/css/m00_learning_blueprint.css
templates_v2/assets/learning_blueprint/*.svg
scripts/build_learning_blueprint_preview.py
examples/sample_blueprint_view_model.json
examples/learning_blueprint_preview.html
patches/*.diff
```

## Integration summary

1. Copy `learning_blueprint_builder.py` into `src_v2/services/`.
2. Copy both Jinja2 templates into `templates_v2/`.
3. Copy `m00_learning_blueprint.css` into `templates_v2/css/`.
4. In `html_renderer.py`, call `build_learning_blueprints(payload)` and merge the result into the Jinja context.
5. In `report_master.jinja2`, include the two templates after the cover page.

See `IMPLEMENTATION_GUIDE_CN.md` for a detailed Chinese integration guide.
