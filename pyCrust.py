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
import time
import json
import queue
import ctypes
import sqlite3
import logging
import threading
import tkinter as tk
from tkinter import ttk, font as tk_font
from turtle import back
 

VERSION = '0.0'
ROOTPATH = os.getcwd()
ACTIVE_CONSOLE = None


class write:
    '''
    Allows for print statements to be sent to the Terminal (print), as well
    as to the standard logging, and to the UI if requested.
    '''
    def __init__(self, string, log_level=0, redirect=0):
        self.string = string
        
        #pyCrust Hooks
        self.log_level = log_level
        self.active_console = ACTIVE_CONSOLE
        self.redirect = redirect
        # Actually send string to defined locations.
        self.write_outputs()

    def write_outputs(self):
        # Handle UI output location
        if self.active_console != None and self.redirect == 1:
            print("\t ui>", self.string)
            self.active_console.std_console(self.string)
        elif self.redirect == 0:
            print(str(self.string))

        # Handle Log handler location
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
            redirect=self.redirect,
        )
        alive = os.access(self._confpath, os.W_OK)
        if alive and self.extension == 'JSON':
            write(
                string='JSON file already exist!',
                log_level=self.log_level,
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
                    redirect=self.redirect,
                )
                return self._config
        elif self.extension == 'XML':
            print(" Jun 24, TODO!")
        else: # When the config file is missing
            write(
                string='Unable to find the config file at "' + self._confpath + '"',
                log_level=self.log_level,
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
        self._Logic = self.LogicThread()

        # Intializing Main Tk/Ttk Classes
        self._ThemeEngine = self.ThemeEngine()
        self.MasterPane = self.UI_RootPane(self)
        self.BottomBar = self.UI_BottomBar(self)

        # Fullscreen Var for <Alt-Enter>
        self.w_fullscreen = False

        # Configuring Tk ELements for Main Window.
        self._config_window()
        self._config_widgets()
        self._config_grid()
        self._config_binds()

    
    # Tk/UI Methods
    def _config_widgets(self):
        '''
        Tk Widgets NOT drawn by Tk_RootPane are defined here.

        This also contains ttk.Style def's for Notebook and Treeview
        '''
        self.configure(background="black")

    def _config_grid(self):
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

    def _config_window(self):
        '''
        This method defines the *Master* TK window settings, such as the
        default render size, or "top menu" configuration.
        '''
        # Misc
        self.title("pyCrust")
        self.geometry('800x494')
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        #titlebar_photo = tk.PhotoImage(file=self.RPATH + "\\core\\bcamp.gif")
        #self.iconphoto(False, titlebar_photo)

    def _config_binds(self):
        self.bind('<Control-`>', self.reveal_install_loc)
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

    def _ttk_theme(self):
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

    def set_frame(self, widget):
        self.MasterPane._main.set_frame(widget)

    def add_sidebar(self, widget):
        self.MasterPane._sidebar.add(widget)
    
    def show_console(self):
        self.MasterPane.show_console()
    
    def minimize_console(self):
        self.MasterPane.minimize_console()
    
    def reveal_install_loc(self, event): 
        os.startfile(ROOTPATH)
    
    def use_theme(self, theme_name):
        self._ThemeEngine.style.theme_use(theme_name)

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

    def add_task(self, proc, args=None, name=None,):
            '''
            Passthrough function to add a executable object to the 'Logic Thread'.

            When using the UI, we need to do long running work on this thread to
            avoid hanging the UI which *MUST* run on the main thread.
            '''
            # Format input vars.
            if name == None:
                _name = ('logic.Thread-'+str(self._Logic.qsize))
            else:
                _name = ('logic.'+name+str(self._Logic.qsize))
            # Pass vars to LogicThread.add(). Error handling done there.
            self._Logic.add(proc, args, _name)
            # Write a Debug log message.
            write((_name + ' added to logicDaemon.'), log_level=2)


    
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
            self.qsize = 0 # Counter for items in Queue. Explict for accuracy.
            self.freq = freq

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
            # Calc thread poll frequency.
            if self.freq == 'lazy':
                _pollrate = 2.0
            elif self.freq == 'normal':
                _pollrate = 1.0
            elif self.freq == 'agro':
                _pollrate = 0.37
            
            # Enter Infinite Loop for 'logicDaemon'
            while True:
                # Get new process pending in queue.
                item = self.q.get()
                #print("$.", item)
                item.start() # Starting thread_obj
                # Enter nested while until 'item' thread is complete.
                while item.is_alive():
                    time.sleep(_pollrate)
                # Exit and go to next item in Queue if any.
                self.q.task_done()
                self.qsize -= 1
        
        def add(self, proc, args=None, name_string=None):
            '''
            Function to add a process into the LogicThread Queue. The 'proc'
            object will be converted to a Thread obj, and put into the 
            'logicDaemon' queue to be executed.
            
            This will be spawned as a child thread with schema 'logic.<Name>'. 
            <Name> is defined by the 'name_string' if provided. If no name is 
            provided, the name will default to a 'logic.Thread-00' with '00' 
            being the number of items ahead of the new process in the queue.
            '''
            print('.add')
            # First, increment self.qsize
            self.qsize += 1
            # Convert 'proc' to a thread Object.
            new_thread = self.ReturnThread(
                target=proc,
                name=name_string,
                args=args
            )
            # Now, put into into the "Worker Thread"
            if type(proc) != None:
                self.q.put(new_thread)
            else:
                print('logic.add_task: ERROR! proc obj is <None>')
        

        class ReturnThread(threading.Thread):
            '''
            Subclass of the 'threading.Thread' class, with the benefit of a 
            the return value being available for retreival if needed.
            '''
            def __init__(self, group=None, target=None, name=None,
                        args=(), kwargs={}, Verbose=None):
                threading.Thread.__init__(self, group, target, name, 
                                        args, kwargs)
                self._return = None

            def run(self):
                print(type(self._target))
                if self._target is not None:
                    self._return = self._target(*self._args,
                                                        **self._kwargs)
            def join(self, *args):
                threading.Thread.join(self, *args)
                return self._return


    class ThemeEngine:
        def __init__(self):
            write("ThemeEngine is starting!")
            self.style = ttk.Style()
            # Generate available custom themes.
            self.create_themes()
            write("Available Themes:" + str(self.style.theme_names()), 1) 
        
        def create_themes(self):
            '''
            FUTURE: Reads a config file of some kind and will generate themes
            based on the contents. 
            CURRENT: Concept space for defining themes.
            '''
            #┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
            #┃  Resetti --- Theme Design. (0) Darkest ->- (4) Lightest        ┃

            # ->- Background 
            bg_0 = "#1D2021"
            bg_1 = "#282828"
            bg_2 = "#3C3836"
            bg_3 = "#504945"
            bg_4 = "#665C54"
            # ->- Foreground
            fg_0 = "#A89984"
            fg_1 = "#BDAE93"
            fg_2 = "#D5C4A1"
            fg_3 = "#EBDBB2"
            fg_4 = "#FBF1C7"
            # ->- Syntax/ANSI codes
            ansi_red = "#CC241D"
            ansi_green = "#98971A"
            ansi_blue = "#458588"
            ansi_yellow = "#D79921"
            ansi_purple = "#B16286"
            ansi_aqua = "#689D6A"
            ansi_orange = "#FE8019"

            #┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
            self.style.theme_create(
                themename='Resetti',
                parent='default',
                settings={
                    #--> Default Button
                    "TButton": {
                        "configure": {"padding": 5, "relief": 'flat'},
                        "map": {
                            "background": [("active", bg_3),
                                            ("!disabled", bg_2)],
                            "fieldbackground": [("!disabled", bg_2)],
                            "foreground": [("focus", fg_3),
                                            ("!disabled", fg_2)]
                        }
                    },
                    #--> Default Frame
                    "TFrame": {
                        "configure": {"padding": 1},
                        "map": {
                            "background": [("active", bg_1),
                                            ("!disabled", bg_1)],
                        }
                    },
                    #--> BottomBar Frame
                    "BottomBar.TFrame": {
                        "configure": {"padding": 1},
                        "map": {
                            "background": [("active", bg_0),
                                            ("!disabled", bg_0)],
                        }
                    },
                    #--> BottomBar Label
                    "BottomBar.TLabel": {
                        "configure": {
                            "padding": 1,
                            "foreground": fg_0
                        },
                        "map": {
                            "background": [("active", bg_0),
                                            ("!disabled", bg_0)],
                        }
                    },
                    #--> BottomBar Separator
                    "BottomBarSep.TFrame": {
                        "configure": {
                            "padding": 0,
                            "height": 1
                            }
                    },
                    #--> Console Frame
                    "Console.TFrame": {
                        "configure": {"padding": 1},
                        "map": {
                            "background": [("active", bg_0),
                                            ("!disabled", bg_0)],
                        }
                    },
                    #--> Console Button
                    "Console.TButton": {
                        "configure": {
                            "padding": 1,
                            "relief": 'flat'
                        },
                        "map": {
                            "background": [("active", bg_0),
                                            ("!disabled", bg_0)],
                            "foreground": [("active", ansi_red),
                                            ("!disabled", fg_0)],
                        }
                    },
                }
            )


    # UI Widget Default Definitions.
    class UI_RootPane(tk.PanedWindow):
        '''
        This is the "Master Pane" that contains all main Widget frames such as
        "Tk_WorkspaceTabs" or "Tk_CaseViewer" - Allowing them to be resized
        via Sash grips.
        '''
        def __init__(self, master):
            super().__init__(master=master, orient=tk.HORIZONTAL)
            self.configure(
                background="#32302F",
                sashwidth=2
            )
            self.config_widgets()

        def config_widgets(self):
            '''
            Defines the Sidebar, Main, and Console Windows.
            '''
            self._main = UI.UI_Main(self)
            self._sidebar = UI.UI_Sidebar(self)
            self.add(self._sidebar)
            self.add(self._main)
        
        def show_console(self):
            '''
            Expands the console window. This is default behavior when no 
            'frame' is set.
            '''
            # Expliclty defining in the event of a collapse.
            self._console = UI.UI_Console
            self._main.add_child(self._console)
        
        def minimize_console(self):
            '''
            Collapses the console window, which can be expanded later.
            '''
            self._main.forget(1)
        
        def hide_console(self):
            '''
            Removes the console from the window completely.
            '''


    class UI_Main(tk.PanedWindow):
        def __init__(self, master):
            super().__init__(master=master, orient=tk.VERTICAL)
            self.configure(
                background="#32302F",
                sashwidth=2
            )
            # And render main frame.
            self._frame = ttk.Frame(
                self,
            )
            self.add(self._frame, )

        def set_frame(self, widget):
            _widget = widget(self._frame)
            _widget.grid(row=0, column=0)

        def add_child(self, widget):
            # Initalize w/ local parent
            _widget = widget(self)
            self.add(_widget, height=150)


    class UI_Frame(ttk.Frame):
        def __init__(self, master):
            super().__init__(master=master)
        
        def add(self, widget):
            # Initalize widget w/ local parent.
            _widget = widget(self)
            # Place via tk.grid()
            # TODO increment row, col, etc
            _widget.grid(row=0, column=0)            


    class UI_Sidebar(UI_Frame):
        def __init__(self, master):
            super().__init__(master=master)
        
        def add(self, widget):
            print("Superclassing w/ UI_Sidebar.")
            return super().add(widget)
        

    class UI_Console(UI_Frame):
        def __init__(self, master):
            super().__init__(master=master)
            self._bg = '#1D2021'
            self._fg = '#83A598'
            self._cursor = '#FABD2F'
            self._font = tk_font.Font(
                family="Consolas", size=10, weight="normal", slant="roman")
            
            self.config_widgets()
            self.config_grid()
        
        def add(self, widget):
            print('Superclassing UI_Frame in Console!')
            return super().add(widget)
        
        def config_widgets(self):
            # Top "MenuBar"
            self._topbar = ttk.Frame(
                self,
                style="Console.TFrame"
            )
            self._minimize = ttk.Button(
                self._topbar,
                style="Console.TButton",
                text="x",
            )
            # Textbox for console outputs.
            self._text = tk.Text(
                self,
                background=self._bg,
                foreground=self._fg,
                font=self._font,
                insertbackground=self._cursor,
                insertwidth=3,
                padx=4,
                pady=3,
                relief='flat',
                wrap='word', 
            )
            # Update the GLobal "ACTIVE_CONSOLE" for write redirects.
            global ACTIVE_CONSOLE
            ACTIVE_CONSOLE = self
        
        def config_grid(self):
            self.rowconfigure(1, weight=1)
            self.columnconfigure(1, weight=1)
            self._topbar.grid(row=0, column=1, sticky='new')
            self._topbar.columnconfigure(0, weight=1)
            self._minimize.grid(row=0, column=0, sticky='nse')

            self._text.grid(row=1, column=1, sticky='nsew')

        def std_console(self, string):
            '''
            Writes output tagged as "Standard" to the console.
            '''
            self._text.insert (tk.END, string)



    class UI_BottomBar(ttk.Frame):
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
            # Root Background color
            self.configure(
                style="BottomBar.TFrame"
            )
            # Left Frame
            self.left_frame = ttk.Frame(
                self,
                style="BottomBar.TFrame"
            )
            self.queue_label = ttk.Label(
                self.left_frame,
                style="BottomBar.TLabel"
            )        
            self.progress_percent = ttk.Label(
                self.left_frame,
                style="BottomBar.TLabel"       
            )
            self.progress_label = ttk.Label(
                self.left_frame,
                style="BottomBar.TLabel"
            )
            # Right/Version Frame
            self.right_frame = ttk.Frame(
                self,
                style="BottomBar.TFrame"
            )
            self.bb_ver = ttk.Label(
                self.right_frame,
                text=VERSION,
                style="BottomBar.TLabel"
            )
            # Seperator
            self.bb_seperator = ttk.Frame(
                self,
                style="BottomBarSep.TFrame"
            )
            self.bb_ver_tt = UI.CustomTk_CreateToolTip(
                self.bb_ver, "pyCrust Version\nWritten by Collin Spears."
            )

        def config_grid(self):
            #self.rowconfigure(0, weight=1)
            self.rowconfigure(1, weight=1)
            self.columnconfigure(0, weight=1)
            # Root Frames 
            self.bb_seperator.grid(
                row=0, column=0, columnspan=2, sticky='new'
            )
            self.left_frame.grid(
                row=1, column=0, sticky="nsw"
            )
            self.right_frame.grid(
                row=1, column=1, sticky='nse'
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
            if len(event.keysym) == 1 or event.keysym in self.CustomTk_autoEntry.tk_umlauts:
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
