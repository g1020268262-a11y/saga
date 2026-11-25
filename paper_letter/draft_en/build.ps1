$ErrorActionPreference = 'Stop'
$savedTexInputs = $env:TEXINPUTS
$savedBstInputs = $env:BSTINPUTS
$savedBibInputs = $env:BIBINPUTS
$paperDir = Split-Path -Parent $PSScriptRoot
$templateDir = Join-Path $paperDir 'ieice_template'

Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Path build -Force | Out-Null
    # Retain the TeX distribution's default search paths.
    $env:TEXINPUTS = "$templateDir;$savedTexInputs;"
    $env:BSTINPUTS = "$templateDir;$savedBstInputs;"
    $env:BIBINPUTS = "$paperDir;$savedBibInputs;"

    & xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build main.tex
    if ($LASTEXITCODE -ne 0) { throw 'Initial XeLaTeX pass failed.' }

    & bibtex build/main
    if ($LASTEXITCODE -ne 0) { throw 'BibTeX failed.' }

    & xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build main.tex
    if ($LASTEXITCODE -ne 0) { throw 'Second XeLaTeX pass failed.' }

    & xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build main.tex
    if ($LASTEXITCODE -ne 0) { throw 'Final XeLaTeX pass failed.' }

    Copy-Item -LiteralPath build/main.pdf -Destination main.pdf -Force
    Write-Output (Join-Path $PSScriptRoot 'main.pdf')
}
finally {
    $env:TEXINPUTS = $savedTexInputs
    $env:BSTINPUTS = $savedBstInputs
    $env:BIBINPUTS = $savedBibInputs
    Pop-Location
}
