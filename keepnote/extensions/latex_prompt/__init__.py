"""
LaTeX Prompt Extension
"""

"""
Author:
    Reshad Hosseini <hosseini@bethgelab.org>
    URL: http://www.bethgelab.org/hosseini

Revision History:
    2012/01/01 - Initial version

---

The main code was borrowd from Matt Rasmussen's python code
        "dialog-python.py" (rasmus@mit.edu).
"""

"""

  dialog_latex
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


# python imports
import gettext
import os
import sys
_ = gettext.gettext

# keepnote imports
from keepnote.gui import extension

from keepnote import notebooklib
from keepnote.gui.richtext import RichTextImage
from gtk import gdk

# pygtk imports
try:
    import pygtk
    pygtk.require('2.0')
    import gtk

#    from keepnote.gui import dialog_app_options

except ImportError:
    # do not fail on gtk import error,
    # extension should be usable for non-graphical uses
    pass


sys.path.append(os.path.dirname(__file__))

# latex2png import
from latex_keepnote import *
import dialog_latex

# Different icons for different latex objects
icons = [
        'formula.png',
        'formula.png',
        'table.png',
        'cite.png',
        'diagram.png',
        'footnote.png'
        ]

class Updating (object):

    def __init__(self, page, inviewer, widget):
        """Initialize ReLoading"""
      
        self._page = page
        self._viewer = inviewer
        self._textview= widget # Textview widget

    def view_pages(self, pages=None):   
        if pages ==None:
            self._viewer.goto_node(self._page)          
        else:
            self._viewer.goto_node(pages[0])
    def get_buffer(self):
        return self._textview.get_buffer()
    def node(self):
        return self._page

class Extension (extension.Extension):

    def __init__(self, app):
        """Initialize extension"""
        
        extension.Extension.__init__(self, app)

        self._widget_focus = {}
        self._set_focus_id = {}


    def get_depends(self):
        return [("keepnote", ">=", (0, 7, 1))]

        
    #================================
    # UI setup

    def on_add_ui(self, window):

        # list to focus events from the window
        self._set_focus_id[window] = window.connect("set-focus", self._on_focus)

        # add menu options

        self.add_action(window, "Insert Equation", "Insert Equation",
                        None)

        self.add_action(window, "Inline Equation", "_Inline...",
                        lambda w: self.on_inline_latex(window,0))

        self.add_action(window, "Equation Array", "E_quation Array...",
                        lambda w: self.on_inline_latex(window,1))

        self.add_action(window, "Insert Table...", "Insert Table...",
                        lambda w: self.on_inline_latex(window,2))

        self.add_action(window, "Insert Citation...", "Insert Citation...",
                        lambda w: self.on_inline_latex(window,3))

        self.add_action(window, "Insert LaTeX Code...", "Insert LaTeX Code...",
                        lambda w: self.on_inline_latex(window,4))

        self.add_action(window, "Insert Footnote...", "Insert Footnote...",
                        lambda w: self.on_inline_latex(window,5))

        # add menu options
        self.add_action(window, "Insert LaTeX Permeable", "Insert LaTeX Permeable", 
                         lambda w: self.on_latex_permeable(window))

        self.add_action(window, "Convert Selection to LaTeX", "Convert Selection to LaTeX", 
                         lambda w: self.on_convert_tolatex(window))

        self.add_action(window, "Convert Selection to RichText", "Convert Selection to RichText", 
                         lambda w: self.on_convert_totext(window))

        self.add_ui(window,
                """
                <ui>
                <menubar name="main_menu_bar">
                   <menu action="Tools">
                      <placeholder name="LaTeX">
                        <menu action="Insert Equation">
                           <menuitem action="Inline Equation"/>
                           <menuitem action="Equation Array"/>
                        </menu>
                        <menuitem action="Insert Table..."/>
                        <menuitem action="Insert Citation..."/>
                        <menuitem action="Insert LaTeX Code..."/>
                        <menuitem action="Insert Footnote..."/>
                      </placeholder>
                   </menu>
                   <menu action="Edit">
                      <placeholder name="Viewer">
                         <placeholder name="Editor">
                           <placeholder name="Extension">
                             <menuitem action="Insert LaTeX Permeable"/>
                             <menuitem action="Convert Selection to LaTeX"/>
                             <menuitem action="Convert Selection to RichText"/>
                           </placeholder>
                         </placeholder>
                      </placeholder>
                   </menu>
                </menubar>
                </ui>
                """)

    def on_remove_ui(self, window):
        
        extension.Extension.on_remove_ui(self, window)
        
        # disconnect window callbacks
        window.disconnect(self._set_focus_id[window])
        del self._set_focus_id[window]


    #================================
    # actions

    def _on_focus(self, window, widget):
        """Callback for focus change in window"""
        self._widget_focus[window] = widget

    def on_latex_permeable(self, window):

        notebook = window.get_notebook()
        if notebook is None:
            return

        nodes = window.get_selected_nodes()
        if len(nodes) == 0:
            parent = notebook
        else:
            sibling = nodes[0]
            if sibling.get_parent():
                parent = sibling.get_parent()
            else:
                parent = sibling

        try:
            uri = os.path.join(self.get_base_dir(), "latex_permeable.txt")
            node = notebooklib.attach_file(uri, parent)
            node.rename("LateX Permeable")
            window.get_viewer().goto_node(node)
        except Exception, e:
            window.error("Error while attaching file '%s'." % uri, e)

    def on_inline_latex(self, window, tag):
        """Callback for inserting different latex objects based on tag"""

        widget = self._widget_focus.get(window, None)

        if isinstance(widget, gtk.TextView):

            # Following gets the notebook
            notebook = window.get_notebook()
            if notebook is None:
               return

            nodes = window.get_selected_nodes()
            if len(nodes) == 0:
               return
            else:
               sibling = nodes[0]

            datadir=self.get_base_dir()
            imfile=icons[tag]
            origfilename=os.path.join(datadir, imfile)
            img = RichTextImage()
            img.set_from_pixbuf(gdk.pixbuf_new_from_file(origfilename.encode()))
            widget.get_buffer().insert_image(img, imfile)
            image_path=os.path.join(sibling.get_path(), img.get_filename())
            tagstr=_("%i") %(tag+3)
            ReLoad = Updating(sibling,window.get_viewer(),widget)
            dialog = dialog_latex.LaTeXDialog(ReLoad,tagstr,image_path)
            dialog.show()

    def on_convert_tolatex(self, window):
        """Converting Richtext text to laTeX"""
        widget = self._widget_focus.get(window, None)
        if isinstance(widget, gtk.TextView):
            # Following gets the notebook
            notebook = window.get_notebook()
            if notebook is None:
               return

            nodes = window.get_selected_nodes()
            if len(nodes) == 0:
               return
            else:
               sibling = nodes[0]
            ReLoad = Updating(sibling,window.get_viewer(),widget)
            richtext2latex(ReLoad)

         
    def on_convert_totext(self, window):
        """Converting laTeX to Richtext"""
        widget = self._widget_focus.get(window, None)
        if isinstance(widget, gtk.TextView):
            # Following gets the notebook
            notebook = window.get_notebook()
            if notebook is None:
               return

            nodes = window.get_selected_nodes()
            if len(nodes) == 0:
               return
            else:
               sibling = nodes[0]
            ReLoad = Updating(sibling,window.get_viewer(),widget)
            latex2richtext(ReLoad)
