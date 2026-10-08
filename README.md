# packmol_util
[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/ohara-lab-su/packmol_util/blob/main/README.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/ohara-lab-su/packmol_util/blob/main/README.ja.md)


A **Python utility kit for automatically generating amorphous initial structures (POSCAR)** for first-principles calculations (VASP) and molecular dynamics (MD) simulations using Packmol.

By specifying only the stoichiometric ratio, density (mass density or number density), and total number of atoms, this tool automatically completes the full workflow: generating the Packmol input file, running Packmol, and outputting a POSCAR in VASP format with Direct coordinates.

---

## 💡 Features

1. **Intuitive density specification**
   - Packmol itself does not interpret density or atomic weights, but this tool performs the required internal calculations and determines the cubic cell length $L$ that satisfies the specified density.
2. **Exclusion radius specification by element symbol**
   - This hides Packmol's inconvenient atom-index-based specification inside XYZ files. Interatomic avoidance distances can be controlled using an intuitive element-name-based dictionary, such as `{"P": 0.25, "O": 1.05}`.
3. **Preservation of molecular units (geometries)**
   - For systems such as $\text{Li}_3\text{PO}_4$, amorphization through mixing and packing can be performed while preserving intramolecular bond lengths, such as those in $\text{PO}_4$ tetrahedra.
4. **Extremely simple high-level API**
   - By using `AmorphousBuilder`, the cumbersome file relay workflow (`.inp` construction $\rightarrow$ external execution $\rightarrow$ coordinate conversion) can be condensed into only a few lines of script.

---

## 📁 Directory structure

```text
src/
├── packmol_util/
│
│   ├── __init__.py          # Package initialization file
│   ├── builder.py           # High-level integrated builder (AmorphousBuilder) ★NEW
│   ├── model.py             # Template XYZ generation and structure-definition module
│   ├── packmol.py           # Core density calculation, Packmol execution, and POSCAR conversion
│   ├── packmol_inp.py       # Parsing engine for constructing packmol.inp
│   ├── param.py             # Atomic weights and physical constants for the periodic table

└── example/                 # Location for material-specific generation scripts
    ├── Li3PO4/
    │   └── make_Li3PO4.py
    └── FeSiB/
        └── make_FeSiB.py
```
