# Build the manuscript and native TikZ figures from dated TeX inputs.
LATEXMK ?= latexmk
PYTHON ?= python3
SHARED_FIGURES := ../../../assets/use-case-492
FIGURE_NAMES := cover-metrics pipeline-evaluation search-surface source-composition
FIGURE_PDFS := $(addprefix figures/,$(addsuffix .pdf,$(FIGURE_NAMES)))
FIGURE_SOURCES := $(addprefix figures/,$(addsuffix .tex,$(FIGURE_NAMES)))

.PHONY: all figures refresh-figure-data check-figure-data arxiv clean

all: main.pdf

figures: $(FIGURE_PDFS)

figures/%.pdf: figures/%.tex figures/figure-style.tex figure-data.tex Makefile
	cd figures && $(LATEXMK) -g -pdf -interaction=nonstopmode -halt-on-error $*.tex

main.pdf: main.tex references.bib figure-data.tex $(FIGURE_PDFS) figures/abstract_overview.png $(wildcard $(SHARED_FIGURES)/*) Makefile
	$(LATEXMK) -g -pdf -interaction=nonstopmode -halt-on-error main.tex

# Explicit refresh only: first rebuild and audit the corpus from the repo root.
# Normal TeX builds use the checked-in snapshot and need no Python or live data.
refresh-figure-data:
	$(PYTHON) ../../../scripts/export_report_figure_data.py

check-figure-data:
	$(PYTHON) ../../../scripts/export_report_figure_data.py --check

# arXiv runs no BibTeX pass. Ship main.bbl, the dated numbers, native drawings,
# and finished figures; shared screenshots are flattened into figures/.
arxiv: main.pdf
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error main.tex
	rm -rf build/arxiv
	mkdir -p build/arxiv/figures
	cp main.tex main.bbl figure-data.tex build/arxiv/
	cp $(FIGURE_PDFS) $(FIGURE_SOURCES) figures/figure-style.tex figures/*.png $(SHARED_FIGURES)/*.png build/arxiv/figures/
	sed -i.bak 's|{{figures/}{$(SHARED_FIGURES)/}}|{{figures/}}|' build/arxiv/main.tex
	rm -f build/arxiv/main.tex.bak
	tar -czf arxiv.tar.gz -C build/arxiv .

# Keep tracked PDFs; remove only intermediates and the upload staging area.
clean:
	$(LATEXMK) -c main.tex
	cd figures && $(LATEXMK) -c $(addsuffix .tex,$(FIGURE_NAMES))
	rm -rf build arxiv.tar.gz
