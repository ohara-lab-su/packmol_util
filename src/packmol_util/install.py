"""packmol_util に付属するスクリプトとサンプルの配置機能。"""

from __future__ import annotations

import argparse
import shutil
import sys
import sysconfig
from pathlib import Path


def _source_directory(kind: str) -> Path:
    """インストール済みの共有データ領域から配布ファイルを探す。"""
    base = Path(sysconfig.get_path("data")) / "share" / "packmol_util"
    source = base / kind
    if not source.is_dir():
        raise FileNotFoundError(
            f"配布データが見つかりません: {source}\n"
            "パッケージを再インストールし、scripts/example が配布物に含まれるか確認してください。"
        )
    return source


def install(kind: str, *, destination: str | Path = ".", force: bool = False) -> tuple[int, int]:
    """配布ファイルをカレントディレクトリへ再帰的にコピーする。

    同名ファイルは既定で保持する。force=True の場合のみ上書きする。
    既存のディレクトリは削除せず、ファイル単位で判定する。
    """
    if kind not in ("scripts", "example"):
        raise ValueError("kind は 'scripts' または 'example' を指定してください")
    source = _source_directory(kind)
    target = Path(destination).expanduser().resolve()
    copied = skipped = 0
    for src in sorted(source.rglob("*")):
        if not src.is_file():
            continue
        relative = src.relative_to(source)
        dst = target / relative
        if dst.exists() and not force:
            print(f"SKIP {dst}")
            skipped += 1
            continue
        if dst.is_dir():
            raise IsADirectoryError(f"コピー先がディレクトリです: {dst}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        existed = dst.exists()
        shutil.copy2(src, dst)
        print(f"{'OVERWRITE' if existed else 'COPY'} {dst}")
        copied += 1
    print(f"完了: {copied} ファイル配置、{skipped} ファイルをスキップ")
    return copied, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="packmol_util")
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("install", help="付属スクリプトまたはサンプルを配置")
    command.add_argument("target", choices=("scripts", "example"))
    command.add_argument("--force", action="store_true", help="同名ファイルを上書き")
    args = parser.parse_args(argv)
    try:
        install(args.target, force=args.force)
    except (OSError, ValueError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
