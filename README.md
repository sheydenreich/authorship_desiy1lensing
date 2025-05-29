# Authorship Management Tool for DESI Y1 Lensing Papers

This tool automates the generation of author lists and affiliations for DESI Y1 Lensing papers. It processes CSV files containing author information and generates properly formatted LaTeX output suitable for journal submissions.

## Features

- **Hierarchical Author Ordering**: Supports first-tier authors followed by infrastructure authors, then remaining authors alphabetically
- **ORCID Integration**: Automatically includes ORCID links in LaTeX output
- **Fuzzy Matching**: Interactive matching for infrastructure authors when exact names don't match
- **Multiple Output Formats**: 
  - Standard AASTeX format with author/affiliation blocks
  - Numbered affiliation format with superscript references for manual author lists
  - CSV output for journal submission forms
- **Email Integration**: Merges author emails from user database

## Requirements

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### Dependencies
- `numpy`: Array operations and data manipulation
- `astropy`: Reading/writing scientific data tables
- `fuzzywuzzy`: Fuzzy string matching for author name resolution
- `python-Levenshtein`: Improves fuzzy matching performance

## Input Files

### CSV Author Data (Auto-generated)
The main input CSV file is generated automatically from the DESI members database.

### Author Lists
Two text files define author categories:

**`first_tier_authors.dat`**: Key contributors listed in specified order
```
Sven Heydenreich
Alexie Leauthaud
Chris Blake
...
```

**`infrastructure_authors.dat`**: Y1 Lensing infrastructure authors (sorted alphabetically by last name)
```
Chris Blake
Joseph DeRose
Ni Putu Audita Placida Emas
...
```

## Usage

### Basic Usage
```bash
python authors.py input_authors.csv output_authors.tex output_authors.csv \
    --first-tier first_tier_authors.dat \
    --infrastructure infrastructure_authors.dat
```

### With Numbered Affiliations
```bash
python authors.py input_authors.csv output_authors.tex output_authors.csv \
    --first-tier first_tier_authors.dat \
    --infrastructure infrastructure_authors.dat \
    --alt-authors-tex numbered_authors.tex \
    --alt-affiliations-tex numbered_affiliations.tex
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `input_csv` | Input CSV file with author information (required) |
| `output_tex` | Output LaTeX file for author list (required) |
| `output_csv` | Output CSV file for journal submission (required) |
| `--first-tier` | File with first-tier authors (required) |
| `--infrastructure` | File with infrastructure authors (required) |
| `--users-csv` | CSV file with user emails (default: Users.csv) |
| `--alt-authors-tex` | Alternative output: authors with numbered affiliations |
| `--alt-affiliations-tex` | Alternative output: numbered affiliations list |
| `--no-fuzzy-matching` | Disable interactive fuzzy matching |
| `--no-orcid-links` | Disable ORCID links in output |

## LaTeX Setup

### Required Packages

For ORCID links to work properly in your LaTeX document, include these packages **in this specific order**:

```latex
\usepackage{hyperref}
\usepackage{orcidlink}
```

**Important**: The `orcidlink` package must be loaded **after** `hyperref` for proper functionality.

### Example LaTeX Usage

#### Standard AASTeX Format
```latex
\documentclass{aastex631}
\usepackage{hyperref}
\usepackage{orcidlink}

\begin{document}
\input{output_authors.tex}
\end{document}
```

#### Numbered Affiliation Format
```latex
\documentclass{article}
\usepackage{hyperref}
\usepackage{orcidlink}

\begin{document}
\author{
\input{numbered_authors.tex}
}

\input{numbered_affiliations.tex}
\end{document}
```

## Output Files

### `output_authors.tex`
Standard AASTeX format with `\author{}` and `\affiliation{}` commands:
```latex
\orcidlink{0000-0000-0000-0000}\author[0000-0000-0000-0000]{John Doe}
\affiliation{University of Example}

\author{Jane Smith}
\affiliation{Example Institute}
```

### `numbered_authors.tex` (Alternative Format)
Authors with superscript affiliation numbers:
```latex
\orcidlink{0000-0000-0000-0000}John Doe,$^{1,2}$
Jane Smith,$^{2}$
```

### `numbered_affiliations.tex` (Alternative Format)
Numbered affiliation list:
```latex
$^{1}$ University of Example \\
$^{2}$ Example Institute \\
```

### `output_authors.csv`
CSV file for journal submission forms with columns: Order, Firstname, Lastname, Email

## Author Ordering Logic

1. **First-tier authors**: Listed in the exact order specified in `first_tier_authors.dat`
2. **Infrastructure authors**: Listed alphabetically by last name (excluding those already in first-tier)
3. **Remaining authors**: All other authors listed alphabetically by last name

## Interactive Features

When infrastructure authors are not found exactly, the tool offers fuzzy matching:
```
Infrastructure author 'J. Doe' not found exactly.
Possible matches:
  1. John Doe (confidence: 95%)
  2. Jane Doe (confidence: 85%)
  0. None of the above (skip this author)
Select match (0-2): 1
```

Use `--no-fuzzy-matching` to disable this interactive mode.

## Error Handling

- Missing first-tier authors cause the script to exit with an error
- Infrastructure authors that cannot be matched are reported but don't stop execution
- Missing email database generates warnings but continues processing
- Duplicate authors are automatically merged with combined affiliations

## Examples

See the included sample files:
- `first_tier_authors.dat`: Example first-tier author list
- `infrastructure_authors.dat`: Example infrastructure author list

These demonstrate the expected input format for author name files.
