# Tutorial

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/packmol_util/en/tutorial.html) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/packmol_util/ja/tutorial.html)


## Building a structure from single-atom templates

This example places Fe, Si, and B as separate single-atom templates.

### Create templates

```python
from packmol_util.model import write_single_atom_xyz

write_single_atom_xyz("Fe.xyz", "Fe")
write_single_atom_xyz("Si.xyz", "Si")
write_single_atom_xyz("B.xyz", "B")
```

Each call writes an XYZ template containing one atom.

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

The composition ratios sum to 100. The number of composition units is available as `builder.multiplier`.

### Register templates

```python
builder.add_template("Fe.xyz", 80 * builder.multiplier)
builder.add_template("Si.xyz", 9 * builder.multiplier)
builder.add_template("B.xyz", 11 * builder.multiplier)
```

### Generate the structure

```python
builder.build("FeSiB")
```

`build()` generates the Packmol input, executes Packmol, and converts the output structure.

## Using number density

Number density can be used instead of mass density:

```python
builder = AmorphousBuilder(
    symbols=["Fe", "Si", "B"],
    ratios=[80, 9, 11],
    total_atom_count=1000,
    minimum_separation=2.0,
    number_density=0.08,
)

print(builder.box_length)
```

## Placing a multi-atom structural unit

For Li3PO4, PO4 can be placed as a single structural unit with its own XYZ template.

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

These distances describe the internal geometry of PO4, not its packing exclusion distances.

### Create the builder

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

Li3PO4 contains eight atoms per composition unit, so 512 atoms correspond to 64 units.

### Register templates

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

`packing_radii` controls exclusion distances during Packmol placement, not internal P–O bond lengths.

### Generate the structure

```python
builder.build("Li3PO4")
```

## Low-level API

You can use `PackmolInp` to construct Packmol input independently, or `Packmol` for density and cell-size calculations, execution, and XYZ-to-POSCAR conversion. See {doc}`api/modules` for current class and method signatures.
