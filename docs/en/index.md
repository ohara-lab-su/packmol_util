# packmol_util

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/packmol_util/en/index.html) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/packmol_util/ja/index.html)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Fpackmol_util-181717?logo=github)](https://github.com/ohara-lab-su/packmol_util/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/packmol_util/en/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/index.en.html)


`packmol_util` is an open-source Python toolkit for generating initial
amorphous structures with Packmol.
It automates structure preparation from composition,
atom count, density,
and minimum-distance constraints through Packmol execution and POSCAR output.

It also supports generating FNC constraints for RMC_POT,
helping connect initial structure preparation to reverse Monte Carlo modeling.
For RMC_POT input preparation, calculation automation, and result analysis, see the independently usable [rmc_util](https://ohara-lab-su.github.io/rmc_util/en/).

```{toctree}
:maxdepth: 2
:caption: Contents

philosophy
tutorial
reference
api/modules
```


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
