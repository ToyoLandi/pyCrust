# pyCrust
 
  'pyCrust' defines various features that can be  enabled/disabled based
  on the goals of the main project. This is meant to shortcut the
  implementation of common features that I wish to include in most python
  Apps and scripts such as...
                                                                         
  - A Featured GUI, with theme support via 'Tkinter'
  - Standard and Debug Logging.
  - Config files (JSON -or- XML) for global user modified params.
  - Directory creation for consistent file-structure of projects.
  - Pre-populated 'README' to get a head-start on documentation.

## A Simple Example.
~~~
import pyCrust

example_config = {
    'version': '0.0',
    'username': 'toyolandi',
    'theme': 'Resetto'
}

applog = pyCrust.Logging()
config = pyCrust.Config(example_config, log_level=1)

print('$', config.get_config())
~~~

