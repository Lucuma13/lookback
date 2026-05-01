# lookback

`lookback` is a file and directory comparison tool. It answers two related questions:

* _Are these two files the same?__ Hashes both files and compares the digests.
* _Do these two directories contain the same files?__ Either compares file names and sizes (default), or hashes every file and compares the digests (full comparison mode). Optional `-i` flag ignores folder structure to focus exclusively on files (useful when directories have been moved around or renamed).

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
lookback path/to/file_a path/to/file_b
```

Compare two directories:

```bash
lookback path/to/source/ path/to/destination/               # metadata only (filenames and file sizes)
lookback -f path/to/source/ path/to/destination/            # deep mode: hash every file
lookback -i path/to/source/ path/to/destination/            # ignore folder structure
```

Check that the destination contains all of the files from the source:
```bash
lookback path/to/source/ path/to/destination/ | grep "<"
```

Output uses a `diff`-like format. Lines starting with `<` are unique to the source side, `>` lines are unique to the destination side, and identical entries are omitted:

```
$ lookback photos_2024/ photos_backup_2024/
< 1432891  IMG_0421.dng
> 1432891  IMG_0422.dng
$ echo $?
1
```

Other options:
  ```
    -d, --deep           : deep mode: hash every file (slower but safer)
    -i, --ignore         : ignore folder structure (compare flat list of file names and sizes)
    -a, --algorithm ALGO : hash algorithm (default: xxh128 if installed, else blake2b;
                           also: md5, sha1, sha256, blake2b, blake2s)
    -s, --save           : save listing of source under destination
    -X, --appledouble    : include AppleDouble (._*) files
  ```
