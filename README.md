# EMu reports YAML

This is a python filter/script to allow you to write csv and Excel reports
for Axiell EMu Museum Collections Management database using YAML
configuration files.

At heart the filter is applying XSLT transforms to the export data but
abstracts away the complexities of XSLT making it easier
to write the report configuration.

*If* you are comfortable working on the command line and with text files you may 
find this a more convenient method of creating reports. Familiarity with XSLT
will also be helpful but is not essential.

You will need ssh access to your EMu server - if your IT team don't
permit that you won't be able to use this filter.

Currently the filter will output csv or excel files (or, for re-using
in a separate report, python dicts). The columns in the csv or excel
files can include any field that can be referenced from the module you
are reporting on. You can also report on tables and nested tables and
include conditions under which particular fields should be reported.

The reports in samareports are the ones we use here in the South Australian 
Museum and may be useful as examples.


