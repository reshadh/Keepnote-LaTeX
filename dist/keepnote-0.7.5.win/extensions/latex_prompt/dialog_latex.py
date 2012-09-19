"""
A dialog for converting latex code to png images embedded in keepnote text editor
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
#import os
import sys
#import StringIO

# pygtk imports
import pygtk
pygtk.require('2.0')
import gtk
import gtk.gdk
from gtk import gdk
import pango

# latex2png import
from latex2png import *
from latex_keepnote import _load_permeable
# keepnote imports
import keepnote
#from keepnote.gui import Action


def move_to_start_of_line(it):
    """Move a TextIter it to the start of a paragraph"""

    if not it.starts_line():
        if it.get_line() > 0:
            it.backward_line()
            it.forward_line()
        else:
            it = it.get_buffer().get_start_iter()
    return it

def move_to_end_of_line(it):
    """Move a TextIter it to the start of a paragraph"""
    it.forward_line()
    return it


class Stream (object):

    def __init__(self, callback):
        self._callback = callback

    def write(self, text):
        self._callback(text)

    def flush(self):
        pass

class LaTeXDialog (object):
    """LaTeX dialog"""

    def __init__(self, main_window, tag=0, image_path=''):
        self.main_window = main_window
        self._TAG=tag
        self._image_path=image_path
        self._page_scrolls = {}            # remember scroll in each page
        self._page_cursors = {}
        # Saving Cursors
        if main_window._page is not None:
            it = main_window._textview.get_buffer().get_insert_iter()
            self._page_cursors[main_window._page] = it.get_offset()

            x, y = main_window._textview.window_to_buffer_coords(
                  gtk.TEXT_WINDOW_TEXT, 0, 0)
            it = main_window._textview.get_iter_at_location(x, y)
            self._page_scrolls[main_window._page] = it.get_offset()

        # Following line is needed to save figures to directory befor starting
        # Saving is needed when inserting latex object or when one pastes
        # the content to new node
        self.main_window.view_pages([main_window._page])
        self.outfile = Stream(self.output_text)
        self.errfile = Stream(lambda t: self.output_text(t, "error"))

        self.error_tag = gtk.TextTag()
        self.error_tag.set_property("foreground", "red")
        self.error_tag.set_property("weight", pango.WEIGHT_BOLD)

        self.info_tag = gtk.TextTag()
        self.info_tag.set_property("foreground", "blue")
        self.info_tag.set_property("weight", pango.WEIGHT_BOLD)

    def show(self):

        # setup environment
        self.env = {"window": self.main_window,
                    "info": self.print_info}

        # create dialog
        self.dialog = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.dialog.connect("delete-event", lambda d,r: self.dialog.destroy())
        self.dialog.ptr = self
        self.dialog.set_default_size(400, 400)

        self.vpaned = gtk.VPaned()
        self.dialog.add(self.vpaned)
        self.vpaned.set_position(200)

        # editor buffer
        self.editor = gtk.TextView()
        self.editor.connect("key-press-event", self.on_key_press_event)
        f = pango.FontDescription("Courier New")
        self.editor.modify_font(f)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.add(self.editor)
        self.vpaned.add1(sw)

        # output buffer
        self.output = gtk.TextView()
        self.output.set_wrap_mode(gtk.WRAP_WORD)
        f = pango.FontDescription("Courier New")
        self.output.modify_font(f)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.add(self.output)
        self.vpaned.add2(sw)

        self.output.get_buffer().tag_table.add(self.error_tag)
        self.output.get_buffer().tag_table.add(self.info_tag)

        self.dialog.show_all()
        self.editor_text()
        #print "TAG"
        #print self._TAG
        if self._TAG == 0:
            self.output_text("Press Ctrl+Enter to execute. Ready...\n", "info")
        elif self._TAG == "1":
            self.output_text("Press Ctrl+Enter to save the Caption. Ready...\n", "info")
        elif self._TAG == "2":
            self.output_text("Press Ctrl+Enter to save the Label. Ready...\n", "info")
        elif self._TAG == "3":
            self.output_text("Press Ctrl+Enter to insert and save the inline Equation. Ready...\n", "info")
        elif self._TAG == "4":
            self.output_text("Press Ctrl+Enter to insert and save the Equation. Ready...\n", "info")
        elif self._TAG == "5":
            self.output_text("Press Ctrl+Enter to insert and save the Table. Ready...\n", "info")
        elif self._TAG == "6":
            self.output_text("Press Ctrl+Enter to insert and save the Citation. Ready...\n", "info")
        elif self._TAG == "7":
            self.output_text("Press Ctrl+Enter to insert and save the LaTeX. Ready...\n", "info")
        elif self._TAG == "8":
            self.output_text("Press Ctrl+Enter to save the footnote. Ready...\n", "info")
        #self.main_window.view_pages([self.main_window._page])
        #self._load_cursor()


    def on_key_press_event(self, textview, event):
        """Callback from key press event"""

        if (event.keyval == gtk.keysyms.Return and
            event.state & gtk.gdk.CONTROL_MASK):
            # execute
            self.execute_buffer()
            return True

        if event.keyval == gtk.keysyms.Return:
            # new line indenting
            self.newline_indent()
            return True


    def newline_indent(self):
        """Insert a newline and indent"""

        buf = self.editor.get_buffer()

        it = buf.get_iter_at_mark(buf.get_insert())
        start = it.copy()
        start = move_to_start_of_line(start)
        line = start.get_text(it)
        indent = []
        for c in line:
            if c in " \t":
                indent.append(c)
            else:
                break
        buf.insert_at_cursor("\n" + "".join(indent))


    def execute_buffer(self):
        """Execute code in buffer"""

        buf = self.editor.get_buffer()
        pages=[self.main_window._page]
        #self.main_window.view_pages(pages)
        #self.dialog.present()
        sel = buf.get_selection_bounds()
        if len(sel) > 0:
            # get selection
            start, end = sel
            if self._TAG == "1":
                self.output_text("Saving selection to the Caption:\n", "info")
            elif self._TAG == "2":
                self.output_text("Saving selection to the Label:\n", "info")
            else:
                self.output_text("Saving and Executing the selection:\n", "info")

        else:
            # get all text
            start = buf.get_start_iter()
            end = buf.get_end_iter()
            if self._TAG == "1":
                 self.output_text("Saving buffer to the Caption:\n", "info")
            elif self._TAG == "2":
                 self.output_text("Saving buffer to the Label:\n", "info")
            else:
                self.output_text("Saving and Executing the buffer:\n", "info")

        # get text in selection/buffer
        text = start.get_text(end)

        # execute code
        I=gdk.pixbuf_new_from_file(self._image_path)
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
        if self._TAG == "1":
            # Saving the tag to the file
            caption=text.encode()
        elif self._TAG == "2":
            # Saving the tag to the file
            label=text.encode()
        else:
            # Saving the tag to the file
            tex=text.encode()
            # Executing Latex to get the picture out
            self.execute_code(tex)
            I=gdk.pixbuf_new_from_file(self._image_path)
            tag=self._TAG
        print {"tEXt::tag":tag,"tEXt::label":label}
        I.save(self._image_path,"png", {"tEXt::tag":tag,"tEXt::label":label,\
        "tEXt::caption":caption,"tEXt::tex":tex})
        self.main_window.view_pages(pages)
        self.dialog.present()
        self._load_cursor()

    def execute_code(self, tex):
        latex_permeable=_load_permeable(self.main_window._page)
        if self._TAG == "3":
            tag=math2png(tex, self._image_path, latex_permeable)
            if tag is -1:
                tag=error2png(self._image_path)
        elif self._TAG == "4":
            tag=eqn2png(tex, self._image_path, latex_permeable)
            if tag is -1:
                tag=error2png(self._image_path)
        elif self._TAG == "5":
            tag=table2png(tex, self._image_path, latex_permeable)
            if tag is -1:
                tag=error2png(self._image_path)
        elif self._TAG == "6":
            tag=cite2png(tex, self._image_path, latex_permeable)
            if tag is -1:
                tag=error2png(self._image_path)
        elif self._TAG == "7":
            tag=latex2png(tex, self._image_path, latex_permeable)
            if tag is -1:
                tag=error2png(self._image_path)

    def _load_cursor(self):

        # place cursor in last location
        if self.main_window._page in self._page_cursors:
            offset = self._page_cursors[self.main_window._page]
            it = self.main_window._textview.get_buffer().get_iter_at_offset(offset)
            self.main_window._textview.get_buffer().place_cursor(it)

        # place scroll in last position
        if self.main_window._page in self._page_scrolls:
            offset = self._page_scrolls[self.main_window._page]
            buf = self.main_window._textview.get_buffer()
            it = buf.get_iter_at_offset(offset)
            mark = buf.create_mark(None, it, True)
            self.main_window._textview.scroll_to_mark(mark,
                0.49, use_align=True, xalign=0.0)
            buf.delete_mark(mark)


    def output_text(self, text, mode="normal"):
        """Output text to output buffer"""

        buf = self.output.get_buffer()

        # determine whether to follow
        mark = buf.get_insert()
        it = buf.get_iter_at_mark(mark)
        follow = it.is_end()

        # add output text
        if mode == "error":
            buf.insert_with_tags(buf.get_end_iter(), text, self.error_tag)
        elif mode == "info":
            buf.insert_with_tags(buf.get_end_iter(), text, self.info_tag)
        else:
            buf.insert(buf.get_end_iter(), text)

        if follow:
            buf.place_cursor(buf.get_end_iter())
            self.output.scroll_mark_onscreen(mark)

    def editor_text(self):
        """Output text to editor buffer"""

        buf = self.editor.get_buffer()

        # Loading the image and its text chunks
        I=gdk.pixbuf_new_from_file(self._image_path)
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
           tex=""
        if self._TAG == "1":
               # add output text
               text=caption.encode("utf-8")
               buf.insert(buf.get_end_iter(), text)
        elif self._TAG == "2":
               # add output text
               text=label.encode("utf-8")
               buf.insert(buf.get_end_iter(), text)
        else:
               # add output text
               text=tex.encode("utf-8")
               buf.insert(buf.get_end_iter(), text)

    def print_info(self):

        print "COMMON INFORMATION"
        print "=================="
        print

        keepnote.print_runtime_info(sys.stdout)

        print "Open notebooks"
        print "--------------"
        print "\n".join(n.get_path() for n in self.app.iter_notebooks())
