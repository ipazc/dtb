# dtb
Dataset Builder tool CLI that allows to convert datasets among different formats and standardize them.

![alt text][logo]

[logo]: https://github.com/ipazc/dtb/blob/master/dtb.jpeg "Dataset Builder tool."

# Requirements
It is required Ubuntu >= 14.04 or Debian >= 8 Jessie with Caffe and LMDB libraries installed.


# Installation
The following pip packages must be installed: docopt and lmdb:
```bash
sudo pip3 install docopt lmdb
```

Use the install script that is bundled with the project to install it:
```bash
$ chmod +x install.sh
$ ./install.sh
```

# Usage
The command line interface can be used with `$ dtb`.

## Initialize a dataset repository in the current folder for an age estimation dataset

```bash
$ dtb init GenericImageAgeDataset
```

## Add image[s] to the repository

```bash
$ dtb add path/to/image.jpg path/to/image2.jpg path/to/image3.jpg ...
```

## Retrieve information from the current dataset
```bash
$ dtb info
```

## Retrieve the size of the current dataset (number of elements)
```bash
$ dtb size
```

## Export to zip
".zip" extension is not required in `zip_name`. It will be appended automatically.

```bash
$ dtb zip export /path/zip_name
```

## Import from zip
".zip" extension is not required in `zip_name`. It will be appended automatically.

```bash
$ dtb zip import /path/zip_name
```

## Export to LMDB splitted in multiple sets, preprocessing images to a size, equalizing their histogram and shuffling the result.

```bash
$ dtb lmdb export /path/to/lmdb train:0.7 test:0.2 val:0.1 --size=227x227 --equalize-histogram --shuffle
```

## Check existing LMDB health to be used to train in Caffe.

```bash
$ dtb lmdb check-shuffle-status /path/to/lmdb
```

## Check LMDB number of elements

```bash
$ dtb lmdb size /path/to/lmdb
```

## Import from LMDB into current repository

```bash
$ dtb lmdb import /path/to/lmdb
```

## Merge multiple datasets into a single one deduplicating by hashes.

```bash
$ dtb merge /path/to/dataset_repository1 /path/to/dataset_repository2 ... --deduplicate-by-hash
```
