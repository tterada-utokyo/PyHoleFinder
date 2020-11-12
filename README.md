# PyHoleFinder
PyHoleFinder is a python program to find holes in holey carbon films on a cryo-electron microscope (cryo-EM) grid.

## Main features 
This program has following features:
1.	This program read a SerialEM Navigator file and imports images from a MRC file described in the Navigator file.
2.	The positions of the holes are detected by template-matching method. The user specifies a region containing a typical hole in an image to use it as the template.
3.	Holes near grid bars are ignored. The width of the ignored region is controlled by parameters.
4.	Clustering can be performed on detected holes. Holes in the largest cluster, which are usually those in the central square, are retained.
5.	Holes in the largest cluster can be divided into 3x3 or 5x5 groups.
6.	The coordinates of the detected holes can be saved in a file in the Navigator file format. When clustering is performed, the coordinates of the holes in the largest cluster are written. When grouping is performed, the coordinates of the central hole in each group are written.
7.	This program provides a user-friendly graphical user interface to perform these analysis.
8.	The User can apply the analysis to all images in a MRC file.
9.	This program can run as a stand-alone application and can be called from SerialEM.

## Install and usage
This program was developed and tested on a Windows-10 PC with Anaconda 3.18.9. See manual.pdf for details.

## Author
This program is written by Tohru Terada of The University of Tokyo.

## Acknowledgements
The author is grateful for valuable inputs by Profs. Masahide Kikkawa and Haruaki Yanagisawa of The University of Tokyo.
This program was developed with support by Platform Project for Supporting Drug Discovery and Life Science Research (Basis for Supporting Innovative Drug Discovery and Life Science Research (BINDS)) from AMED under Grant Number JP20am0101107.

## License
The source code is distributed under the MIT license. See LICENSE for details.
