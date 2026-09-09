# Build the manuscript and native TikZ figures from dated TeX inputs.
LATEXMK ?= latexmk
PYTHON ?= python3
FIGURE_NAMES := corpus-evidence cover-metrics pipeline-evaluation search-surface source-composition
FIGURE_PDFS := $(addprefix figures/,$(addsuffix .pdf,$(FIGURE_NAMES)))
FIGURE_SOURCES := $(addprefix figures/,$(addsuffix .tex,$(FIGURE_NAMES)))
# Drawn from the classified catalog and committed as finished PDFs.
TAXONOMY_FIGURES := figures/taxonomy-sankey.pdf figures/taxonomy-trends.pdf

.PHONY: all figures arxiv check-small-numbers clean

all: check-small-numbers

figures: $(FIGURE_PDFS)

figures/%.pdf: figures/%.tex figures/figure-style.tex figure-data.tex catalog-data.tex Makefile
	cd figures && $(LATEXMK) -g -pdf -interaction=nonstopmode -halt-on-error $*.tex

figures/corpus-evidence.pdf: figures/corpus-evidence-body.tex

main.pdf: main.tex references.bib figure-data.tex catalog-data.tex findings-data.tex taxonomy-data.tex taxonomy-trend-data.tex figures/corpus-evidence-body.tex $(FIGURE_PDFS) $(TAXONOMY_FIGURES) $(wildcard figures/*.png) Makefile
	$(LATEXMK) -g -pdf -interaction=nonstopmode -halt-on-error main.tex

# Scan rendered text and raster figures on every normal build, even if the PDF
# is up to date. Small numbers warn; unreadable inputs or missing tools fail.
check-small-numbers: main.pdf
	mkdir -p build
	$(PYTHON) scripts/check_small_numbers.py main.pdf --json-output build/small-number-warnings.json

# arXiv runs no BibTeX pass. Ship main.bbl, the dated numbers, native drawings,
# and finished figures. All paper assets live in this repository.
arxiv: check-small-numbers
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error main.tex
	rm -rf build/arxiv
	mkdir -p build/arxiv/figures
	cp main.tex main.bbl figure-data.tex catalog-data.tex findings-data.tex taxonomy-data.tex taxonomy-trend-data.tex build/arxiv/
	cp $(FIGURE_PDFS) $(TAXONOMY_FIGURES) $(FIGURE_SOURCES) figures/figure-style.tex figures/corpus-evidence-body.tex figures/*.png build/arxiv/figures/
	tar -czf arxiv.tar.gz -C build/arxiv .

# Keep tracked PDFs; remove only intermediates and the upload staging area.
clean:
	$(LATEXMK) -c main.tex
	cd figures && $(LATEXMK) -c $(addsuffix .tex,$(FIGURE_NAMES))
	rm -rf build arxiv.tar.gz
