Parsera

See grammars, parse trees and stacks come alive.

Parsera is a desktop learning tool for compiler construction, built with pure Python and Tkinter. It turns abstract topics such as parse trees, ambiguity and operator precedence into step-by-step animations that you can play, pause, rewind and speed up.

Wherever a stack appears, an animated teacher, Prof. Lambda, operates it: he tosses a coin on every push, catches it on every pop, cheers when a step succeeds and panics on a syntax error.

📹 Add a demo GIF or video here, for example docs/demo.gif.

✨ Features

Parsera has six modules, each one a tab in the sidebar:

#	Module	What it does
1	Grammar → Parse Tree	Enter a context-free grammar and a string. Watch the leftmost derivation being built, step by step, as a parse tree.
2	Ambiguity Detect	Checks whether a grammar is ambiguous. If it is, both competing parse trees of the same string are shown side by side.
3	Make Unambiguous	Rewrites an ambiguous expression grammar into an unambiguous one using precedence levels and associativity (left or right), then verifies that the language is unchanged.
4	Parse Tree → AST	Collapses a parse tree into an Abstract Syntax Tree, animated, with the resulting prefix and postfix forms.
5	Infix → Prefix/Postfix	Converts expressions with a live operator stack, an input token row and an output tray (shunting-yard style, with brackets and priorities).
6	Operator Precedence Parser	Parses an expression with a precedence relation table (<, =, >), a live stack and a parse tree built step by step. Reports syntax errors.
🧑‍🏫 The animated teacher (Tabs 5 and 6)
Push: the teacher tosses the coin on top of the stack, the coin lands with a squash and a ring, and he cheers.
Pop: he flicks the top coin off, catches it with a surprised face, then smiles.
Reduce: several pops followed by a push play as a quick chain.
Empty stack: he announces "Empty!".
Error: he looks worried and shakes his head ("Syntax error!").
The animation speed follows the player's Slow / Normal / Fast setting.
🎛️ Player controls

Every animated module has Restart, Back, Play/Pause, Next, a seek bar and a speed selector, so you can slow down at exactly the step that confuses you.

🎨 Interface

Modern dark-slate sidebar, card-based layout, animated splash screen and rounded custom widgets, all drawn on Tkinter canvases (no external UI libraries).

🚀 Getting started
Requirements
Python 3.8 or newer
Tkinter (included with the standard Python installer on Windows and macOS)

No pip install is needed. The project has no third-party dependencies.

Linux: if Tkinter is missing, install it with your package manager, e.g. sudo apt install python3-tk.

Run
bash
git clone https://github.com/<your-username>/parsera.git
cd parsera
python main.py
📁 Project structure
parsera/
├── main.py        # App window, sidebar navigation, entry point
├── splash.py      # Animated welcome / loading screen
├── tabs.py        # The six tabs (Tab1 … Tab6)
├── ui_common.py   # Theme, custom widgets, player, tree canvas, StackView + animated teacher
└── core.py        # Pure logic (no GUI): grammar parsing, ambiguity, rewriting, AST, conversion, OPP

Design note: core.py contains only algorithms and no GUI code, so the logic can be tested independently of the interface.

🧠 How it works (short overview)
Grammar engine: parses rules like E -> E + E | E * E | ( E ) | id, tokenizes the input string and counts or builds all parse trees (capped, to detect ambiguity).
Ambiguity detection: generates strings of the language up to a given length and checks whether any of them has more than one parse tree.
Unambiguous rewriting: infers the operator structure of the grammar, then layers it by precedence and associativity and verifies the new grammar against the old one.
Conversion and parsing: each algorithm produces a list of frames (state snapshots). The player simply steps through them, which is why Back, Seek and Speed all work smoothly.
🧪 Try these examples
Module	Grammar	Input
Ambiguity	E -> E + E | E * E | ( E ) | id	id + id * id
Parse Tree → AST	E -> E + T | T, T -> T * F | F, F -> ( E ) | id	id + id * id
Infix → Postfix	–	a * ( b + c )
Operator Precedence	E -> E + T | T, T -> T * F | F, F -> ( E ) | id	a + b * ( c - d ) ^ 2
