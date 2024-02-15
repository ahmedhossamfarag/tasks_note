from enum import Enum, IntEnum
from io import TextIOWrapper
from tkinter import BUTT, INSERT, NO, SE, Button, Entry, Frame, Label, LabelFrame, Misc, Scrollbar, Tk, Widget, dialog, font
import tkinter
from tkinter import filedialog



WndWidth = 800
WndHeight = 600
BPad = 20
BLen = 10
NtHeight = 50
NtWidth = 75
NtLines = 2
NtPad = 5
NSLen = 30



class NoteState(IntEnum):
    Yet = 0
    Ongoing = 1
    Complete = 2



class Note:
    def __init__(self, *, state: NoteState = NoteState.Yet, data: str = ""):
        self.State = state
        self.Data = data
        
    def len(self) -> int:
        return self.Data.count("\n")
    
    def color(self) -> str:
        return "red" if self.State == NoteState.Yet \
            else "orange" if self.State == NoteState.Ongoing \
            else "green"



class NoteBook:
    def __init__(self, *, name: str = "Tasks Note"):
        self.Name = name
        self.Notes: list[Note] = []
        


class NoteView(LabelFrame):
    def __init__(self, master: Misc, note : Note):
        super().__init__(master)
        self.Note = note
        self.Delete = Button(self, text="X")
        self.Delete.grid(row=0, column=0)
        self.State = LabelFrame(self, width=NSLen, height= NSLen, bg = note.color())
        self.State.grid(row=0, column=1)
        self.State.bind('<Button>', self.changeState)
        self.Data = tkinter.Text(self, height= NtLines, width=NtWidth, font=(font.NORMAL, 12))
        self.Data.insert(INSERT, note.Data)
        self.Data.grid(row=0, column=2)
        self.grid_configure(pady=NtPad)
        
    def save(self):
        self.Note.Data = self.Data.get("1.0", "end-1c")
        
    def changeState(self, event):
        self.Note.State = (self.Note.State + 1) % 3
        self.State.config(bg = self.Note.color())
        


class NoteBookView(Frame):
    def __init__(self, master : Misc, book: NoteBook = NoteBook()):
        super().__init__(master, padx=BPad, pady=BPad)
        self.Book = book
        self.Notes: list[NoteView] = []
        for note in book.Notes:
            self.Notes.append(NoteView(self, note))
        self.Index = 0
        self.grid_columnconfigure([i for i in range(0,BLen)],weight=1)
        self.display()
           
    def display(self):
        for i in range(0, min(BLen, len(self.Notes))):
            self.Notes[self.Index + i].grid(row = i, sticky='ew')
        for i in range(self.Index + BLen, len(self.Notes)):
            self.Notes[i].grid_remove()
            

    def add(self, nt):
        ntv = NoteView(self, nt)
        self.Notes.append(ntv)
        ntv.Delete.config(command=lambda:self.remove(ntv))
        self.Index = max(0, len(self.Notes) - BLen)
        self.display()
        self.event_generate('<<Item_added>>')
        

    def remove(self, ntv : NoteView):
        nt = ntv.Note
        self.Book.Notes.remove(nt)
        ntv.destroy()
        self.Notes.remove(ntv)
        if self.Index + BLen > len(self.Notes):
            self.Index = max(0, self.Index - 1)
        self.display()
        self.event_generate('<<Item_removed>>')

    def new(self):
        nt = Note()
        self.Book.Notes.append(nt)
        self.add(nt)

    def save(self):
        for nt in self.Notes:
            nt.save()
        saveBook(self.Book)



class BookScroll(Scrollbar):
    def __init__(self, master: Misc, book : NoteBookView):
        super().__init__(master, command= self.setBook)
        self.Book = book
        self.setScroll()
        book.bind('<<Item_added>>', self.setScroll)
        book.bind('<<Item_removed>>', self.setScroll)
        
    def setScroll(self, obj = None):
        count = len(self.Book.Notes)
        if count == 0:
            self.set(0, 1)
        else:
            pos = float(self.Book.Index) / count
            self.set(pos, min(pos + (float(BLen) / count), 1))

    def setBook(self, *p):
        indx = round(float(p[1]) * len(self.Book.Notes))
        if indx != self.Book.Index:
            self.Book.Index = indx
            self.Book.display()
            self.setScroll()



class ToolsView(Frame):
    def __init__(self, master : Misc):
        super().__init__(master, width= WndWidth)
        self.New = Button(self, text="New")
        self.New.pack(side='left')
        self.Save = Button(self, text="Save")
        self.Save.pack(side='left')
        self.NewB = Button(self, text="New Book")
        self.NewB.pack(side='right')
        self.OpenB = Button(self, text="Open Book")
        self.OpenB.pack(side='right')



class TasksBookView(Tk):
    def __init__(self, book: NoteBook):
        super().__init__(book.Name)
        self.title(book.Name)
        self.geometry("{0}x{1}".format(WndWidth,WndHeight))
        self.resizable(0,0)
        self.Header = ToolsView(self)
        self.Header.grid(column=0, sticky='ew')
        self.Book = NoteBookView(self, book)
        self.Book.grid(row = 1, column=0, sticky='ew')
        self.Scroll = BookScroll(self, self.Book)
        self.Scroll.grid(row=1, column=1, sticky='ns')
        self.grid_columnconfigure(0,weight=1)
        self.Header.New.config(command= self.Book.new)
        self.Header.Save.config(command= self.save)
        self.Header.NewB.config(command= newBook)
        self.Header.OpenB.config(command= openBook)

    def save(self):
        self.Book.save()
        self.title(self.Book.Book.Name)
    

        
def newBook():
     newWnd = TasksBookView(NoteBook())
     newWnd.mainloop()
     


def openBook():
    file = filedialog.askopenfile(filetypes=[("text files", "*.txt")])
    if file != None:
        try:
            book = readBook(file.name)
            newWnd = TasksBookView(book)
            newWnd.mainloop()
        except:
            pass
    pass



def saveBook(b: NoteBook):
    try:
        file = open(b.Name,'r')
    except FileNotFoundError:
        dialog = filedialog.asksaveasfile(filetypes=[("text files", "*.txt")], defaultextension="txt")
        if dialog != None:
            b.Name = dialog.name
        else:
            return
    
    try:
        file = open(b.Name,'w')
        writeBook(b, file)
    except:
        pass



def writeBook(bk: NoteBook, file):
    for n in bk.Notes:
        file.write(str(n.State))
        file.write("\n")
        file.write(n.Data)
        for i in range(n.len(), NtLines):
            file.write("\n")



def readBook(name: str) -> NoteBook:
    bk = NoteBook(name=name)
    file = open(name,'r')
    notes = file.readlines()
    i = 0
    while i < len(notes):
        n = Note()
        n.State = int(notes[i][0])
        n.Data = notes[i+1]+ notes[i+2]
        bk.Notes.append(n)
        i+=3
        
    return bk



wnd = TasksBookView(NoteBook())
wnd.mainloop()
