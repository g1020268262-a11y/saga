$ErrorActionPreference = 'Stop'
$savedTexInputs = $env:TEXINPUTS
$savedBstInputs = $env:BSTINPUTS
$savedBibInputs = $env:BIBINPUTS
Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Path build -Force | Out-Null
    # The trailing semicolon retains the TeX distribution's default paths.
    $env:TEXINPUTS = "$PSScriptRoot/ieice_template;$savedTexInputs;"
    $env:BSTINPUTS = "$PSScriptRoot/ieice_template;$savedBstInputs;"
    $env:BIBINPUTS = "$PSScriptRoot;$savedBibInputs;"
    & pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build main.tex
    if ($LASTEXITCODE -ne 0) { throw 'Initial pdflatex pass failed.' }
    & bibtex build/main
    if ($LASTEXITCODE -ne 0) { throw 'BibTeX failed.' }
    & pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build main.tex
    if ($LASTEXITCODE -ne 0) { throw 'Second pdflatex pass failed.' }
    & pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build main.tex
    if ($LASTEXITCODE -ne 0) { throw 'Final pdflatex pass failed.' }
    Copy-Item -LiteralPath build/main.pdf -Destination main.pdf
}
finally {
    $env:TEXINPUTS = $savedTexInputs
    $env:BSTINPUTS = $savedBstInputs
    $env:BIBINPUTS = $savedBibInputs
    Pop-Location
}
