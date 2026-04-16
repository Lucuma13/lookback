#!/bin/bash

# lookback - A Bash utility to compare files and directories.
readonly LOOKBACK_VERSION="1.0"

# Copyright (c) 2026 Luis Gómez Gutiérrez
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

function show_help() {
	echo lookback v$LOOKBACK_VERSION. A Bash utility to compare files and directories.
	echo
	echo "Usage: lookback [options] <source> <destination>"
	echo
	echo "Options:"
	echo "  -i : Ignore folder structure"
	echo "  -y : Side-by-side comparison"
	echo "  -s : Save a list of files of the source directory (on the destination directory)"
	echo "  -H <hash> : File comparison using specific hash function: xxHash-128 (default), md5"
	echo "  -X : Show hidden AppleDouble files"
	echo "  -v : Verbose"
	echo "  -h : Show this help message"
	echo "  --version : Print version"
	echo
	exit 0
}

function get_abs_path() {
    local user_path="${1:-.}"
    if [[ -d "$user_path" ]]; then
        (cd "$user_path" && pwd)
    elif [[ -f "$user_path" ]]; then
        echo "$(cd "$(dirname "$user_path")" && pwd)/$(basename "$user_path")"
    else
        echo "$user_path"
    fi
}

# Options
verbose=false
ignore=false
sidebyside=""
save=false
hashfunction="xxhash-128"
appledouble=false

# Parse long-format flags
[[ "$1" == "--version" ]] && { echo "$LOOKBACK_VERSION"; exit 0; }
[[ "$1" == "--help" ]] && show_help

# Parse short-format flags
while getopts "isyXH:vh" option
do
	case $option in
		i) ignore=true ;; #ignore folder structure
		s) save=true ;;
		y) sidebyside='-y' ;;
		X) appledouble=true ;;
		H) hashfunction=$OPTARG ;; #accepts "md5" and "xxHash" (default) as arguments
		v) verbose=true ;;
		h) show_help ;;
		*) show_help ;;
	esac

done
shift "$((OPTIND-1))"

src=$(get_abs_path "$1")
dest=$(get_abs_path "$2")
srcname=$(basename "$1")
destname=$(basename "$2")


# Check input errors
[[ -z "$src" || -z "$dest" ]] && { echo "Error: Source and destination required" && exit 1 ; }
[ "$src" == "$dest" ] && { echo "Error: The two paths provided must be different" && exit 1 ; }


# Case-insensitive conversion for hashfunction
hashfunction=$(echo "$hashfunction" | tr '[:upper:]' '[:lower:]')

# --- File comparison ---
if [ -f "$src" ] && [ -f "$dest" ]; then
	[[ $verbose == true ]] && echo "Comparing checksums of individual files..."
	case $hashfunction in
		md5)
			if command -v md5 >/dev/null; then	# macOS/BSD
				hash1=$(md5 -q "$src")
				hash2=$(md5 -q "$dest")
				else							# Linux/GNU
				hash1=$(md5sum "$src" | cut -d " " -f 1)
				hash2=$(md5sum "$dest" | cut -d " " -f 1)
				fi
			;;
		xxhash-128|xxhash)
			if ! command -v xxhsum >/dev/null; then
				echo "Error: xxhsum not found. Please install xxHash or use md5 (see -h for help menu)." && exit 1
			fi
				hash1=$(xxhsum -H128 "$src" | cut -d " " -f 1)
				hash2=$(xxhsum -H128 "$dest" | cut -d " " -f 1)
			;;
		*) echo "Unsupported hash provided: $hashfunction" && exit 1 ;;
	esac

	if [ "$hash1" == "$hash2" ]; then
		echo && echo "It's a match! Checksums from $(basename "$src") and $(basename "$dest") are identical." && echo
	else
		echo && echo "Calculated hashes are different" && echo
	fi

# --- Directory comparison ---
elif [ -d "$src" ] && [ -d "$dest" ]; then
	#Define exclusion patterns (including AppleDouble files)
	find_exclude=( -type f
		! -iname ".DS_Store"
		! -path "*/.Trashes*"
		! -path "*/.Spotlight-V100*"
		! -path "*/.fseventsd*"
		! -path "*/.DocumentRevisions-V100*"
		#! -iname "Network Trash Folder"
		#! -iname "Temporary Items"
		#! -path "*/Cache*"
		#! -path "*/Caches*"
	)
	[[ $appledouble == false ]] && find_exclude+=( ! -iname "._*" )

	#Define 'stat' flags for portability (detect GNU vs BSD stat)
	if stat --help 2>&1 | grep -q "GNU"; then
		# GNU Stat (Linux or Homebrew coreutils)
		stat_portable=(stat --quoting-style=literal -c "%n %% %s")
	else
		# BSD Stat (default macOS)
		stat_portable=(stat -f "%N %% %z")
	fi


	#Define sorting logic (optionally ignoring folder structure)
	sorting_process="sort"
	[[ $ignore == true ]] && sorting_process="sed 's:.*/::' | sort -u"

	#Verbose
	if [[ $verbose == true ]]; then
		status_msg="Checking filenames and file sizes..."
		[[ $ignore == true ]] && status_msg="Ignoring folder structure, checking only filenames and file sizes..."
		[[ $appledouble == true ]] && status_msg="$status_msg Showing AppleDouble file differences..."
		echo "$status_msg"
	fi

	#Execution
	if [[ $save == true ]]; then
		(cd "$src" && find . "${find_exclude[@]}" -exec "${stat_portable[@]}" {} + | eval "$sorting_process") > "$dest/molist_$srcname.log"
		echo "File list saved to $dest/molist_$srcname.log"
	else
		diff $sidebyside \
			<(cd "$src" && find . "${find_exclude[@]}" -exec "${stat_portable[@]}" {} + | eval "$sorting_process") \
			<(cd "$dest" && find . "${find_exclude[@]}" -exec "${stat_portable[@]}" {} + | eval "$sorting_process")
		[ $? -eq 0 ] && echo && echo "It's a match! Filenames and file sizes from $srcname and $destname are matching." && echo
	fi
else
	echo && echo "Input needs to be either two files or two directories on the file system. Type \"lookback -h\" for help." && echo
fi
