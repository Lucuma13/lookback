# lookback

`lookback` provides a fast way to verify data integrity and structural consistency. It supports:
* File comparison: checksums (xxHash and MD5)
* Directory comparison: filenames, file sizes, and optionally folder structure

### 🛠 Dependencies

* [xxHash](https://github.com/Cyan4973/xxHash) © 2012-2026 Yann Collet (BSD 2-Clause)

### 🚀 Installation

##### macOS and Linux

1. Install [Homebrew](https://brew.sh/) (if not already installed):
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. Tap and install:
```
brew tap lucuma13/dit
brew install lookback
```

### 📖 Usage

`lookback [options] <source> <destination>`

| Option | Description |
| :---: | :--- |
| `-i` | Ignore folder structure |
| `-y` | Side-by-side comparison |
| `-s` | Save a list of files of the source directory (on the destination directory) |
| `-H` | File comparison using specific hash function: xxHash-128 (default), md5 |
| `-X` | Show hidden AppleDouble files |
| `-v` | Verbose |
| `-h` | Show help message |
| `--version` | Print version |

### 🤝 Acknowledgments

A special thank you to Mohammad Ayyash for initiating me into the dark magic of Bash, and writing the first "molist" commands from which this utility evolved.
