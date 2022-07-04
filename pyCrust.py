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
import sys
import json
import logging

VERSION = '0.0'
ROOTPATH = os.getcwd()

class _write:
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
            print('pyCrust-> ' + self.string)
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
        _write(
            string=('Checking for an exisisting config.' + self.extension 
                + ' file.'),
            log_level=self.log_level,
            ui=self.init_ui,
            redirect=self.redirect,
        )
        alive = os.access(self._confpath, os.W_OK)
        if alive and self.extension == 'JSON':
            _write(
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
            _write(
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
                _write(
                    string='Successfully loaded the config file.',
                    log_level=self.log_level,
                    ui=self.init_ui,
                    redirect=self.redirect,
                )
                return self._config
        elif self.extension == 'XML':
            print(" Jun 24, TODO!")
        else: # When the config file is missing
            _write(
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


class UI:
    '''
    Enables a user-readable config file for quick editing of global params.
    '''
    def __init__(self):
        _write("You should do this Collin...")

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
        db_path = ROOTPATH + "\\db\\basecamp.db"
        # Try to open exisiting 'datastore.json'
        if os.access(db_path, os.R_OK):
            print("SQLite3 started successfully! - Connected to DB.")
        else:
            print("Not Found. Generating new 'basecamp.db' file...")
            # Creating .db file
            file = open(db_path, "w+")
            file.close()
            print("Successfully created basecamp.db file")

        # Connecting to sqlite DB
        self.db_connection = sqlite3.connect(db_path)
        # Create default tables
        self.dbshell = self.db_connection.cursor()
        # Close connection - Jobs Done!
        self.db_connection.commit()
        self.dbshell.close()

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
            





# Custom Error Exception codes for pyCrust
class UnexpectedInitVar(Exception):
    '''
    Raised when there is an "__init__" value for a class that is not in the
    expected values list in "pyCrust.*.check_initvars()"
    '''
    pass #Do nothing and let the dev handle this error.
