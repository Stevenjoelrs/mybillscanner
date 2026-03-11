#!/usr/bin/env python3
import random

# ====== Configuration ======
# Invalid ranges per denomination
INVALID_RANGES = {
    10: [(67250001, 67700000), (76310012, 85139995)],
    20: [(87280145, 91646549), (118700001, 119600000)],
    50: [(77100001, 77550000), (108050001, 108500000)],
}

# Desired counts per denomination and validity
COUNTS = {
    10: {'valid': 9, 'invalid': 9},
    20: {'valid': 8, 'invalid': 8},
    50: {'valid': 8, 'invalid': 8},
}

SCALE = 0.65  # Scale factor for two bills per row

# Font file paths - UPDATE THESE PATHS TO MATCH YOUR SYSTEM
# Option A: If fonts are in the same directory as your .tex file
FIRA_EXTRABOLD_PATH = "FiraSans-ExtraBold.ttf"
GOOGLE_SANS_REGULAR_PATH = "GoogleSansCode-Regular.ttf"

# Option B: If using system fonts (macOS/Linux paths as examples)
# FIRA_EXTRABOLD_PATH = "/usr/local/share/fonts/FiraSans-ExtraBold.ttf"
# GOOGLE_SANS_REGULAR_PATH = "~/Library/Fonts/GoogleSans-Regular.ttf"  # macOS example

# ====== Helper functions ======
def is_invalid(denom, serial):
    """Return True if serial is in any invalid range for the denomination."""
    for lo, hi in INVALID_RANGES[denom]:
        if lo <= serial <= hi:
            return True
    return False

def generate_valid_serial(denom):
    """Generate a random 9-digit serial not in any invalid range."""
    while True:
        serial = random.randint(1, 999999999)
        if not is_invalid(denom, serial):
            return serial

def generate_invalid_serial(denom):
    """Generate a random serial from one of the invalid ranges."""
    ranges = INVALID_RANGES[denom]
    lo, hi = random.choice(ranges)
    return random.randint(lo, hi)

def format_serial(serial):
    """Return serial as a zero-padded 9-digit string."""
    return f"{serial:09d}"

# ====== Generate all bills ======
bills = []

# Valid bills (Series A)
for denom, counts in COUNTS.items():
    for _ in range(counts['valid']):
        serial = generate_valid_serial(denom)
        bills.append((denom, format_serial(serial), 'A', 'valid'))

# Invalid bills (Series B)
for denom, counts in COUNTS.items():
    for _ in range(counts['invalid']):
        serial = generate_invalid_serial(denom)
        bills.append((denom, format_serial(serial), 'B', 'invalid'))

# Shuffle
random.shuffle(bills)

# ====== Generate LaTeX code with fontspec ======
latex_preamble = r"""\documentclass[a4paper]{article}
\usepackage{tikz}
\usepackage{longtable}
\usepackage{geometry}
\geometry{margin=1cm}

% Use fontspec with XeLaTeX or LuaLaTeX
\usepackage{fontspec}

% Load fonts from files (adjust paths as needed)
\newfontfamily\denomfont[
    Path = ./,          % Look in current directory - change if needed
    Extension = .ttf,
    UprightFont = *-ExtraBold,
    BoldFont = *-ExtraBold  % Same font for bold (no separate bold needed)
]{FiraSans}

\newfontfamily\serialfont[
    Path = ./,
    Extension = .ttf,
    UprightFont = *-Regular,
    BoldFont = *-Regular    % Same for bold
]{GoogleSansCode}

% Fallback for compilation without fonts (optional)
\newcommand{\denomstyle}[1]{{\denomfont #1}}
\newcommand{\serialstyle}[1]{{\serialfont #1}}

% Command to draw a single bill
% #1 = denomination, #2 = serial (9 digits), #3 = series, #4 = validity (1=valid,0=invalid)
\newcommand{\drawbill}[4]{%
  \begin{tikzpicture}
    \draw (0,0) rectangle (14,7);
    % top left small denomination
    \node[anchor=north west] at (1,6.5) {\small\denomstyle{#1}};
    % bottom left small denomination
    \node[anchor=south west] at (1,1.0) {\small\denomstyle{#1}};
    % bottom left serial + series
    \node[anchor=south west] at (1,0.5) {\serialstyle{#2 #3}};
    % top right serial + series
    \node[anchor=north east] at (13,6.5) {\serialstyle{#2 #3}};
    % bottom right large denomination (using the bold denomination font)
    \node[anchor=south east] at (13,0.5) {{\fontsize{50}{60}\selectfont\denomstyle{#1}}};
    % validity label
    \ifnum#4=1
      \node[anchor=south, gray!50] at (7,0.2) {\tiny VALID};
    \else
      \node[anchor=south, gray!50] at (7,0.2) {\tiny INVALID};
    \fi
  \end{tikzpicture}%
}

\begin{document}

\begin{center}
\begin{longtable}{cc}
\hline
\endhead
"""

latex_footer = r"""
\end{longtable}
\end{center}

\end{document}
"""

# Build table rows
rows = []
for i, (denom, serial, series, validity) in enumerate(bills):
    val_code = 1 if validity == 'valid' else 0
    bill_code = f"\\scalebox{{{SCALE}}}{{\\drawbill{{{denom}}}{{{serial}}}{{{series}}}{{{val_code}}}}}"
    if i % 2 == 0:
        rows.append(bill_code + " &")
    else:
        rows.append(bill_code + " \\\\")

print(latex_preamble)
print("\n".join(rows))
print(latex_footer)
