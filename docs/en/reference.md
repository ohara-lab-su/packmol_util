# Reference

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/packmol_util/en/reference.html) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/packmol_util/ja/reference.html)


This page describes the roles of the main components. The complete list of classes, methods, parameters, type annotations, and docstrings is generated in the {doc}`api/modules`.

## `AmorphousBuilder`

The high-level interface coordinating structure generation. It maintains elements and composition ratios, reconciles atom counts with composition units, determines the multiplier, computes cell size from mass or number density, registers Packmol templates, generates input, runs Packmol, and converts the result to POSCAR.

## `Packmol`

Handles Packmol execution and related numerical operations: atomic and mean atomic masses, mass-to-number-density conversion, cell-size calculations, Packmol execution, and XYZ-to-POSCAR conversion.

## `PackmolInp`

Builds Packmol input files from structure templates, placement counts, placement regions, and packing radii.

## `model`

Manages structure templates and recipes, including single-atom XYZ templates and multi-atom structural units.

## `Config`

Reads `packmol_util` configuration values from configuration files.

## `param`

Holds constants such as atomic masses used in density and cell-size calculations.

## API reference

```{toctree}
:maxdepth: 2

api/modules
```

The API pages are generated at build time by `docs/build.sh` from `src/packmol_util`; they are not manually maintained.
