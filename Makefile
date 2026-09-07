# Build the Benchmark Radar technical report.
#
#   make        -> main.pdf
#   make arxiv  -> arxiv.tar.gz, the self-contained arXiv upload
#   make clean  -> remove build intermediates

LATEXMK ?= latexmk

# Use-case screenshots are shared with the rest of the repository, so the source
# tree keeps one copy and the arXiv target stages a flat build directory.
SHARED_FIGURES := ../../../assets/use-case-492

.PHONY: all arxiv clean

all: main.pdf

main.pdf: main.tex references.bib $(wildcard figures/*) $(wildcard $(SHARED_FIGURES)/*)
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error main.tex

# arXiv runs no BibTeX pass, so the upload ships the built main.bbl. Every figure
# is flattened into figures/ because the shared path does not exist upstream.
arxiv: main.pdf
	rm -rf build/arxiv
	mkdir -p build/arxiv/figures
	cp main.tex main.bbl build/arxiv/
	cp figures/* $(SHARED_FIGURES)/* build/arxiv/figures/
	sed -i.bak 's|{{figures/}{$(SHARED_FIGURES)/}}|{{figures/}}|' build/arxiv/main.tex
	rm -f build/arxiv/main.tex.bak
	tar -czf arxiv.tar.gz -C build/arxiv .

clean:
	$(LATEXMK) -C
	rm -rf build arxiv.tar.gz
