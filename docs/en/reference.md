# Reference

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/packmol_util/en/reference.html) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/packmol_util/ja/reference.html)

This page describes the responsibilities of the main components for users.

The complete generated listing of classes, methods, arguments, type annotations, and docstrings is available at {doc}`api/modules`.

## `AmorphousBuilder`

The high-level interface that coordinates structure generation.

Main responsibilities:

- Store element symbols and composition ratios
- Reconcile total atom count with composition ratios
- Determine the composition-unit multiplier
- Determine cell size from mass density or number density
- Register Packmol templates
- Generate Packmol input
- Run Packmol
- Convert output to POSCAR

This is the usual entry point.

## `Packmol`

Handles Packmol execution and associated numerical operations.

Main responsibilities:

- Atomic masses and mean atomic mass
- Conversion between mass density and number density
- Cell-size calculation from atom count and number density
- Packmol execution
- XYZ-to-POSCAR conversion

## `PackmolInp`

Constructs Packmol input files.

It translates structure templates, copy counts, placement regions, packing radii, and other settings into Packmol input syntax.

## `model`

Handles structure templates and recipes supplied to Packmol.

It can generate XYZ templates for individual atoms and multi-atom structural units.

## `Config`

Loads `packmol_util` settings from configuration files.

## `param`

Stores constants used in density and cell-size calculations, including atomic masses.

## API Reference

```{toctree}
:maxdepth: 2

api/modules
```

This section is not maintained manually. `docs/build.sh` scans `src/packmol_util` and generates it during the documentation build.


## Distinctions among public APIs

| Component | Main APIs | Purpose |
| --- | --- | --- |
| `AmorphousBuilder` | `__init__`, `multiplier`, `add_template`, `build` | Generate structures from composition, density, and templates |
| `PackmolInp` | `__init__`, `add_structure`, `write` | Generate `.inp` files |
| `Packmol` | `number_density_from_mass_density`, `mass_density_from_number_density`, `cell_length_from_number_density` | Density and cell-edge calculations |
| `Packmol` | `compute_element_counts`, `compute_cell_sizes`, `get_unit_atom_count` | Atom counts and composition ratios |
| `Packmol` | `run_packmol`, `xyz_to_poscar`, `write_fnc_file`, `count_atoms_in_xyz` | Execution, conversion, and FNC output |
| `model` | `write_xyz_template`, `write_single_atom_xyz`, `write_tetrahedral_unit_xyz` | Create XYZ templates |
| `model` | `StructureSpec`, `MaterialRecipe`, `make_material_recipe`, `make_atomic_mixture_recipe` | Placement recipes |
| `model` | `make_tetrahedral_unit_fnc_pairs`, `make_tetrahedral_unit_fnc_spec_from_ranges`, `TetrahedralUnitFncSpec` | Tetrahedral FNC constraints |
| `model` | `solve_packing_radii_from_pair_distances` | Approximate packing radii from element-pair distances |
| `Config` | `__init__(yaml_path=...)`, `load_yaml()` | Load YAML settings |

### `AmorphousBuilder` arguments

`symbols` and `ratios` specify corresponding elements and integer composition ratios. `total_atom_count` is the requested number of atoms; `minimum_separation` is Packmol's `tolerance`; `mass_density` is in g/cm³; `number_density` is in Å⁻³; and `packmol_bin` is an executable name or path. **Number density takes precedence** if both density parameters are supplied. In `add_template(xyz_file, number, packing_radii=None, fnc_pairs_in_template=None, fnc_distance_ranges=None, fnc_output_constraint_types=None)`, `number` means the **number of template copies**, not the number of atoms.

### `PackmolInp` arguments

`PackmolInp(minimum_separation_distance, output_xyz, box_length, use_pbc=False)` uses a cubic cell. The radii dictionary passed to `add_structure(xyz_file, number, packing_radii_by_atom_symbol=None)` is keyed by element symbol. `write(inp_file)` converts element symbols in the template into 1-based Packmol atom indices and, when needed, writes `atoms ... radius ... end atoms` blocks.

### Loading `Config`

`Config(yaml_path="settings.yaml")` overrides instance attributes with YAML keys, whereas `Config.load_yaml("settings.yaml")` overrides class attributes. Unknown keys produce a `NO SUCH VAR:` message. When called without an argument, `load_yaml()` consults the `PACKMOL_UTIL_CONFIG_YAML` environment variable. Omitting `yaml_path` when constructing an instance does not load YAML. The defaults in `Config` are example settings for Fe–Si–B and are not automatically consumed by `AmorphousBuilder`.

### Limitations

`Packmol.write_fnc_file()` requires consecutive constraint types starting at type 1. `Packmol.xyz_to_poscar()` obtains the cubic cell edge length from the first `inside box` line in the Packmol input. `PackmolInp` uses the same cell edge length for `pbc` and `inside box`. If you edit the input file manually, keep the cell dimensions consistent with these assumptions.
