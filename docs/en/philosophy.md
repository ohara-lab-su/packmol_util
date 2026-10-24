# Design principles

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/packmol_util/en/philosophy.html) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/packmol_util/ja/philosophy.html)


## A higher-level interface to Packmol

Packmol operates on structure templates, placement counts, placement regions, and minimum separation distances. Users preparing structures, however, usually start from composition ratios, total atom counts, mass or number densities, and molecular or structural units.

`packmol_util` separates these two levels:

```text
Composition / total atoms / density / structural units
                         |
                         v
                    packmol_util
                         |
                         v
        structure / number / inside box / radius
                         |
                         v
                       Packmol
```

The intended interface accepts these conditions as Python data rather than requiring users to assemble Packmol input text themselves.

## High-level and low-level interfaces

For routine structure generation, use `AmorphousBuilder`. Lower-level components remain available for cell-size calculations, Packmol input generation and execution, and XYZ-to-POSCAR conversion.

```text
AmorphousBuilder
      |
      +-- model
      +-- PackmolInp
      +-- Packmol
```

This separation allows users to work directly with only the layer they need.

## `builder`

`AmorphousBuilder` coordinates composition ratios, total atom count, mass or number density, minimum separation, and placement templates. It determines the multiplier for a composition unit, calculates the cell size from density, and passes registered templates to the Packmol input layer.

## `packmol`

`Packmol` handles Packmol execution and supporting numerical operations, including density and cell-size calculations and XYZ-to-POSCAR conversion. Template definitions are managed separately.

## `packmol_inp`

`PackmolInp` converts Python-side configuration into Packmol input syntax:

```text
structure ...
    number ...
    inside box ...
end structure
```

When packing radii are specified by element symbol, the module maps them to Packmol atom indices according to the atom order in the XYZ template.

## `model`

`model` manages structure templates, including single atoms and multi-atom units such as PO4. The geometry inside a structural unit and the exclusion distances used during packing are distinct: the P–O distance belongs to the XYZ template geometry, not to the packing radius.

## Composition ratios and total atom count

A composition ratio of `[3, 1, 4]` represents eight atoms per composition unit. The total atom count must preserve complete composition units. `AmorphousBuilder` determines the consistent atom count and multiplier; the multiplier is available as `builder.multiplier` and can be used to determine template placement counts.

## Cell size from density

For number density $\rho_N$, total atom count $N$, and cubic cell edge length $L$:

$$
L = \left(\frac{N}{\rho_N}\right)^{1/3}
$$

For mass density, the library calculates the mean atomic mass from composition, converts to number density, and determines the cell size before passing the placement region to Packmol.
