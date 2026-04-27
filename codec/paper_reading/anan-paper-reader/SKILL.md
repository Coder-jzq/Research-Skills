---
name: anan-paper-reader
description: Read and analyze one academic paper PDF with AnAn Paper Reader, extracting metadata, paper structure, method, model/framework figure evidence, experiments, ablations, analysis, and limitations, then producing a structured Chinese paper-reading summary for group meetings, research discussion, and personal study. Use when the user provides a paper PDF and asks to read, summarize, explain, analyze, present, or discuss it using AnAn Paper Reader or anan-paper-reader.
---

# AnAn Paper Reader

Use this skill to read one academic paper PDF and produce an accurate, structured Chinese paper-reading summary. Prioritize accuracy over completeness: never fabricate venue, corresponding authors, affiliations, datasets, baselines, metrics, results, or limitations.

## Workflow

1. Locate the single paper PDF. If multiple PDFs are plausible, ask which one to analyze.
2. Create an output directory near the PDF, for example `anan-paper-reader-output/`.
3. Run the bundled preprocessing helper from the skill root directory:

```bash
python3 scripts/extract_paper_context.py path/to/paper.pdf --out anan-paper-reader-output
```

If the Codex bundled Python runtime is available, prefer that executable because it may include PDF libraries. The helper writes:

- `paper_text.md`: page-by-page extracted text.
- `paper_metadata.json`: PDF metadata and extraction status.
- `section_snippets.md`: likely title/author, abstract, introduction, related work, method, experiments, conclusion, limitations, and appendix snippets.
- `figure_candidates.json`: captions/pages likely to contain an overview/framework/model/pipeline/method figure.

4. Read the generated files before writing the final answer. Return to the PDF when author blocks, equations, tables, or captions are unclear.
5. Use the model/framework figure as evidence when it is understandable from the caption, nearby text, and method section. Do not extract, crop, save, or output the figure image.
6. If text extraction fails or is mostly empty, try OCR or PDF-to-image conversion with available local tools. If it still fails, explain the failure in Chinese.
7. Use `references/output_template.md` as the required final-answer structure.

## Model Figure Handling

- Prefer figures whose caption or nearby text contains `Overview`, `Framework`, `Architecture`, `Model`, `Pipeline`, `Method`, or `Proposed Method`.
- Explain the figure in Chinese: overall structure, flow direction, key modules, correspondence with the method section, and whether the figure supports the claimed method design.
- If no clear model/framework figure exists, write `论文中未提供清晰的模型图或方法框架图。`
- If a figure exists but cannot be reliably understood, write `未能可靠理解论文中的模型图或方法图。`
- Do not create, crop, save, or list a model image file.

## Writing Rules

- Final output must be in Chinese.
- Keep paper titles, model names, method names, dataset names, and metric names in English when appropriate.
- Use simple Markdown: headings, concise bullets, and tables only when comparison is clearer.
- Use bold text only for important keywords or conclusions.
- Explain technical terms briefly in Chinese when they are important.
- Use plain language and concrete examples; do not only translate the abstract.
- When adding your own critical judgment, label it with `我的分析：`.
- If information is missing or uncertain, write `论文中未明确说明。` or `不确定。`
- Summarize experimental trends instead of copying every number. Include exact values only when needed to support a conclusion.
- Point out weak baselines, missing ablations, unsupported claims, or mismatches between motivation, method, and experiments when evidence supports the critique.

## Final Check

Before answering, verify that:

- The response starts with `# 论文精读总结`.
- Sections 1 through 13 from the template are present.
- The answer is Chinese except for names and technical terms that should remain English.
- No missing metadata or results are guessed.
- The model/framework figure is explained or the required uncertainty sentence is included.
