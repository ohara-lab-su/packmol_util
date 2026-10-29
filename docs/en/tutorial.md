# Tutorial

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/packmol_util/en/tutorial.html) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/packmol_util/ja/tutorial.html)

## Build a structure from single-atom templates

This example places each element independently as a single-atom template, as in Fe–Si–B.

### Create the templates

```python
from packmol_util.model import write_single_atom_xyz

write_single_atom_xyz("Fe.xyz", "Fe")
write_single_atom_xyz("Si.xyz", "Si")
write_single_atom_xyz("B.xyz", "B")
```

Each file contains a single-atom XYZ template.

### Create the builder

```python
from packmol_util.builder import AmorphousBuilder

builder = AmorphousBuilder(
    symbols=["Fe", "Si", "B"],
    ratios=[80, 9, 11],
    total_atom_count=1000,
    minimum_separation=2.0,
    mass_density=7.0,
)
```

The composition ratios sum to 100. The number of composition units is available through:

```python
builder.multiplier
```

### Register the templates

```python
builder.add_template(
    "Fe.xyz",
    80 * builder.multiplier,
)

builder.add_template(
    "Si.xyz",
    9 * builder.multiplier,
)

builder.add_template(
    "B.xyz",
    11 * builder.multiplier,
)
```

### Generate the structure

```python
builder.build("FeSiB")
```

`build()` generates Packmol input, runs Packmol, and converts the resulting structure.

## Specify number density

Number density can be specified instead of mass density.

```python
builder = AmorphousBuilder(
    symbols=["Fe", "Si", "B"],
    ratios=[80, 9, 11],
    total_atom_count=1000,
    minimum_separation=2.0,
    number_density=0.08,
)
```

The calculated cell edge length can be inspected with:

```python
print(builder.box_length)
```

## Place molecular or structural units

To place PO4 as a single structural unit in Li3PO4, create an XYZ template for PO4.

### Li template

```python
from packmol_util.model import write_single_atom_xyz

write_single_atom_xyz("Li.xyz", "Li")
```

### PO4 template

```python
from packmol_util.model import write_tetrahedral_unit_xyz

write_tetrahedral_unit_xyz(
    filename="PO4.xyz",
    center_element="P",
    vertex_element="O",
    center_vertex_distance=1.54,
    vertex_vertex_distance=2.51,
)
```

These distances describe the internal geometry of PO4.

### Builder

```python
from packmol_util.builder import AmorphousBuilder

builder = AmorphousBuilder(
    symbols=["Li", "P", "O"],
    ratios=[3, 1, 4],
    total_atom_count=512,
    minimum_separation=1.5,
    number_density=0.09119,
)
```

Li3PO4 has eight atoms per composition unit; 512 atoms correspond to 64 composition units.

### Register the templates

```python
builder.add_template(
    xyz_file="Li.xyz",
    number=3 * builder.multiplier,
)

builder.add_template(
    xyz_file="PO4.xyz",
    number=builder.multiplier,
    packing_radii={
        "P": 0.25,
        "O": 1.05,
    },
)
```

`packing_radii` specifies exclusion distances used when Packmol places templates, not bond lengths within PO4.

### Generate the structure

```python
builder.build("Li3PO4")
```

## Low-level API

Lower-level APIs can be used without the high-level `AmorphousBuilder` interface.

Use `PackmolInp` to construct Packmol input alone, or `Packmol` for individual operations such as density and cell-size calculations, Packmol execution, and XYZ-to-POSCAR conversion.

For current class and method signatures, see {doc}`api/modules`.


## Installing Packmol

`packmol_util` does not bundle the Packmol executable. Install Packmol separately and make the `packmol` command available. If the executable is elsewhere, supply its path through `AmorphousBuilder(packmol_bin="...")`.

- [Packmol official website](https://m3g.iqm.unicamp.br/packmol/)
- [Packmol source code](https://github.com/m3g/packmol)
- [Packmol source archive](https://m3g.iqm.unicamp.br/packmol/packmol.tar.gz)

Example of building from source on Linux:

```sh
wget https://m3g.iqm.unicamp.br/packmol/packmol.tar.gz
tar xzf packmol.tar.gz
cd packmol
make
```

Example using GNU Fortran on macOS:

```sh
brew install gcc
tar xzf packmol.tar.gz
cd packmol
FC=gfortran-14 F77=gfortran-14 ./configure
make
```

Replace `gfortran-14` with the installed compiler name. Build procedures vary by Packmol version; also consult the upstream instructions. Add the executable location to `PATH` or specify `packmol_bin`.

## Packmol input files and the low-level API

Packmol input files specify XYZ templates, copy counts, and placement regions. The following example places single-atom Fe, Si, and B templates.

```text
tolerance 2.0
pbc 20.0 20.0 20.0
filetype xyz
output FeSiB_packmol.xyz

structure Fe.xyz
  number 80
  inside box 0.0 0.0 0.0 20.0 20.0 20.0
end structure

structure Si.xyz
  number 9
  inside box 0.0 0.0 0.0 20.0 20.0 20.0
end structure

structure B.xyz
  number 11
  inside box 0.0 0.0 0.0 20.0 20.0 20.0
end structure
```

`PackmolInp` lets you express the same structure in Python. Here, the cell edge length is an illustrative 20 Å and is not calculated from density.

```python
from packmol_util.model import write_single_atom_xyz
from packmol_util.packmol_inp import PackmolInp
from packmol_util.packmol import Packmol

for symbol in ("Fe", "Si", "B"):
    write_single_atom_xyz(f"{symbol}.xyz", symbol)

inp = PackmolInp(
    minimum_separation_distance=2.0,
    output_xyz="FeSiB_packmol.xyz",
    box_length=20.0,
    use_pbc=True,
)
for symbol, count in (("Fe", 80), ("Si", 9), ("B", 11)):
    inp.add_structure(f"{symbol}.xyz", count)
inp.write("FeSiB_packmol.inp")

runner = Packmol()
runner.run_packmol("FeSiB_packmol.inp", "FeSiB_packmol.log")
index_map = runner.xyz_to_poscar(
    xyz_file="FeSiB_packmol.xyz",
    poscar_file="POSCAR",
    packmol_inp="FeSiB_packmol.inp",
    elements=["Fe", "Si", "B"],
)
```

`run_packmol()` passes the input file to Packmol through standard input and saves standard output and standard error in a log. `xyz_to_poscar()` reads the cell length from `inside box`, converts Cartesian coordinates to Direct coordinates, and sorts atoms by element. The returned `index_map` maps 1-based atom indices in Packmol XYZ to 1-based atom indices in POSCAR.

## Density, composition ratios, and total atom count

`AmorphousBuilder` accepts number density directly or derives it from mass density and composition. For number density \(n\) [Å\(^{-3}\)] and total atom count \(N\), the cubic cell edge length is \(L=(N/n)^{1/3}\) [Å]. For mass density \(\rho\) [g cm\(^{-3}\)] and mean atomic mass \(\bar M\) [g mol\(^{-1}\)], \(n=\rho N_A 10^{-24}/\bar M\).

```python
from packmol_util.packmol import Packmol
pm = Packmol()
counts = pm.compute_element_counts(["Fe", "Si", "B"], [80, 9, 11], 503)
number_density = pm.number_density_from_mass_density(
    ["Fe", "Si", "B"], [80, 9, 11], 7.35
)
length = pm.cell_length_from_number_density(500, number_density)
print(counts, length)
```

`Packmol.compute_element_counts()` keeps the total atom count fixed and distributes remaining atoms to elements with the largest fractional remainders; the resulting composition may not exactly match the requested ratios. In contrast, `AmorphousBuilder` adjusts `total_atom_count` to the nearest integer multiple of `sum(ratios)`, preserving the ratios. Inspect the adjusted count with `builder.total_atom_count` and the multiplier with `builder.multiplier`. `model.make_atomic_mixture_recipe()` rejects atom counts that are not integer multiples and raises `ValueError`. These behaviors are distinct.

## Structure recipes and templates

`model` provides XYZ template generators and data structures for recording placement counts. `StructureSpec` stores a template filename, copy count, and element-specific packing radii. `make_material_recipe()` reads the first line of each XYZ file to determine the number of atoms per template and sets `MaterialRecipe.total_atom_count` to the sum of `number × atoms per template`. `make_atomic_mixture_recipe()` creates single-atom XYZ files and a recipe together.

```python
from packmol_util.model import make_atomic_mixture_recipe
recipe = make_atomic_mixture_recipe(
    symbols=["Fe", "Si", "B"],
    ratios=[80, 9, 11],
    total_atom_count=500,
)
assert recipe.total_atom_count == 500
```

Creating `StructureSpec` or `MaterialRecipe` does not run Packmol. To use a recipe with `AmorphousBuilder`, register the entries in `recipe.structures` one by one using `builder.add_template()`.

## Tetrahedral templates and RMC_POT FNC

For PO4, the local atom indices in the template are P=1 and O=2–5. Register FNC atom pairs using these local indices; after Packmol runs, they are mapped to POSCAR atom indices. `make_tetrahedral_unit_fnc_pairs()` returns four P–O pairs (type 1) and six O–O pairs (type 2).

```python
from packmol_util.builder import AmorphousBuilder
from packmol_util.model import (
    write_single_atom_xyz,
    write_tetrahedral_unit_xyz,
    make_tetrahedral_unit_fnc_pairs,
)

write_single_atom_xyz("Li.xyz", "Li")
write_tetrahedral_unit_xyz(
    filename="PO4.xyz",
    center_element="P",
    vertex_element="O",
    center_vertex_distance=1.54,
    vertex_vertex_distance=2.515,
)

builder = AmorphousBuilder(
    symbols=["Li", "P", "O"],
    ratios=[3, 1, 4],
    total_atom_count=512,
    minimum_separation=1.5,
    number_density=0.09119,
)
builder.add_template("Li.xyz", 3 * builder.multiplier)
builder.add_template(
    "PO4.xyz",
    builder.multiplier,
    packing_radii={"P": 0.25, "O": 1.05},
    fnc_pairs_in_template=make_tetrahedral_unit_fnc_pairs(),
    fnc_distance_ranges={1: (1.45, 1.65), 2: (2.40, 2.65)},
    fnc_output_constraint_types=[1, 2],
)
builder.build("Li3PO4")
```

`fnc_output_constraint_types=None` outputs all types; `[1]` outputs only type 1. Selecting FNC types does not change the XYZ template geometry or placement conditions supplied to Packmol. `Packmol.write_fnc_file()` requires FNC types to be **consecutive integers starting at 1**, so requesting only type 2 with `[2]` raises an error in the current implementation.

`make_tetrahedral_unit_fnc_spec_from_ranges()` calculates the midpoint of each FNC distance range, checks whether the distances are geometrically consistent with a regular tetrahedron, and returns representative template distances and FNC pairs. The center–vertex distance \(d\) and vertex–vertex distance \(a\) must satisfy \(a=d\sqrt{8/3}\). `geometry_distance_tolerance` controls the tolerance of this geometry check, not the width of the FNC distance ranges.

`solve_packing_radii_from_pair_distances()` approximates requested minimum element-pair distances as sums of packing radii. Distances for all same-element and different-element pairs are required. `pair_distance_tolerance` is the allowed approximation error for the distance table, not Packmol's `tolerance`. The search is discrete and does not guarantee a solution for an arbitrary distance table.

## Output files and implementation constraints

`builder.build("FeSiB")` produces `FeSiB_packmol.inp`, `FeSiB_packmol.xyz`, `FeSiB_packmol.log`, `POSCAR`, and `POSCAR.vasp`. By default, `FeSiB.fnc` is also written **only if FNC pairs have been registered**. Specify another FNC destination with `build(output_prefix, fnc_file=...)`. The names `POSCAR` and `POSCAR.vasp` are fixed regardless of the output prefix, so repeated runs in the same working directory overwrite them.

Ensure that the sum of `add_template(number=...)` copy counts multiplied by the atom counts of their respective templates equals the adjusted `builder.total_atom_count`. The current `AmorphousBuilder` does not check this equality at the start of `build()`. FNC generation depends on template placement order in Packmol XYZ and element-based sorting in POSCAR. FNC atom indices are **1-based**.


## Installing bundled scripts and examples

After `pip install packmol-util`, run the following commands in the working directory where you want the files:

```sh
packmol_util install scripts
packmol_util install example
```

The first command copies the contents of the repository's `scripts/` directory, while the second copies `example/`. Subdirectory structures are preserved. For example, `example/Li3PO4/non_builder/make_Li3PO4.py` becomes `./Li3PO4/non_builder/make_Li3PO4.py`.

Existing files are **not overwritten** by default. To overwrite files with the same name, use `--force`:

```sh
packmol_util install scripts --force
packmol_util install example --force
```

Files are copied into the current working directory. Unrelated files are not deleted. This feature does not install the external Packmol executable.
