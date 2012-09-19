"""
Convert latex code to keepnote text and images in TextBuffer
"""

"""
Author:
    Reshad Hosseini <hosseini@bethgelab.org>
    URL: http://www.bethgelab.org/hosseini

Revision History:
    2012/01/01 - Initial version

"""

"""

  latex_keepnote
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
import tempfile
import os
from gtk import gdk
from latex2png import *
# keepnote imports
from keepnote.gui.richtext import RichTextImage
#from keepnote.gui import *

def _load_permeable(node):
    """ Finding the node which contains LaTeX Permeable """
    for child in node.get_children():
             pathni ,pathi =os.path.split( child.get_path())
             if pathi==u"latex permeable":
                file_name=os.path.join(child.get_path(), "latex_permeable.txt")
                f=open(file_name,'rb')
                return_text=f.read()
                f.close()
                return return_text
    if node.get_parent():
         return _load_permeable(node.get_parent())
    else:
         return default_packages

def richtext2latex(widget):
    """
    Changes the textbuffer in a node to its latex equivalent

    If some part of a text is marked then only the selected part is changed
    """
    textbuffer=widget.get_buffer()
    sel = textbuffer.get_selection_bounds()

    # do nothing if nothing is selected
    if not sel:
        return

    start, end = sel
    # It is important to create a list out of contents
    contents = list(textbuffer.copy_contents(start, end))

    # make sure all inserts are treated as one action
    textbuffer.begin_user_action()

    textbuffer.delete_selection(False, True)
    text_old=""
    contents2=list()
    for kind, offset, param in contents:
        # NOTE: offset is ignored

        if kind == "text":
            text_old=("%s%s")% (text_old,param)
            offset_old=offset

        else:
            if text_old is not "":
                text_old=uni2latex(text_old)
                contents2.append(["text",offset_old,text_old])
                text_old=""

            if kind == "anchor":
                # insert widget
                anchor = param[0].copy()
                if isinstance(anchor, RichTextImage):
                    pixbuff=anchor.get_original_pixbuf()
                    text_pixbuf=pixbuf2latex(pixbuff)
                    if text_pixbuf is None:
                        contents2.append([kind,offset,(param[0],param[0])])
                    else:
                        contents2.append(["text",offset,text_pixbuf])
                else:
                    contents2.append([kind,offset,param])
            else:
                contents2.append([kind,offset,param])

    if text_old is not "":
        contents2.append(["text",offset_old,text_old])

    textbuffer.insert_contents(contents2)
    #widget.view_pages()

    # make sure all inserts are treated as one action
    textbuffer.end_user_action()

def latex2richtext(widget):
    """
    Changes the latex text in textbuffer to its keepnote equivalent

    If some part of a text is marked then only the selected part is changed
    """
    textbuffer=widget.get_buffer()
    sel = textbuffer.get_selection_bounds()
    permeable=_load_permeable(widget.node())
    # do nothing if nothing is selected
    if not sel:
        return

    start, end = sel
    # It is important to create a list out of contents
    contents = list(textbuffer.copy_contents(start, end))

    # make sure all inserts are treated as one action
    textbuffer.begin_user_action()

    textbuffer.delete_selection(False, True)

    text_old=""
    contents2=list()
    len_contents=len(contents)
    counter=0;
    for kind, offset, param in contents:
        # NOTE: offset is ignored
        counter=counter+1;
        if kind == "text":
            text_old=("%s%s")% (text_old,param)
            offset_old=offset

        if kind is not "text" or counter==len_contents:
            if text_old is not "":
                while True:
                    # Following finds an object selection except inline equation
                    text_old ,text_section, latextype = splitlatexobject(text_old)
                    if text_section is None or text_section is "":
                        break
                    if latextype == "EquationArray" or latextype == "Table" or latextype == "Footnote"\
                    or latextype == "Citation" or latextype == "LaTeX" or latextype == "Figure"\
                    or latextype == "InlineEquation":
                        I=latex2pixbuf(permeable,text_section,latextype)
                        if I is not None:
                            contents2.append(["anchor",offset_old,(I,I)])
                        else:
                            # Converting text to image was no successful return text
                            contents2.append(["text",offset_old,text_section])
                    elif latextype == "text":
                        contents2.append(["text",offset_old,text_section])
                    elif latextype == "Bold" or latextype == "Italic":
                        #TODO This part would be implemented to map latex tags to Richtext tags
                        print "Do Nothing"
                    if text_old=="" or text_old is None:
                        break

                text_old=uni2latex(text_old)
                contents2.append(["text",offset_old,text_old])
                text_old=""
            if kind is not "text":
                contents2.append([kind,offset,param])

    if text_old is not "":
        contents2.append(["text",offset_old,text_old])

    textbuffer.insert_contents(contents2)
    # make sure all inserts are treated as one action
    #widget.view_pages()
    textbuffer.end_user_action()

def pixbuf2latex(I):
    """
    Converting PNG images to their corresponding LaTeX code
    """
    tag=I.get_option("tEXt::tag")
    caption=I.get_option("tEXt::caption")
    tex=I.get_option("tEXt::tex")
    label=I.get_option("tEXt::label")
    if tag==None:
       tag="0";
    if label==None:
       label=""
    if caption==None:
       caption=""
    if tex==None:
       tex="";
    if tag=="0":
       return None
    elif tag=="3":
       # Inline Equation
       out_txt=("$%s$")% (tex)
       return out_txt
    elif tag=="4":
       out_txt=("\\begin{align*}%s\label{%s}\end{align*}")% (tex,label)
       return out_txt
    elif tag=="5":
       out_txt=("\\begin{table*}\\begin{tabular}%s\end{tabular}\caption{%s}\label{%s}\end{table*}")%\
       (tex,caption,label)
       return out_txt
    elif tag=="6":
       out_txt=("\\bibliography{%s}")% (tex)
       return out_txt
    elif tag=="7":
       out_txt=("%s")% (tex)
       return out_txt
    elif tag=="8":
       out_txt=("\\footnote{%s}")% (tex)
       return out_txt
    else:
       return None

def uni2latex(text_old):
    """
    Converting unicode text to latex text (Converting Unicode
           characters to their latex equivalent)
    """
    # ToDo: In future the unicode symbols would be converted to latex equivaent
    return text_old

def latex2pixbuf(permeable,out_txt,latex_type):
    """
    Converting latex objects to RichTextImage
    """
    try:
        # Set the working directory
        workdir = tempfile.gettempdir()
        if latex_type== "InlineEquation":
            latex_name='formula.png'
            origfilename=os.path.join(workdir,latex_name )
            result_tag=math2png(out_txt[1:-1], origfilename,permeable)
            if result_tag is -1:
                result_tag=error2png(origfilename)
            tag="3"
            tex=out_txt[1:-1].encode()
            caption=""
            label=""
        if latex_type== "Footnote":
            latex_name='footnote.png'
            origfilename=os.path.join(workdir,latex_name )
            result_tag=footnote2png(origfilename)
            tag="8"
            tex=out_txt[10:-1].encode()
            caption=""
            label=""
        if latex_type== "LaTeX":
            latex_name='latex.png'
            origfilename=os.path.join(workdir,latex_name )
            result_tag=latex2png(out_txt, origfilename,permeable)
            if result_tag is -1:
                result_tag=error2png(origfilename)
            tag="7"
            tex=out_txt.encode()
            caption=""
            label=""
        if latex_type== "Citation":
            latex_name='cite.png'
            origfilename=os.path.join(workdir,latex_name )
            result_tag=cite2png(out_txt[14:-1], origfilename,permeable)
            if result_tag is -1:
                result_tag=error2png(origfilename)
            tag="6"
            tex=out_txt[14:-1].encode()
            caption=""
            label=""
        if result_tag is not -1:
            img = RichTextImage()
            pixbuf=gdk.pixbuf_new_from_file(origfilename)
            pixbuf.save(origfilename,"png", {"tEXt::tag":tag,"tEXt::label":label,\
            "tEXt::caption":caption,"tEXt::tex":tex})
            img.set_from_pixbuf(gdk.pixbuf_new_from_file(origfilename.encode()))
            img.set_filename(latex_name)
        else:
            img=None
    finally:
        if os.path.exists(origfilename):
            os.remove(origfilename)


    return img

def splitlatexobject(txt):
    """
    This function splits the input txt into possibly two parts the first part is either
     latex: A part corresponding to equation array, footnote, table, figure, diagram
     inline equation: A part containig text plus inline equation
     bibliography: A part corresponding to bibliographical information
     footnote: A part corresponding to footnotes
    """
    if txt=="":
        return (txt,None,None)
    index_inline=txt.find("$")
    index_footnote=txt.find("\\footnote{")
    index_latex=txt.find("\\begin{")
    index_bib=txt.find("\\bibliography{")
    if index_inline == -1:
        index_inline = len(txt)
    if index_footnote == -1:
        index_footnote = len(txt)
    if index_latex == -1:
        index_latex = len(txt)
    if index_bib == -1:
        index_bib = len(txt)
    if (index_inline is not 0 and index_footnote is not 0 \
    and index_latex is not 0 and index_bib is not 0):
        index=min(index_inline,index_footnote,index_latex,index_bib)
        txt1=txt[0:index]
        txt2=txt[index:]
        tag="text"
    elif (index_inline < index_footnote) and (index_inline < index_latex) \
    and (index_inline < index_bib):
        index_inline_end=txt.find("$",index_inline+1)
        if index_inline_end is not -1:
            tag="InlineEquation"
            txt1=txt[0:index_inline_end+1]
            txt2=txt[index_inline_end+1:]
        else:
            [txt2,txt1,tag]=[txt,None,None]
    elif (index_footnote < index_inline) and (index_footnote < index_latex) \
    and (index_footnote < index_bib):
        index_footnote_end=findclosing(txt,index_footnote+9)
        if index_footnote_end is not -1:
            tag="Footnote"
            txt1=txt[0:index_footnote_end+1]
            txt2=txt[index_footnote_end+1:]
        else:
            [txt2,txt1,tag]=[txt,None,None]
    elif (index_latex < index_inline) and (index_latex < index_footnote) \
    and (index_latex < index_bib):
        index_latex_middle=txt.find("}",index_latex+1)
        if index_latex_middle is not -1:
            operation=txt[7:index_latex_middle]
            index_latex_end=txt.find("\end{%s}"%operation,index_latex+1)
            if index_latex_end is not -1:
                tag="LaTeX"
                index_latex_end=txt.find("}",index_latex_end)
                txt1=txt[0:index_latex_end+1]
                txt2=txt[index_latex_end+1:]
            else:
                [txt2,txt1,tag]=[txt,None,None]
        else:
            [txt2,txt1,tag]=[txt,None,None]
    elif (index_bib < index_inline) and (index_bib < index_footnote) \
        and (index_bib < index_latex):
        index_bib_end=findclosing(txt,index_bib+14)
        if index_bib_end is not -1:
            tag="Citation"
            txt1=txt[0:index_bib_end+1]
            txt2=txt[index_bib_end+1:]
        else:
            [txt2,txt1,tag]=[txt,None,None]

    else:
        [txt2,txt1,tag]=[txt,None,None]

    return (txt2,txt1,tag)

def findclosing(txt,index):
    """
    This function finds the closing "}" for the latex text ignoring all pairs "{ }"
    in between
    """
    index_end=txt.find("}",index)
    counter=0;
    index_start=index
    while True:
        while True:
            index_start=txt.find("{",index_start+1,index_end)
            if index_start==-1:
                break
            else:
                counter=counter+1
        if counter == 0:
            break
        index_start=index_end
        for iteration in range(0,counter):
            index_end=txt.find("}",index_end+1)
        counter=0
        if index_end == -1:
            break
    return index_end
