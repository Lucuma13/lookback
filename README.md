# triplecheck

`triplecheck` is a two- and three-way file and directory comparison tool:
* For files it compares their hashes.
* For directories, it either compares the hashes of every file (full comparison mode), or compares file names and sizes (default). And it contains an optional `-i` flag to ignore folder structure and focus exclusively on files (useful if directories have been nested, moved around or renamed in one of your copies).

This is a cross-platform tool (macOS / Linux / Windows) written in [Python](https://www.python.org/) and integrating the [xxhash](https://pypi.org/project/xxhash) package for high-throughput hashing and [blake3](https://pypi.org/project/blake3) for cryptographic hashing.

### 🚀 Installation

1. Install the `uv` package manager with the [official installer](https://docs.astral.sh/uv/getting-started/installation/), or:
* macOS: `brew install uv`
* Windows: `winget install astral-sh.uv`
* Linux (Debian): `apt-get install uv`
<!--
* Linux (RHEL): `yum install uv`
* Linux (SUSE): `zypper install python-uv`
* Linux (Arch): `pacman -S muv`
-->

2. Install the tool:

```bash
uv tool install triplecheck
```

3. Test the installation (if the command is not recognised try `uv tool update-shell` and restart Terminal):

```bash
triplecheck --version
```

### 📖 Usage examples

Compare two (or three) files or directories:

```bash
triplecheck "path/to/file1" "path/to/file2"                        # full comparison of files
triplecheck "path/to/dir1" "path/to/dir2" "path/to/dir3"           # metadata-only comparison (filenames and file sizes)
triplecheck -f "path/to/dir1" "path/to/dir2"                       # full directory comparison: hash every file
triplecheck -i "path/to/dir1" "path/to/dir2"                       # ignore folder structure
triplecheck -e "*.mhl" -e "*.txt" "path/to/dir1" "path/to/dir2"    # exclude .mhl and .txt files
```

Check that the destination contains all of the files from the source:
```bash
triplecheck "path/to/src" "path/to/dst" | grep "<"
```

Output is composed of pairs or triads representing the relationship between the paths (`<`, `>` and `>>` represent the paths provided). In the example below `IMG_0421.mov` exists only in `PRJ_MST01`, while `IMG_0422.mov` exists everywhere but the copy on `PRJ_BAK02` is different to the others.
```
$ triplecheck /Volumes/PRJ_MST01 /Volumes/PRJ_BAK01 /Volumes/PRJ_BAK02
<  ∃ IMG_0421.mov
>  ∄ IMG_0421.mov
>> ∄ IMG_0421.mov

<  = IMG_0422.mov
>  = IMG_0422.mov
>> ≠ IMG_0422.mov
```

Two-way comparison with `--diff` offers an alternative output format for those familiar with `diff`. Lines starting with `<` are unique to the first path, `>` lines are unique to the second path:

```
$ triplecheck --diff /Volumes/PRJ_MST01 /Volumes/PRJ_BAK01
< IMG_0421.mov
> IMG_0422.mov
```

Run `triplecheck --help` to see the full list of options.


### 🤝 Acknowledgments

A special thank you to Mohammad Ayyash for initiating me into the dark magic of Python and Bash, and writing the first "molist" commands from which this utility evolved.
