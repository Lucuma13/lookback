# lookback

`lookback` is a file and directory comparison tool. It answers two related questions:

* _Are these two files the same?_ Hashes both files and compares the digests.
* _Do these two directories contain the same files?_ Either compares file names and sizes (default), or hashes every file and compares the digests (full comparison mode). Optional `-i` flag ignores folder structure to focus exclusively on files (useful when directories have been moved around or renamed).

This is a cross-platform tool (macOS / Linux / Windows) written in [Python](https://www.python.org/) and integrating the [xxhash](https://github.com/ifduyue/python-xxhash) package for high-throughput hashing. 

### 🚀 Installation

1. Install the `uv` package manager with the [official installer](https://docs.astral.sh/uv/getting-started/installation/) (or `brew install uv` on macOS / Linux).

2. Install the tool:

```
uv tool install lookback
```

### 📖 Usage

Compare two files:

```bash
lookback <file1> <file2>
```

Compare two directories:

```
lookback <source> <destination>               # metadata only (filenames and file sizes)
lookback -f <source> <destination>            # full comparison mode: hash every file
lookback -i <source> <destination>            # ignore folder structure
```

Check that the destination contains all of the files from the source:
```
lookback path/to/source/ path/to/destination/ | grep "<"
```

Output uses a `diff`-like format. Lines starting with `<` are unique to the source side, `>` lines are unique to the destination side:

```
$ lookback /Volumes/PRJ_MST01 /Volumes/PRJ_BAK01
< 1432891  IMG_0421.dng
> 1432891  IMG_0422.dng
```

Other options (run `lookback --help` for full list):
  ```
    -f, --full                     : deep mode: hash every file (slower but safer)
    -i, --ignore                   : ignore folder structure (compare flat list of file names and sizes)
    -a, --algorithm [xxh64|xxh128] : hash algorithm (default: xxh64)
    -s, --save                     : save listing for manual comparison
    -X, --appledouble              : include AppleDouble (._*) files
  ```
