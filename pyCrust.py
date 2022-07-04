# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ pyCrust v0.0 - "A template for Python projects.""                         ┃
# ┃ Authored by Collin Spears                                                 ┃
# ┃                                                                           ┃
# ┃  'pyCrust' defines various features that can be  enabled/disabled based   ┃
# ┃  on the goals of the main project. This is meant to shortcut the          ┃
# ┃  implementation of common features that I wish to include in most python  ┃ 
# ┃  Apps and scripts such as...                                              ┃
# ┃                                                                           ┃
# ┃  - A GUI                                                                  ┃
# ┃  - Standard and Debug Logging                                             ┃
# ┃  - Config files (JSON -or- XML) for global user modified params.          ┃
# ┃  - Directory creation for consistent file-structure of projects.          ┃
# ┃  - Pre-populated 'README' to get a head-start on documentation.           ┃
# ┃                                                                           ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

import os
from re import M
import time
import json
import queue
import sqlite3
import logging
import threading
import tkinter as tk
from tkinter import ttk, font as tk_font 

VERSION = '0.0'
ROOTPATH = os.getcwd()


class write:
    '''
    Allows for print statements to be sent to the Terminal (print), as well
    as to the standard logging, and to the UI if requested.
    '''
    def __init__(self, string, log_level=0, ui=None, redirect=0):
        self.string = string
        #pyCrust Hooks
        self.log_level = log_level
        self.init_ui = ui
        self.redirect = redirect
        # Actually send string to defined locations.
        self.write_outputs()

    def write_outputs(self):
        if self.redirect == 0:
            print(str(self.string))
        if self.log_level == 1:
            # Write to Standard log.
            logging.info(self.string)
        if self.log_level == 2:
            # Write to Debug log.
            logging.debug(self.string)


class Config:
    '''
    Enables a user-readable config file for quick editing of global params.
    '''
    def __init__(self, dictionary, extension='JSON', ui=None, 
        log_level=0, redirect=0):
        self.conf_table = dictionary
        self.extension = extension
        self.init_ui = ui
        self.log_level = log_level
        self.redirect = redirect
        self._config = None # Set in "create_config"
        self._confpath = os.path.normpath(ROOTPATH + ("\\config\\config." + self.extension))
        # Check vars
        self.check_initvars()

    def check_initvars(self):
        # Check the extension variable is acceptable value.
        ext_vals = ['JSON', 'XML']
        if self.extension not in ext_vals:
            raise UnexpectedInitVar
        if not isinstance(self.conf_table, dict):
            raise UnexpectedInitVar
        # If var check passes
        self.create_config()
    
    def create_config(self):
        '''
        Checks if there is an exisisting "config.x" file. If not, a new file is
        created based on the "extension" provided.
        '''
        write(
            string=('Checking for an exisisting config.' + self.extension 
                + ' file.'),
            log_level=self.log_level,
            ui=self.init_ui,
            redirect=self.redirect,
        )
        alive = os.access(self._confpath, os.W_OK)
        if alive and self.extension == 'JSON':
            write(
                string='JSON file already exist!',
                log_level=self.log_level,
                ui=self.init_ui,
                redirect=self.redirect,
            )
        if alive and self.extension == 'XML':
            # Loadin XML
            print("TODO 6/18 - readxml files")
        if not alive and self.extension == 'JSON':
            try:
                os.makedirs(ROOTPATH + '\\config')
            except FileExistsError:
                pass
            with open(self._confpath, 'w') as file:
                json.dump(self.conf_table, file, indent=4)
            write(
                string='Generated a new "config.json" file.',
                log_level=self.log_level,
                ui=self.init_ui,
                redirect=self.redirect,
            )

    def get_config(self):
        if self.extension == 'JSON':
            # Loadin JSON file.
            with open(self._confpath, 'r') as file:
                self._config = json.load(file)
                write(
                    string='Successfully loaded the config file.',
                    log_level=self.log_level,
                    ui=self.init_ui,
                    redirect=self.redirect,
                )
                return self._config
        elif self.extension == 'XML':
            print(" Jun 24, TODO!")
        else: # When the config file is missing
            write(
                string='Unable to find the config file at "' + self._confpath + '"',
                log_level=self.log_level,
                ui=self.init_ui,
                redirect=self.redirect,
            )
            raise FileNotFoundError


class Logging:
    '''
    Enables Standard and Debug logging, and returns two logging objects for
    easy writing to the pre-configured log locations. 

    'min_log' defines the minimum log level to actually write to the log file.
    0 = None
    1 = Write Info+ Level Logs
    2 = Write Debug+ level logs (omit Info)
    '''
    def __init__(self, min_log=1):
        self.min_log = min_log
        self.log_level = None
        self.conv_loglevel()
        
        self.logdir = os.path.normpath(ROOTPATH + '\\log')
        self.create_log()

    def conv_loglevel(self):
        if self.min_log == 1:
            self.log_level = logging.INFO
        if self.min_log == 2:
            self.log_level = logging.DEBUG

    def create_log(self):
        path = os.path.normpath(self.logdir + '\\main.log')
        alive = os.access(path, os.W_OK)
        if not alive:
            # Create Dir
            try:
                os.makedirs(self.logdir)
            except:
                pass
            # Create the file
            with open(path, 'w+') as logfile:
                logfile.close()
        self.rootlog = logging.basicConfig(
            filename=path, 
            encoding='utf-8', 
            level=self.log_level
        )
        # Configure backup logs here if needed later...
        # Return main.log
        return self.rootlog


class Sqlite:
    '''
    Creates the 'basecamp.db' SQLite3 File - and populates it with the 
    default schema. 

    NOTE: Parameter markers can be used only for expressions, i.e., values.
    You cannot use them for identifiers like table and column names. If a
    query needs to be written with identifiers being a variable, THIS "query"
    SHOULD NOT TAKE INPUT FROM USERS. THIS WILL EXPOSE THE DB TO SQL
    INJECTION. 
    '''

    def __init__(self):
        db_dir = ROOTPATH + "\\data"
        db_path = ROOTPATH + "\\data\\database.sql"
        # Try to open exisiting 'datastore.json'
        if os.access(db_path, os.R_OK):
            write("SQLite3 started successfully! - Connected to DB.")
        else:
            write("Not Found. Generating new 'database.sql' file...")
            # Check if dir exist.
            try:
                os.mkdir(db_dir)
            except FileExistsError:
                pass
            # Creating .db file
            file = open(db_path, "w+")
            file.close()
            write("Successfully created database.sql file")

        # Connecting to sqlite DB
        self.db_connection = sqlite3.connect(db_path)
        # Create default tables
        self.dbshell = self.db_connection.cursor()
        self.dbshell.execute(self.mastertable())
        # Close connection - Jobs Done!
        self.db_connection.commit()
        self.dbshell.close()

    def mastertable(self):
        '''
        Default root table for any pyCrust based project.
        '''
        query = """ CREATE TABLE IF NOT EXISTS master (
                        version TEXT UNIQUE,
                        rkey TEXT UNIQUE                 
             ); """
        return query
            

    def config_schema(self):
        '''
        The table that defines user choices, and general application config
        data such as root paths, UI defaults, etc.
        '''
        query = """ CREATE TABLE IF NOT EXISTS bcamp_config (
                        version TEXT UNIQUE,
                        root_path TEXT NOT NULL,
                        remote_root TEXT NOT NULL,
                        download_root  TEXT NOT NULL,
                        time_zone TEXT NOT NULL,
                        time_format TEXT NOT NULL,
                        dev_mode TEXT NOT NULL,
                        notepad_path TEXT,
                        ui_start_res TEXT NOT NULL,
                        ui_render_top_menu TEXT NOT NULL,
                        ui_caseviewer_location TEXT NOT NULL,
                        ui_render_caseviewer TEXT NOT NULL,
                        ui_caseviewer_search_location TEXT NOT NULL,
                        ui_render_caseviewer_search TEXT NOT NULL,
                        ui_render_favtree TEXT NOT NULL,
                        user_texteditor TEXT NOT NULL                       
             ); """
        return query
            

class UI(tk.Tk):
    '''
    Main Class of Basecamp UI

    This class renders the main UI window, and initializes the Tk/TtK classes
    used through out the application. The idea is for this class to be a 
    "framework" for the rest of the UI elements.

    Further Reading...
    - https://docs.python.org/3/library/tk.html
    - https://docs.python.org/3/library/tk.ttk.html#module-tk.ttk

    '''
    def __init__(self):
        super().__init__()
        # Start the 'logic' thread to run non-UI code. The UI must be 
        # multi-threaded to prevent the Tk "mainloop" from hanging if we need 
        # to process something for some time.
        self.LogicThread()

        # Intializing Main Tk/Ttk Classes
        #self.BottomBar = Tk_BottomBar(self.file_queue)
        self.MasterPane = self.UI_RootPane(self)
        self.BottomBar = self.UI_BottomBar(self)

        # Fullscreen Var for <Alt-Enter>
        self.w_fullscreen = False

        # Configuring Tk ELements for Main Window.
        self.config_widgets()
        self.config_grid()
        self.config_window()
        self.config_binds()
        
        # STARTING TK/TTK UI

    # pyCrust Methods - Available for Dev needs!
    def launch(self):
        '''
        Formally launches the UI 'mainloop'. UI Definitions are frozen once 
        called.
        '''
        self.mainloop()
    
    def shutdown(self):
        '''
        Formally shuts down the UI 'mainloop' closing the tkinter session. 
        '''
        self.mainloop()


    # Tk/UI Methods
    def config_widgets(self):
        '''
        Tk Widgets NOT drawn by Tk_RootPane are defined here.

        This also contains ttk.Style def's for Notebook and Treeview
        '''
        self.configure(background="black")

    def config_grid(self):
        '''
        Initalized Frames and "config_widgets" content is added to the UI 
        geometry manager here. - using tk.grid().
        '''
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.MasterPane.grid(row=0,
            column=0, 
            #columnspan=5, 
            sticky='nsew')
        self.BottomBar.grid(row=1, 
            column=0, 
            columnspan=3, 
            sticky="sew")

    def config_window(self):
        '''
        This method defines the *Master* TK window settings, such as the
        default render size, or "top menu" configuration.
        '''
        # Misc
        self.title("pyCrust")
        self.geometry('800x494')
        #titlebar_photo = tk.PhotoImage(file=self.RPATH + "\\core\\bcamp.gif")
        #self.iconphoto(False, titlebar_photo)

    def config_binds(self):
        #self.bind('<Control-i>', self.reveal_install_loc)
        #self.bind('<Control-d>', self.reveal_download_loc)
        #self.bind('<Control-,>', self.open_settings_menu)
        #self.bind('<Control-n>', self.Workbench.import_tab)
        #self.bind('<Control-b>', self.toggle_CaseViewer)
        #self.bind('<Control-l>', self.launch_bulk_importer)
        #self.bind('<Control-x>', self.export_cases_backup)
        #self.bind('<Control-r>', self.import_cases_backup)
        #self.bind('<Alt_L>', self.toggle_top_menu)
        #self.bind('<Alt-Return>', self.make_fullscreen)
        pass

    def ttk_theme_changes(self):
        '''
        Container method to organize all Ttk theme changes used globally 
        throughout the UI.
        '''
        # Ttk Styles from here...
        self.def_font = tk_font.Font(
            family="Segoe UI", size=12, weight="normal", slant="roman")
        self.tab_font = tk_font.Font(
            family="Segoe UI", size=10, weight="bold", slant="roman")

        # BUGFIX FOR tk TREEVIEW COLORS 
        def fixed_map(option):
            # Fix for setting text colour for tk 8.6.9
            # From: https://core.tcl.tk/tk/info/509cafafae
            #
            # Returns the style map for 'option' with any styles starting with
            # ('!disabled', '!selected', ...) filtered out.

            # style.map() returns an empty list for missing options, so this
            # should be future-safe.
            return [elm for elm in style.map('Treeview', query_opt=option) if
                    elm[:2] != ('!disabled', '!selected')]

        # Defining Treeview header color style.
        style = ttk.Style()
        style.theme_use('default')
        style.element_create(
            "Custom.Treeheading.border", "from", "default")
        style.layout("Custom.Treeview.Heading", [
            ("Custom.Treeheading.cell", {'sticky': 'nswe'}),
            ("Custom.Treeheading.border", {'sticky': 'nswe', 'children': [
                ("Custom.Treeheading.padding", {'sticky': 'nswe', 'children': [
                    ("Custom.Treeheading.image", {
                        'side': 'right', 'sticky': ''}),
                    ("Custom.Treeheading.text", {'sticky': 'we'})
                ]})
            ]}),
        ])
        style.layout("Custom.Treeview", [('Custom.Treeview.treearea', {'sticky': 'nswe'})])
        style.configure("Custom.Treeview.Heading",
                        background="#212121", activebackground="#313131", foreground="white", relief="flat")
        style.map("Custom.Treeview.Heading",
                    relief=[('active', 'groove'), ('pressed', 'flat')])
        style.map('Custom.Treeview',
                  foreground=fixed_map('foreground'),
                  background=fixed_map('background'),
                  )
        style.configure("Custom.Treeview",
                        fieldbackground="#0a0a0a", 
                        background="#0a0a0a", 
                        foreground="#fdfdfd",
                        relief='flat',
                        highlightthickness=0,
                        bd=0,)
        
        # Defining Scrollbar Styles.
        style.configure("Vertical.TScrollbar", gripcount=0,
                background="#2B2B28", darkcolor="red", lightcolor="red",
                troughcolor="#101010", bordercolor="#101010", arrowcolor="#5E5E58",
                troughrelief='flat', borderwidth=0, relief='flat')
        style.configure("Horizontal.TScrollbar", gripcount=0,
                background="#404247", darkcolor="red", lightcolor="red",
                troughcolor="#101010", bordercolor="black", arrowcolor="black",
                troughrelief='flat', borderwidth=0, relief='flat')

        # Defining the Notebook style colors for "Worktabs".
        myTabBarColor = "#10100B"
        myTabBackgroundColor = "#1D1E19"
        myTabForegroundColor = "#8B9798"
        myActiveTabBackgroundColor = "#414438"
        myActiveTabForegroundColor = "#FFE153"

        style.map("TNotebook.Tab", background=[("selected", myActiveTabBackgroundColor)], foreground=[("selected", myActiveTabForegroundColor)]);
        # Import the Notebook.tab element from the default theme
        style.element_create('Plain.Notebook.tab', "from", 'clam')
        # Redefine the TNotebook Tab layout to use the new element
        style.layout("TNotebook.Tab",
            [('Plain.Notebook.tab', {'children':
                [('Notebook.padding', {'side': 'top', 'children':
                    [('Notebook.focus', {'side': 'top', 'children':
                        [('Notebook.label', {'side': 'top', 'sticky': ''})],
                    'sticky': 'nswe'})],
                'sticky': 'nswe'})],
            'sticky': 'nswe'})])
        
        style.configure("TNotebook", background=myTabBarColor, borderwidth=0, bordercolor=myTabBarColor, focusthickness=40)
        style.configure("TNotebook.Tab", background=myTabBackgroundColor,
            foreground=myTabForegroundColor, lightcolor=myTabBarColor,
            borderwidth=0, bordercolor=myTabBackgroundColor, font=self.tab_font)

    def add_sidebar(self):
        #TODO
        pass

    def add(self, widget):
        self.MasterPane.add(widget)

    # Sub-Classes for UI.
    class LogicThread:
        '''
        Master Queue for all logic besides the UI thread.

        The 'freq' var determines the timing of the sleep within the 
        processing loop. The options are...

        'lazy'   ... 2.0 second(s)
        'normal' ... 1.0 second(s)
        'agro'   ... 0.5 second(s)
        '''
        def __init__(self, freq='normal'):
            self.q = queue.Queue()

            # Vars used for Progressbar updates. Callbacks are registered in UI.
            #self.queue_size = 0
            #self.queue_callback = callbackVar()
            #self.progress_obj = callbackVar()

            threading.Thread(target=self.worker_thread, name="logicDaemon", daemon=True).start()

        def worker_thread(self):
            '''
            Daemon Thread for FileOpsQueue
            '''
            write('Starting logicDaemon Processing Loop')
            while True: # Infin. Loop
                item = self.q.get()
                #print("$.fq", item)
                item.start() # Starting thread_obj
                # Enter nested while until 'item' thread is complete.
                while item.is_alive():
                    time.sleep(0.5)
                # Exit and go to next item in Queue if any.
                self.q.task_done()

    # UI Widget Default Definitions.
    class UI_RootPane(tk.PanedWindow):
        '''
        This is the "Master Pane" that contains all main Widget frames such as
        "Tk_WorkspaceTabs" or "Tk_CaseViewer" - Allowing them to be resized
        via Sash grips.
        '''
        def __init__(self, master):
            super().__init__(master)
            self.configure(
                handlesize=16,
                handlepad=100,
                sashwidth=2,
                background="#1D2021"
        )


    class UI_BottomBar(tk.Frame):
        '''
        A dynamic Frame at the bottom of the UI to store Connection status, and
        Progressbar details.
        '''
        def __init__(self, master):
            super().__init__(master=master)
            # ProgressBar Vars
            self.progress_strVar = tk.StringVar()
            self.progress_perc_strVar = tk.StringVar()
            # Render widgets.
            self.config_widgets()
            self.config_grid()

        def config_widgets(self):
            # Font
            self.def_font = tk_font.Font(
                family="Segoe UI", size=8, weight="normal", slant="roman")

            # Colors
            self.base_bg = "#282828"
            self.base_fg = "#7E7E71"
            self.prog_fg = "#A6E22E"

            # Root Background color
            self.configure(
                background=self.base_bg
            )

            # FileOps Frame
            self.left_frame = tk.Frame(
                self,
                background=self.base_bg
            )
            self.queue_label = tk.Label(
                self.left_frame,
                #textvariable=self.queue_strVar,
                background=self.base_bg,
                foreground=self.base_fg,
                relief="flat"
            )        
            self.progress_percent = tk.Label(
                self.left_frame,
                #textvariable=self.progress_perc_strVar,
                background=self.base_bg,
                foreground=self.prog_fg           
            )
            self.progress_label = tk.Label(
                self.left_frame,
                #textvariable=self.progress_strVar,
                background=self.base_bg,
                foreground=self.base_fg,
            )


            # Connectivity/Ver Frame
            self.right_frame = tk.Frame(
                self,
                background=self.base_bg
            )
            self.bb_ver = tk.Label(
                self.right_frame,
                text=VERSION,
                background=self.base_bg,
                foreground=self.base_fg,
                font=self.def_font
            )

        def config_grid(self):
            self.rowconfigure(0, weight=1)
            self.columnconfigure(0, weight=1)
            # Root Frames 
            self.left_frame.grid(
                row=0, column=0, sticky="nsw"
            )
            self.right_frame.grid(
                row=0, column=1, sticky='nse'
            )

            # Filesops Frame Grid
            self.queue_label.grid(
                row=0, column=0, sticky='nsw', padx=1, pady=5
            )
            self.progress_percent.grid(
                row=0, column=1, sticky='nsw', padx=1, pady=5
            )
            self.progress_label.grid(
                row=0, column=2, sticky='nsw', padx=1, pady=5
            )
            # Conn Frame Grid
            self.bb_ver.grid(row=0, column=0, sticky='se', padx=5, pady=5)


        # ProgressBar Methods
        def update_progressbar(self, new_progress_obj):
            '''
            Callback method whenever *FilesOpsQ.progress_obj* var is modified from
            the FileOpsQueue daemon initialized on start.

            Parses the 'new_progress_obj' dictionary which contains a default
            'mode' value, and any other info provided from the API scripts
            for progress string formatting, which is done here!
            '''
            def calc_percentage(cursize, totalsize):
                # Converts Totalsize/cursize to a rounded percentage.
                raw_percent = cursize / totalsize
                formated_percent = "{:.0%}".format(raw_percent)
                return formated_percent
            
            if new_progress_obj['mode'] == None:
                # Set when reset by FileOps Worker Thread
                self.progress_strVar.set("")
                self.progress_perc_strVar.set("")

    
    class CustomTk_CreateToolTip(object):
            '''
            create a tooltip for a given widget, originally from Stack.

            https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tk
            '''

            def __init__(self, widget, text='widget info'):
                self.waittime = 500  # miliseconds
                self.wraplength = 180  # pixels
                self.widget = widget
                self.text = text
                self.widget.bind("<Enter>", self.enter)
                self.widget.bind("<Leave>", self.leave)
                self.widget.bind("<ButtonPress>", self.leave)
                self.id = None
                self.tw = None

            def enter(self, event=None):
                self.schedule()

            def leave(self, event=None):
                self.unschedule()
                self.hidetip()

            def schedule(self):
                self.unschedule()
                self.id = self.widget.after(self.waittime, self.showtip)

            def unschedule(self):
                id = self.id
                self.id = None
                if id:
                    self.widget.after_cancel(id)

            def showtip(self, event=None):
                x = y = 0
                try:
                    x, y, cx, cy = self.widget.bbox("insert")
                except:
                    pass
                x += self.widget.winfo_rootx() + 0
                y += self.widget.winfo_rooty() + 0
                # creates a toplevel window
                self.tw = tk.Toplevel(self.widget)
                # Leaves only the label and removes the app window
                self.tw.wm_overrideredirect(True)
                self.tw.wm_geometry("+%d+%d" % (x, y))


                #%%hex
                label = tk.Label(self.tw, text=self.text, justify='center',
                                background="#ffffff", relief='solid', borderwidth=1,
                                wraplength=self.wraplength)


                
                label.pack(ipadx=1)

            def hidetip(self):
                tw = self.tw
                self.tw = None
                if tw:
                    tw.destroy()


    class CustomTk_autoEntry(ttk.Entry):
        """
        Subclass of tk.Entry that features autocompletion.
        To enable autocompletion use set_completion_list(list) to define 
        a list of possible strings to hit.
        To cycle through hits use down and up arrow keys.
        """
        tk_umlauts=['odiaeresis', 'adiaeresis', 'udiaeresis', 'Odiaeresis', 'Adiaeresis', 'Udiaeresis', 'ssharp']

        def set_completion_list(self, completion_list):
            self._completion_list = completion_list
            self._hits = []
            self._hit_index = 0
            self.position = 0
            self.bind('<KeyRelease>', self.handle_keyrelease)               

        def autocomplete(self, delta=0):
            """autocomplete the Entry, delta may be 0/1/-1 to cycle through possible hits"""
            if delta: # need to delete selection otherwise we would fix the current position
                self.delete(self.position, tk.END)
            else: # set position to end so selection starts where textentry ended
                self.position = len(self.get())
            # collect hits
            _hits = []
            for element in self._completion_list:
                #if element.startswith(self.get().lower()):
                if element.startswith(self.get()):
                    _hits.append(element)
            # if we have a new hit list, keep this in mind
            if _hits != self._hits:
                self._hit_index = 0
                self._hits=_hits
            # only allow cycling if we are in a known hit list
            if _hits == self._hits and self._hits:
                self._hit_index = (self._hit_index + delta) % len(self._hits)
            # now finally perform the auto completion
            if self._hits:
                self.delete(0,tk.END)
                self.insert(0,self._hits[self._hit_index])
                self.select_range(self.position,tk.END)
                            
        def handle_keyrelease(self, event):
            """event handler for the keyrelease event on this widget"""
            if event.keysym == "BackSpace":
                self.delete(self.index(tk.INSERT), tk.END) 
                self.position = self.index(tk.END)
            if event.keysym == "Left":
                if self.position < self.index(tk.END): # delete the selection
                    self.delete(self.position, tk.END)
                else:
                    self.position = self.position-1 # delete one character
                    self.delete(self.position, tk.END)
            if event.keysym == "Right":
                self.position = self.index(tk.END) # go to end (no selection)
            if event.keysym == "Down":
                self.autocomplete(1) # cycle to next hit
            if event.keysym == "Up":
                self.autocomplete(-1) # cycle to previous hit
            # perform normal autocomplete if event is a single key or an umlaut
            if len(event.keysym) == 1 or event.keysym in CustomTk_autoEntry.tk_umlauts:
                self.autocomplete()


    class CustomTk_Textbox(tk.Text):
        '''
        Same as the native Tk Text class, with the added proxy method when text is
        modified. 
        
        Notes from stack...
            "The proxy in this example does three things:

            First it calls the actual widget command, passing in all of the arguments it received.
            Next it generates an event for every insert and every delete
            Then it then generates a virtual event
            And finally it returns the results of the actual widget command
            You can use this widget exactly like any other Text widget, with the added benefit that you can bind to <<TextModified>>."

        https://stackoverflow.com/questions/40617515/python-tkinter-text-modified-callback
        '''
        def __init__(self, *args, **kwargs):
            tk.Text.__init__(self, *args, **kwargs)

            # create a proxy for the underlying widget
            self._orig = self._w + "_orig"
            self.tk.call("rename", self._w, self._orig)
            self.tk.createcommand(self._w, self._proxy)

        def _proxy(self, command, *args):
            cmd = (self._orig, command) + args
            try:
                result = self.tk.call(cmd)
            except Exception:
                return None

            if command in ("insert", "delete", "replace"):
                self.event_generate("<<TextModified>>")

            return result



# Custom Error Exception codes for pyCrust
class UnexpectedInitVar(Exception):
    '''
    Raised when there is an "__init__" value for a class that is not in the
    expected values list in "pyCrust.*.check_initvars()"
    '''
    pass #Do nothing and let the dev handle this error.
