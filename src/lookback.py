#!/usr/bin/env python3
"""
`lookback` is a file and directory comparison tool. It answers two related questions:

* _Are these two files the same?_ Hashes both files and compares the digests.
* _Do these two directories contain the same files?_ Either compares file names and sizes
(default), or hashes every file and compares the digests (full comparison mode). Optional
`-i` flag ignores folder structure to focus exclusively on files (useful when directories
have been moved around or renamed).

  Examples:
    1. Compare two files:

```bash
    lookback <file1> <file2>
```

    2. Compare two directories:

```bash
    lookback <source> <destination>        # metadata only (filenames and file sizes)
    lookback -f <source> <destination>     # full comparison mode: hash every file
    lookback -i <source> <destination>     # ignore folder structure
```

    3. Check that the destination contains all of the files from the source:
```bash
    lookback <source> <destination> | grep "<"
```
"""
# Copyright (c) 2026 Luis Gómez Gutiérrez. License: MIT.

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import xxhash as _xxhash

VERSION = "1.1.0"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EXCLUDED_NAMES = frozenset({
    ".DS_Store",            # macOS Finder metadata
})

EXCLUDED_DIR_PARTS = frozenset({
    ".Trashes",
    ".Spotlight-V100",
    ".fseventsd",
    ".DocumentRevisions-V100",
})

ALGORITHM_ALIASES = {
    "xxh64": "xxh64", "xxhash64": "xxh64", "xxhash64be": "xxh64",
    "xxh128": "xxh128", "xxhash128": "xxh128"
}

# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------
def normalise_algorithm(algo: str) -> str:
    result = ALGORITHM_ALIASES.get(algo.lower())
    if result is None:
        sys.exit(
            f"error: unknown algorithm '{algo}'. "
            f"Choose either xxh64 or xxh128."
        )
    return result


# ---------------------------------------------------------------------------
# File hashing
# ---------------------------------------------------------------------------
# Read files in 1 MiB chunks. Big enough that the read overhead is amortised,
# small enough that we don't blow up RAM on huge files.
_CHUNK = 1 << 20  # Bitwise shift that equals 2^20


def hash_file(path: str, algo: str) -> str:
    """
    Read a file from disk and return its xxhash digest as a hexadecimal string.
    """
    h = _xxhash.xxh128() if algo == "xxh128" else _xxhash.xxh64()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Walking a directory tree
# ---------------------------------------------------------------------------
def walk_tree(root: str, appledouble: bool):
    """
    Visit every regular file under `root`, skipping system/junk entries.
    Yields `(relative_path, size_in_bytes, full_path)` for each file.
    """
    root_len = len(root) + 1

    stack = [root]
    while stack:
        current = stack.pop()

        try:
            it = os.scandir(current)
        except OSError:
            continue

        with it:
            entries = list(it)

        for entry in entries:
            name = entry.name

            try:
                if entry.is_dir(follow_symlinks=False):
                    if name in EXCLUDED_DIR_PARTS:
                        continue
                    stack.append(entry.path)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    continue
            except OSError:
                continue

            if name in EXCLUDED_NAMES:
                continue
            if not appledouble and name.startswith("._"):
                continue

            try:
                size = entry.stat(follow_symlinks=False).st_size
            except OSError:
                continue

            yield entry.path[root_len:], size, entry.path


def walk_tree_with_empty_dirs(root: str, appledouble: bool):
    """
    Like `walk_tree`, but also yields a marker for every directory that
    contains no eligible files or subdirectories, so empty dirs show up
    in the diff.

    Yields `(relative_path + '/', -1, full_path)` for empty directories,
    in addition to the normal file tuples from `walk_tree`.
    """
    root_len = len(root) + 1

    stack = [root]
    while stack:
        current = stack.pop()

        try:
            it = os.scandir(current)
        except OSError:
            continue

        with it:
            entries = list(it)

        eligible_children = False
        subdirs = []

        for entry in entries:
            name = entry.name

            try:
                if entry.is_dir(follow_symlinks=False):
                    if name in EXCLUDED_DIR_PARTS:
                        continue
                    subdirs.append(entry.path)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    continue
            except OSError:
                continue

            if name in EXCLUDED_NAMES:
                continue
            if not appledouble and name.startswith("._"):
                continue

            try:
                size = entry.stat(follow_symlinks=False).st_size
            except OSError:
                continue

            eligible_children = True
            yield entry.path[root_len:], size, entry.path

        if current != root and not eligible_children and not subdirs:
            yield current[root_len:] + "/", -1, current

        stack.extend(subdirs)


# ---------------------------------------------------------------------------
# Building sorted listings of a directory
# ---------------------------------------------------------------------------
def list_metadata(root: str, ignore: bool, appledouble: bool):
    """
    Return a sorted list of `(size, path_or_name)` tuples for every file
    under `root`.

    If `ignore` is True we strip directory components and compare only
    filenames and sizes, with no empty-dir markers (structure is irrelevant).
    If `ignore` is False, empty directories are included as markers so they
    show up in the diff.
    """
    if ignore:
        seen = set()
        for rel, size, _full in walk_tree(root, appledouble):
            seen.add((size, os.path.basename(rel)))
        return sorted(seen, key=lambda e: e[1])

    out = [(size, rel) for rel, size, _full in walk_tree_with_empty_dirs(root, appledouble)]
    out.sort(key=lambda e: e[1])
    return out


def list_full(root: str, algo: str, appledouble: bool, ignore: bool):
    """
    Return a sorted list of `(hex_digest, name_or_path)` for every file under
    `root`. Every file is read end-to-end and hashed, so changes that don't
    alter file size are detected.

    If `ignore` is True we compare only by filename and hash, with no
    empty-dir markers (structure is irrelevant).
    If `ignore` is False, empty directories are included as markers so they
    show up in the diff.
    """
    if ignore:
        seen: dict[str, str] = {}
        for rel, _size, full in walk_tree(root, appledouble):
            name = os.path.basename(rel)
            seen[name] = hash_file(full, algo)
        results = [(digest, name) for name, digest in seen.items()]
    else:
        results = [(hash_file(full, algo) if size != -1 else "", rel)
                   for rel, size, full in walk_tree_with_empty_dirs(root, appledouble)]

    results.sort(key=lambda e: e[1])
    return results


# ---------------------------------------------------------------------------
# Streaming sorted-merge diff
# ---------------------------------------------------------------------------
def diff_sorted(a, b):
    """
    Compare two lists `a` and `b` that are *already sorted* by their
    second element (the path). Yield `('<', tuple)` for items only in `a`
    and `('>', tuple)` for items only in `b`.

    This is the classic two-pointer merge from merge sort: O(n+m) time,
    constant extra memory.
    """
    ia = ib = 0
    la, lb = len(a), len(b)

    while ia < la and ib < lb:
        ka, kb = a[ia][1], b[ib][1]
        if ka == kb:
            if a[ia] != b[ib]:
                yield "<", a[ia]
                yield ">", b[ib]
            ia += 1
            ib += 1
        elif ka < kb:
            yield "<", a[ia]
            ia += 1
        else:
            yield ">", b[ib]
            ib += 1

    while ia < la:
        yield "<", a[ia]
        ia += 1
    while ib < lb:
        yield ">", b[ib]
        ib += 1


# ---------------------------------------------------------------------------
# Save listings to TSV
# ---------------------------------------------------------------------------
def _write_listing(name: str, listing: list, full: bool, ignore: bool) -> None:
    """Write a TSV listing for one directory to cwd."""
    out = Path.cwd() / f"molist_{name}.tsv"
    col_header = "hash" if full else "size"
    path_header = "filename" if ignore else "filepath"
    try:
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"{col_header}\t{path_header}\n")
            for tup in listing:
                f.write(f"{tup[0]}\t{tup[1]}\n")
        print(f"Listing saved to {out}")
    except OSError as e:
        sys.exit(f"error: could not write to current directory: {e}")


def cmd_save(src: Path, a: list, dest: Path | None, b: list | None, args) -> int:
    """Save TSV listings for source (and optionally destination) to cwd."""
    cwd = Path.cwd()
    if not os.access(cwd, os.W_OK):
        sys.exit(f"error: current directory is not writable: {cwd}")
    _write_listing(src.name, a, args.full, args.ignore)
    if dest is not None and b is not None:
        _write_listing(dest.name, b, args.full, args.ignore)
    return 0


# ---------------------------------------------------------------------------
# Top-level commands (file vs file, directory vs directory)
# ---------------------------------------------------------------------------
def cmd_compare_files(src: Path, dest: Path, algo: str) -> int:
    """
    Compare two single files by hashing them.
    """
    h1 = hash_file(str(src), algo)
    h2 = hash_file(str(dest), algo)
    if h1 == h2:
        print(f"\n🎉 It's a match! File hashes from \"{src.name}\" and \"{dest.name}\" are identical.\n")
        return 0
    print("\n🛑 Calculated hashes are different.\n")
    return 1


def cmd_compare_dirs(src: Path, dest: Path | None, args) -> int:
    """
    Compare two directory trees.
    """
    if args.full:
        a = list_full(str(src), args.algorithm, args.appledouble, args.ignore)
        b = list_full(str(dest), args.algorithm, args.appledouble, args.ignore) if dest else None
    else:
        a = list_metadata(str(src), args.ignore, args.appledouble)
        b = list_metadata(str(dest), args.ignore, args.appledouble) if dest else None

    if args.save:
        return cmd_save(src, a, dest, b, args)

    if dest is None:
        sys.exit("error: destination is required for comparison. "
                 "Use -s to save a listing without a destination.")

    diffs = list(diff_sorted(a, b))

    if not diffs:
        if args.full:
            print(f"\n🎉 It's a match! File hashes from \"{src.name}\" and \"{dest.name}\" are identical.\n")
        else:
            print(f"\n🎉 It's a match! File names and sizes from \"{src.name}\" and \"{dest.name}\" are matching.\n")
        return 0

    if args.side_by_side:
        left  = {tup[1]: tup for sign, tup in diffs if sign == "<"}
        right = {tup[1]: tup for sign, tup in diffs if sign == ">"}
        all_paths = sorted(set(left) | set(right))

        try:
            term_width = os.get_terminal_size().columns
        except OSError:
            term_width = 80
        col = max(20, (term_width - 3) // 2)

        for path in all_paths:
            l_str = left[path][1]  if path in left  else ""
            r_str = right[path][1] if path in right else ""
            print(f"{l_str:<{col}} | {r_str}")
    else:
        write = sys.stdout.write
        for sign, tup in diffs:
            write(f"{sign} {tup[1]}\n")

    return 1


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------
def main(argv=None):
    """
    Parse command-line arguments and dispatch to the right command.
    """
    p = argparse.ArgumentParser(
        prog="lookback",
        description="Compare files and directories.",
    )

    p.add_argument("source")
    p.add_argument("destination", nargs="?")

    p.add_argument("-i", "--ignore",       action="store_true",
                   help="ignore folder structure (compare flat list of file names and sizes)")
    p.add_argument("-f", "--full",         action="store_true",
                   help="full directory comparison: hash every file (slower)")
    p.add_argument("-y", "--side-by-side", action="store_true",
                   help="show differences side by side")
    p.add_argument("-a", "--algorithm", default="xxh64", metavar="[xxh64|xxh128]",
                   help="hash algorithm (default: xxh64)")
    p.add_argument("-s", "--save",         action="store_true",
                   help="save listing for manual comparison")
    p.add_argument("-X", "--appledouble", action="store_true",
                   help="include AppleDouble (._*) files")
    p.add_argument("-v", "--verbose",     action="store_true")
    p.add_argument("--version", action="version", version=VERSION)

    # Show help menu if no arguments are provided
    if not (argv if argv is not None else sys.argv[1:]):
        p.print_help()
        return 1

    args = p.parse_args(argv)

    args.algorithm = normalise_algorithm(args.algorithm)

    src  = Path(args.source).resolve()
    dest = Path(args.destination).resolve() if args.destination else None

    # Single-path invocation: only valid with -s
    if dest is None:
        if not args.save:
            sys.exit("error: destination is required for comparison. "
                     "Use -s to save a listing without a destination.")
        if not src.is_dir():
            sys.exit("error: source must be a directory when using -s without a destination.")
        return cmd_compare_dirs(src, None, args)

    if src == dest:
        sys.exit("Error: source and destination must be different")
    if src.is_file() and dest.is_file():
        return cmd_compare_files(src, dest, args.algorithm)
    if src.is_dir() and dest.is_dir():
        return cmd_compare_dirs(src, dest, args)
    sys.exit("Input needs to be either two files or two directories on the file system. "
             "Type \"lookback --help\" for help")


if __name__ == "__main__":
    sys.exit(main())