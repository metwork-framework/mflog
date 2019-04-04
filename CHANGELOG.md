<a name="unreleased"></a>
## [Unreleased]

### Feat
- add drone support

### Fix
- atomic writing when logging big messages in json
- don't use mflog_override paths if the corresponding variable is empty
- isEnabledFor() and getEffectiveLevel() are now working
- json file was not opened in append mode
- logger names were not logged
- null files in metwork environment (again)
- null files was created in some directories
- we can now give an exception object to "exception() method"

