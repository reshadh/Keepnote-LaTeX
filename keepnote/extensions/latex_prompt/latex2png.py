"""
Converts LaTeX objects like equation, table, etc to png images.
"""

"""
Author:
    Reshad Hosseini <hosseini@bethgelab.org>
    URL: http://www.bethgelab.org/hosseini

Revision History:
    2012/01/01 - Initial version

---

The main code was borrowd from Kamil Kisiel's python code
        "latexmath2png.py" (http://www.kamilkisiel.net).
"""

"""

  latex2png
  Copyright (c) 2012 Reshad Hosseini <hosseini@bethgelab.org>

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; version 2 of the License.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.

"""

"""
Help: How to use the program
   math2png(tex, _image_path, latex_permeable): converts math latex code to png
   eqn2png(tex, _image_path, latex_permeable): converts math latex code to png
   table2png(tex, _image_path, latex_permeable): converts math latex code to png
   latex2png(tex, _image_path, latex_permeable): converts math latex code to png
"""

# python imports
import os
import tempfile

# Default packages to use when generating output
default_packages = [
        'amsmath',
        'amsthm',
        'amssymb',
        'bm',
        'color',
    #    'amsfonts',
    #    'mathrsfs',
    #    'graphicx'
        ]

def __build_preamble(packages):
    preamble = '\documentclass{article}\n'
    if packages==default_packages:
        for p in packages:
            preamble += "\usepackage{%s}\n" % p
    else:
        preamble +=packages.encode()
    preamble += "\pagestyle{empty}\n\\begin{document}\n"
    return preamble

def __remove_aux_latex(infile):
    basefile = infile.replace('.tex', '')
    tempext = [ '.aux', '.dvi', '.log', '.bbl', '.blg', '.ps', '.pgf', '.pdf']
    for te in tempext:
        tempfile = basefile + te
        if os.path.exists(tempfile):
            os.remove(tempfile)
            
def __write_convert_output(infile, outdir, workdir = '.', size = 1):
    try:
        RUNDVI=1
        if RUNDVI:
           # normal latex produces colors better
           # Generate the DVI file
           latexcmd = 'latex -draftmode -halt-on-error -interaction=nonstopmode -output-directory %s %s'\
                   % (workdir, infile)
           rc = os.system(latexcmd)
           # Something bad happened, abort
           if rc != 0:
               return -1
           # Convert the DVI file to PNG's
           dvifile = infile.replace('.tex', '.dvi')
           psfile = infile.replace('.tex', '.ps')
           pscmd= 'dvips -q* -pp 1 -x %i -o \"%s\" \"%s\" ' % (size * 1000, psfile, dvifile)
           #pscmd= 'dvipdfm -o \"%s\" \"%s\" ' % (psfile, dvifile)
           rc = os.system(pscmd)
           if rc != 0:
               return -1
        else:
           # TikZ drawing is better integrated into pdflatex
           # Generate the PDF file
           latexcmd = 'pdflatex -halt-on-error -interaction=nonstopmode -output-directory %s %s'\
                   % (workdir, infile)
           rc = os.system(latexcmd)
           # Something bad happened, abort
           if rc != 0:
               return -1 
           psfile = infile.replace('.tex', '.pdf')
        pngcmd = "convert -trim -density 100 \"%s\" \"%s\" " %( psfile, outdir)
        rc = os.system(pngcmd)
        if rc != 0:
            return -1
        else:
            return 1
            #raise Exception('covert error')
    finally:
        # Cleanup temporaries
        __remove_aux_latex(infile)

def __write_output(infile, outdir, workdir = '.', size = 1):
    try:
        # Generate the DVI file
        latexcmd = 'latex -draftmode -halt-on-error -interaction=nonstopmode -output-directory %s %s'\
                % (workdir, infile)
        rc = os.system(latexcmd)
        # Something bad happened, abort
        #if rc != 0:
            #raise Exception('latex error')

        # Convert the DVI file to PNG's
        dvifile = infile.replace('.tex', '.dvi')
        dvicmd = "dvipng -q* --pp 1 -T tight -x %i -z 9 -bg Transparent "\
                "-o \"%s\" \"%s\"" % (size * 1000, outdir, dvifile)
        rc = os.system(dvicmd)
        if rc != 0:
            return -1
        else:
            return 1
    finally:
        # Cleanup temporaries
        __remove_aux_latex(infile)

def math2png(eqs, outdir, packages = default_packages, size = 1):
    """
    Generate png images from $...$ style math environment equations.

    Parameters:
        eqs         - An equation ascii tex
        outdir      - Output file for PNG images
        packages    - Optional list of packages to include in the LaTeX preamble
        size        - Scale factor for output
    """
    try:
        # Set the working directory
        workdir = tempfile.gettempdir()

        # Get a temporary file
        fd, texfile = tempfile.mkstemp('.tex', 'eq', workdir, True)
        # Create the TeX document
        with os.fdopen(fd, 'w+') as f:
            f.write(__build_preamble(packages))
            f.write("$%s$" % eqs)
            f.write('\end{document}')

        return __write_output(texfile, outdir, workdir, size)
    finally:
        if os.path.exists(texfile):
            os.remove(texfile)

def eqn2png(eqs, outdir, packages = default_packages, size = 1):
    """
    Generate png images from align environment equations.

    Parameters:
        eqs         - A list of equations
        outdir      - Output directory for PNG images
        packages    - Optional list of packages to include in the LaTeX preamble
        size        - Scale factor for output
    """
    try:
        # Set the working directory
        workdir = tempfile.gettempdir()

        # Get a temporary file
        fd, texfile = tempfile.mkstemp('.tex', 'eq', workdir, True)

        # Create the TeX document
        with os.fdopen(fd, 'w+') as f:
            f.write(__build_preamble(packages))
            f.write('\\begin{align*}')
            f.write("%s" % eqs)
            f.write('\end{align*}')
            f.write('\end{document}')

        return __write_output(texfile, outdir, workdir, size)
    finally:
        if os.path.exists(texfile):
            os.remove(texfile)

def table2png(eqs, outdir, packages = default_packages, size = 1):
    """
    Generate png images from tables.

    Parameters:
        eqs         - The table text
        outdir      - Output directory for PNG images
        packages    - Optional list of packages to include in the LaTeX preamble
        size        - Scale factor for output
    """
    try:
        # Set the working directory
        workdir = tempfile.gettempdir()

        # Get a temporary file
        fd, texfile = tempfile.mkstemp('.tex', 'eq', workdir, True)

        # Create the TeX document
        with os.fdopen(fd, 'w+') as f:
            f.write(__build_preamble(packages))
            f.write('\\begin{table}')
            f.write('\\begin{tabular}')
            f.write("%s" % eqs)
            f.write('\end{tabular}')
            f.write('\end{table}')
            f.write('\end{document}')

        return __write_output(texfile, outdir, workdir, size)
    finally:
        if os.path.exists(texfile):
            os.remove(texfile)

def latex2png(eqs, outdir, packages = default_packages, size = 1):
    """
    Generate png images from latex texts.

    Parameters:
        eqs         - input latex text
        outdir      - Output directory for PNG images
        packages    - Optional list of packages to include in the LaTeX preamble
        size        - Scale factor for output
    """
    try:
        # Set the working directory
        workdir = tempfile.gettempdir()

        # Get a temporary file
        fd, texfile = tempfile.mkstemp('.tex', 'eq', workdir, True)

        # Create the TeX document
        with os.fdopen(fd, 'w+') as f:
            f.write(__build_preamble(packages))
            f.write("%s" % eqs)
            f.write('\end{document}')

        return __write_convert_output(texfile, outdir, workdir, size)
    finally:
        if os.path.exists(texfile):
            os.remove(texfile)



def cite2png(eqs, outdir, packages = default_packages, size = 1):
    """
    Generate png images from bibtex texts.

    Parameters:
        eqs         - input bibtext entry
        outdir      - Output directory for PNG images
        packages    - Optional list of packages to include in the LaTeX preamble
        size        - Scale factor for output
    """
    try:
        # Set the working directory
        workdir = tempfile.gettempdir()

        # Get a temporary file
        fd, texfile = tempfile.mkstemp('.tex', 'eq', workdir, True)
        fdbib, texfilebib = tempfile.mkstemp('.bib', 'eq', workdir, True)

        newfilename = os.path.basename(texfile)
        newfilename, ext = os.path.splitext(newfilename)

        texfileaux=os.path.join(workdir,("%s.aux")%newfilename)
        texfileaux=os.path.join(workdir,("%s.aux")%newfilename)

        bibfilename = os.path.basename(texfilebib)
        bibfilename, ext = os.path.splitext(bibfilename)

        savedPath = os.getcwd()
        os.chdir(workdir)

        # Create the TeX document
        with os.fdopen(fd, 'w+') as f:
            f.write(__build_preamble(packages))
            f.write('\\nocite{*}')
            f.write('\\bibliographystyle{plain}')
            f.write('\\bibliography{%s}'% bibfilename)
            f.write('\end{document}')

        # Create the BibTeX document
        with os.fdopen(fdbib, 'w+') as fbib:
            fbib.write("%s" % eqs)

        # First Complile
        latexcmd = 'latex -halt-on-error -interaction=nonstopmode -output-directory %s %s'\
                % (workdir, texfile)
        rc = os.system(latexcmd)
        # Something bad happened, abort
        if rc != 0:
            return -1
        # First Complile
        latexcmd = 'bibtex -terse %s'\
                % texfileaux
        rc = os.system(latexcmd)
        # Something bad happened, abort
        if rc != 0:
            return -1
        # First Complile
        latexcmd = 'latex -halt-on-error -interaction=nonstopmode -output-directory %s %s'\
                % (workdir, texfile)
        rc = os.system(latexcmd)
        # Something bad happened, abort
        if rc != 0:
            return -1
        return __write_output(texfile, outdir, workdir, size)
    finally:
        # Cleanup temporaries
        __remove_aux_latex(texfile)
        if os.path.exists(texfile):
            os.remove(texfile)
        if os.path.exists(texfilebib):
            os.remove(texfilebib)
        os.chdir(savedPath)

def error2png(outdir, size = 1):
    """
    Generate png images writing Error in Red.

    Parameters:
        outdir      - Output file for PNG images
        size        - Scale factor for output
    """
    try:
        # Set the working directory
        workdir = tempfile.gettempdir()

        # Get a temporary file
        fd, texfile = tempfile.mkstemp('.tex', 'eq', workdir, True)
        # Create the TeX document
        preamble = '\documentclass{article}\n'
        preamble += "\usepackage{color}\n"
        preamble += "\pagestyle{empty}\n\\begin{document}\n"
        with os.fdopen(fd, 'w+') as f:
            f.write(preamble)
            f.write("\\textcolor{red}{LaTeX Error}")
            f.write('\end{document}')

        return __write_output(texfile, outdir, workdir, size)
    finally:
        if os.path.exists(texfile):
            os.remove(texfile)
            
def footnote2png(outdir, size = 1):
    """
    Generate png images writing footnote in Green.

    Parameters:
        outdir      - Output file for PNG images
        size        - Scale factor for output
    """
    try:
        # Set the working directory
        workdir = tempfile.gettempdir()

        # Get a temporary file
        fd, texfile = tempfile.mkstemp('.tex', 'eq', workdir, True)
        # Create the TeX document
        preamble = '\documentclass{article}\n'
        preamble += "\usepackage{color}\n"
        preamble += "\pagestyle{empty}\n\\begin{document}\n"
        with os.fdopen(fd, 'w+') as f:
            f.write(preamble)
            f.write("\\textcolor{green}{Footnote}")
            f.write('\end{document}')

        return __write_output(texfile, outdir, workdir, size)
    finally:
        if os.path.exists(texfile):
            os.remove(texfile)