<a name="unreleased"></a>
## [Unreleased]

### Feat
- add an option to hide key/values in stdout/stderr
- add drone support
- add extra_context_func option

### Fix
- atomic writing when logging big messages in json
- avoid exception when called with no argument (or None)
- don't use mflog_override paths if the corresponding variable is empty
- isEnabledFor() and getEffectiveLevel() are now working
- json file was not opened in append mode
- logger names were not logged
- null files in metwork environment (again)
- null files was created in some directories
- we can now give an exception object to "exception() method"

