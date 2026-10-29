# packmol_util

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/packmol_util/en/index.html) [![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://ohara-lab-su.github.io/packmol_util/ja/index.html)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Fpackmol_util-181717?logo=github)](https://github.com/ohara-lab-su/packmol_util/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/packmol_util/ja/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/)

`packmol_util` は Packmol を用いてアモルファス初期構造を作成する Python ライブラリです。

組成、総原子数、密度、最小原子間距離の条件から、Packmol 入力の生成、実行、生成構造の POSCAR 形式への変換を行います。

```{toctree}
:maxdepth: 2
:caption: 目次

philosophy
tutorial
reference
api/modules
```

## 付属スクリプト・サンプルのインストール

`pip install packmol-util` 後、ファイルを配置したい作業ディレクトリで以下を実行します。

```sh
packmol_util install scripts
packmol_util install example
```

前者はリポジトリの `scripts/` 以下、後者は `example/` 以下のファイルをコピーします。サブディレクトリ構造は維持されます。たとえば `example/Li3PO4/non_builder/make_Li3PO4.py` は `./Li3PO4/non_builder/make_Li3PO4.py` になります。

既存の同名ファイルはデフォルトで上書きしません。上書きする場合は `--force` を指定します。

```sh
packmol_util install scripts --force
packmol_util install example --force
```

コピー先はカレントディレクトリです。無関係なファイルは削除しません。この機能は外部の Packmol 実行ファイルをインストールするものではありません。
