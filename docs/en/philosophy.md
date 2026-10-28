# Design Philosophy

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/packmol_util/en/philosophy.html) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/packmol_util/ja/philosophy.html)

## Work at a higher level than Packmol input

Packmol directly handles structure templates, the number of copies, placement regions, minimum separation distances, and related parameters.

When constructing a structure, however, users generally start from composition ratios, total atom counts, mass or number densities, and molecular or structural units.

`packmol_util` separates these two levels.

```text
Composition / total atom count / density / structural units
                │
                ▼
           packmol_util
                │
                ▼
 structure / number / inside box / radius
                │
                ▼
              Packmol
```

The intended interface is to specify conditions as Python data rather than manually assemble Packmol input text.

## High-level and low-level interfaces

For ordinary structure generation, `AmorphousBuilder` is the entry point.

Lower-level classes can also be used independently to calculate cell dimensions, generate Packmol input, run Packmol, or convert XYZ files to POSCAR format.

```text
AmorphousBuilder
      │
      ├── model
      ├── PackmolInp
      └── Packmol
```

The high-level interface does not conceal all functionality: users can access only the layer they need.

## `builder`

`AmorphousBuilder` integrates the overall workflow.

It primarily manages:

- Composition ratios
- Total atom count
- Mass density or number density
- Minimum separation distance
- Templates to be placed by Packmol

It determines the number of composition units from the ratios and total atom count, calculates the cell size from the density, and passes registered templates to Packmol input generation.

## `packmol`

`Packmol` handles execution of Packmol and associated operations.

It performs density and cell-size calculations, runs Packmol, and converts XYZ to POSCAR. These operations are separate from the definitions of structure templates.

## `packmol_inp`

`PackmolInp` translates Python-side settings into Packmol input syntax.

For example, a registered structure becomes a Packmol block of the form:

```text
structure ...
    number ...
    inside box ...
end structure
```

When packing radii are supplied by element symbol, the symbols are mapped to Packmol atom indices using the atom order in the XYZ template.

## `model`

`model` manages structure templates passed to Packmol.

It can create templates containing a single atom or multi-atom structural units such as PO4.

The important distinction is between:

- Internal geometry of a molecule or structural unit
- Exclusion distances used when Packmol places templates

For example, the P–O distance within PO4 belongs to the geometry of its XYZ template; it is not a packing radius.

## Composition ratios and total atom count

A composition ratio of `[3, 1, 4]` represents eight atoms per composition unit.

The total atom count must be compatible with an integer number of such units if the exact ratio is to be preserved.

`AmorphousBuilder` adjusts the requested count to be consistent with the composition ratio and stores the actual total atom count and multiplier.

The multiplier is available as `builder.multiplier` and can be used to determine the number of template copies.

## Determining the cell size from density

The relationship between number density \(\rho_N\), total atom count \(N\), and cubic cell edge length \(L\) is:

\[
L = \left(\frac{N}{\rho_N}\right)^{1/3}
\]

If mass density is specified, the mean atomic mass is calculated from the composition and used to convert mass density to number density before determining the cell size.

Density is converted into a placement region in Python before Packmol is invoked; Packmol itself is not asked to interpret the density.
