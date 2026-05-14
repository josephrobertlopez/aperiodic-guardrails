#!/bin/bash
# Build paper using docker texlive (the local conda texlive is broken).
# Output: paper/main.pdf, paper/main.log
set -e
cd "$(dirname "$0")/.."
docker run --rm -v "$PWD/paper:/work" -w /work texlive/texlive:latest bash -c '
  cd /work
  pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1 || true
  bibtex main 2>&1 | tail -5 || true
  pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1 || true
  pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1 || true
  echo "===BUILD DONE==="
  echo "ERRORS:"
  grep -anE "^! " main.log | head -30 || echo "  (none)"
  echo "WARNINGS:"
  grep -aE "Warning:" main.log | head -30 || echo "  (none)"
  echo "UNDEFINED CITES/REFS:"
  grep -aE "(undefined|There were)" main.log | grep -avE "of your error" | head -10 || echo "  (none)"
'
