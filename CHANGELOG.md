# CHANGELOG


## [Unreleased]

### New Features
- feat: replace MODULE* environment variables names by MFMODULE* (MODULE_HOME becomes MFMODULE_HOME and so on)
- allow some non standards logging levels
- add an option to avoid to redirect standard python logging
- upgrade structlog
- add an option to hide key/values in stdout/stderr
- add extra_context_func option
- add drone support


### Bug Fixes
- close #11
- fix latest commit
- fix some string templating issues in corner cases
- avoid exception when called with no argument (or None)
- atomic writing when logging big messages in json
- null files in metwork environment (again)
- null files was created in some directories
- isEnabledFor() and getEffectiveLevel() are now working
- we can now give an exception object to "exception() method"
- logger names were not logged
- json file was not opened in append mode
- don't use mflog_override paths if the corresponding variable is





