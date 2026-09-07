# Build the Benchmark Radar technical report.
#
#   make        -> main.pdf
#   make arxiv  -> arxiv.tar.gz, the self-contained arXiv upload
#   make clean  -> remove build intermediates

LATEXMK ?= latexmk

.PHONY: all arxiv clean

all: main.pdf

main.pdf: main.tex references.bib $(wildcard figures/*)
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error main.tex

# arXiv runs no BibTeX pass, so the upload ships the built main.bbl.
arxiv: main.pdf
	tar -czf arxiv.tar.gz main.tex main.bbl figures

clean:
	$(LATEXMK) -C
	rm -f arxiv.tar.gz
