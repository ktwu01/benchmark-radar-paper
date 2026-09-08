# Build the manuscript and native TikZ figures from dated TeX inputs.
LATEXMK ?= latexmk
FIGURE_NAMES := corpus-evidence cover-metrics pipeline-evaluation search-surface source-composition
FIGURE_PDFS := $(addprefix figures/,$(addsuffix .pdf,$(FIGURE_NAMES)))
FIGURE_SOURCES := $(addprefix figures/,$(addsuffix .tex,$(FIGURE_NAMES)))

.PHONY: all figures arxiv clean

all: main.pdf

figures: $(FIGURE_PDFS)

figures/%.pdf: figures/%.tex figures/figure-style.tex figure-data.tex catalog-data.tex Makefile
	cd figures && $(LATEXMK) -g -pdf -interaction=nonstopmode -halt-on-error $*.tex

figures/corpus-evidence.pdf: figures/corpus-evidence-body.tex

main.pdf: main.tex references.bib figure-data.tex catalog-data.tex findings-data.tex figures/corpus-evidence-body.tex $(FIGURE_PDFS) $(wildcard figures/*.png) Makefile
	$(LATEXMK) -g -pdf -interaction=nonstopmode -halt-on-error main.tex

# arXiv runs no BibTeX pass. Ship main.bbl, the dated numbers, native drawings,
# and finished figures. All paper assets live in this repository.
arxiv: main.pdf
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error main.tex
	rm -rf build/arxiv
	mkdir -p build/arxiv/figures
	cp main.tex main.bbl figure-data.tex catalog-data.tex findings-data.tex build/arxiv/
	cp $(FIGURE_PDFS) $(FIGURE_SOURCES) figures/figure-style.tex figures/corpus-evidence-body.tex figures/*.png build/arxiv/figures/
	tar -czf arxiv.tar.gz -C build/arxiv .

# Keep tracked PDFs; remove only intermediates and the upload staging area.
clean:
	$(LATEXMK) -c main.tex
	cd figures && $(LATEXMK) -c $(addsuffix .tex,$(FIGURE_NAMES))
	rm -rf build arxiv.tar.gz
