# CHANGELOG

## v0.0.4 (2020-11-16)

- No interesting change

## v0.0.3 (2020-05-21)

### New Features

- add fancy_output option (with rich library)

## v0.0.2 (2020-05-06)

### New Features

- add drone support
- add extra_context_func option
- add an option to hide key/values in stdout/stderr
- upgrade structlog
- add an option to avoid to redirect standard python logging
- allow some non standards logging levels
-  feat: replace MODULE* environment variables names by MFMODULE* (MODULE_HOME becomes MFMODULE_HOME and so on)
- better error handling if we can't log
- add a way to silent a noisy logger by its name
- add syslog support
- remove metwork specific modes
- use github actions

### Bug Fixes

- don't use mflog_override paths if the corresponding variable is
- json file was not opened in append mode
- logger names were not logged
- we can now give an exception object to "exception() method"
- isEnabledFor() and getEffectiveLevel() are now working
- null files was created in some directories
- null files in metwork environment (again)
- atomic writing when logging big messages in json
- avoid exception when called with no argument (or None)
- fix some string templating issues in corner cases
- fix latest commit
- close #11
- fix a syslog configuration issue with metwork

## changelog_start (2019-01-21)

- No interesting change


