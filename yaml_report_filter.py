#!/usr/bin/env python
# coding=utf-8


import argparse
import zipfile
import os.path
import time
import sys
import csv
from copy import deepcopy
import yaml
import lxml.etree as et


def cell_column(et_elem, field):
    """
    given field, a string, returns the matching record from the ElementTree
    record et_elem.
    >>> xml_string = '''
    ...     <record>
    ...         <thisfield>value</thisfield>
    ...     </record>'''
    >>> field = "thisfield"
    >>> cell_column(et.fromstring(xml_string), field)
    'value'
    """
    base_path = ".//" + field
    string_path = base_path + "/text()"
    try:
        et_elem.xpath(base_path)
    except et.XPathEvalError:
        error = "invalid expression '%s'" % base_path
        sys.exit(error)
    strng = et_elem.xpath(string_path)

    if len(strng) > 1:
        error = ("error: Getting multiple values, '%s', from the field"
                 "'%s'.\nOnly one value should be returned from the "
                 " input: \n%s" % (strng, field, et.tostring(et_elem)))
        sys.exit(error)
    elif len(strng) == 0:
        return ""
    else:
        output = strng[0]
        return output.encode('utf-8')


def cell_table(table_input, field, glue="", rowend=""):
    """
    given field, a dict, returns the matching values from the ElementTree
    record table_input.

    >>> xml_string = '''
    ...     <record>
    ...         <table>
    ...             <tuple>
    ...                 <thisfield>first</thisfield>
    ...             </tuple>
    ...             <tuple>
    ...                 <thisfield>second</thisfield>
    ...             </tuple>
    ...         </table>
    ...     </record>'''
    >>> field = {
    ...             'tablename': 'table',
    ...             'elements': [
    ...                         {
    ...                             'column': 'thisfield'
    ...                         }
    ...                       ]
    ...         }
    >>> table_xml = et.fromstring(xml_string)
    >>> cell_table(table_xml, field)
    'firstsecond'
    """
    try:
        tablename = field["tablename"]
    except KeyError:
        error = "error: No table name in config for table '%s'" % field
        sys.exit(error)

    table_path = ".//" + tablename
    number_of_tables = len(table_input.xpath(table_path))
    if number_of_tables > 1:
        errorstring = et.tostring(table_input, pretty_print=True)
        error = ("the table name '%s' refers to %s occurrences.\n"
                 "It should only refer to one\n"
                 "This is the data line that caused the error\n\n%s"
                 % (tablename, number_of_tables, errorstring))
        sys.exit(error)

    if 'glue' in field:
        glue = field["glue"]
    if 'rowend' in field:
        rowend = field["rowend"]
    table_rows_path = table_path + "/tuple"
    rows = table_input.xpath(table_rows_path)
    table_string = ""
    row_array = []
    for table_row in rows:
        field_array = []
        row_string = ""
        try:
            for row_field in field["elements"]:
                f = process_field(table_row, row_field, glue, rowend)
                field_array.append(f)
        except KeyError:
            error = ("error: no elements recorded in config"
                     " for table %s " % tablename)
            sys.exit(error)
        if field_array:
            if not all('' == s or s is None for s in field_array):
                row_string = glue.join(field_array)
        else:
            pass
        row_array.append(row_string)
    tidied_array = filter(None, row_array)
    table_string = rowend.join(tidied_array)
    return table_string


def cell_conditional(conditional_input, field, glue="", rowend=""):
    """
    >>> xml_string = '''
    ...     <record>
    ...         <top>high</top>
    ...         <bottom>low</bottom>
    ...     </record>'''
    >>> field = {
    ...          'condition': '/text()',
    ...          'target': 'top',
    ...          'elements': [
    ...                     {
    ...                        'string': 'condition met'
    ...                     }
    ...                    ]
    ...         }
    >>> cell_conditional(et.fromstring(xml_string), field)
    'condition met'
    >>> field = {
    ...          'condition': '/text() = low',
    ...          'target': 'top',
    ...          'elements': [
    ...                     {
    ...                        'string': 'condition met'
    ...                     }
    ...                    ],
    ...          'otherwise': {
    ...                      'elements': [
    ...                                 {
    ...                             'string': 'condition not met'
    ...                                 }
    ...                                ]
    ...                        }
    ...            }
    >>> cell_conditional(et.fromstring(xml_string), field)
    'condition not met'
    """

    otherwise = ""
    try:
        condition = field["condition"]
    except KeyError:
        error = ("error: conditional field '%s' must have condition specified."
                 % field)
    elements_for_condition = field["elements"]
    if 'glue' in field:
        glue = field["glue"]
    if 'otherwise' in field:
        otherwise = field["otherwise"]
    if condition is None:
        condition = ""
    condition_string = ""
    try:
        target = field["target"]
    except KeyError:
        error = "error: Condition '%s' must have a target field" % condition
        sys.exit(error)
    condition_xpath = ".//" + target + condition

    try:
        condition_test = conditional_input.xpath(condition_xpath)
    except et.XPathEvalError as e:
        error = "XPathEvalError: '%s' '%s'" % (e, condition_xpath)
        sys.exit(error)

    if not condition_test:
        if not otherwise:
            return
        else:
            elements_for_condition = otherwise["elements"]

    try:
        condition_string = cell_string(
            conditional_input, elements_for_condition, glue, rowend)
    except:
        error = ("Failed to process conditional input: %s"
                 % elements_for_condition)
        sys.exit(error)

    return condition_string


def cell_range(input_data, field, glue, rowend):
    """returns a string of the range between higher and lower
    input_data: ElementTree record
    field: dict {'lower': 'lower value', 'higher': 'higher value'}
    glue: string
    rowend: string
    >>> field = {
    ...         'higher': 'top',
    ...          'lower': 'bottom'
    ...         }
    >>> xml_string = '''
    ...     <record>
    ...         <top>high</top>
    ...         <bottom>low</bottom>
    ...     </record>'''
    >>> cell_range(et.fromstring(xml_string),
    ...                          field,
    ...                          "glue",
    ...                          "rowend")
    'lowgluehigh'
    >>> xml_string = '''
    ...     <record>
    ...         <top>only high</top>
    ...     </record>'''
    >>> cell_range(et.fromstring(xml_string),
    ...                          field,
    ...                          "glue",
    ...                          "rowend")
    'only high'
    """
    if 'lower' not in field or 'higher' not in field:
        error = ("error: range field %s must have both "
                 "a 'higher' and a 'lower' field" % field)
        sys.exit(error)

    low = field["lower"]
    high = field["higher"]

    lower = cell_column(input_data, low)
    higher = cell_column(input_data, high)
    if glue == '':
        if 'glue' in field:
            glue = field["glue"]
        else:
            glue = " - "
    if not lower and not higher:
        return
    elif not higher:
        return lower
    elif not lower or lower == higher:
        return higher
    else:
        return "%s%s%s" % (lower, glue, higher)


def cell_multiple(input_data, field, glue):
    """returns all nodes 'column' concatenated with glue
    >>> xml_string = '''
    ...     <multiple>
    ...         <thisfield>one</thisfield>
    ...         <thisfield>two</thisfield>
    ...     </multiple>'''
    >>> field = "thisfield"
    >>> glue = "X"
    >>> cell_multiple(et.fromstring(xml_string),
    ...                             field,
    ...                             glue)
    'oneXtwo'
    >>> xml_string = '''
    ...     <multiple>
    ...         <thisfield>one</thisfield>
    ...         <nested>
    ...             <thisfield>nested two</thisfield>
    ...         </nested>
    ...     </multiple>'''
    >>> cell_multiple(et.fromstring(xml_string),
    ...                             field,
    ...                             glue)
    'oneXnested two'
    """
    try:
        path = field
    except KeyError:
        error = ("error: multiple field %s does not"
                 " have a field specified" % field)
        sys.exit(error)
    if 'glue' in field:
        glue = field["glue"]

    field_path = ".//" + path + "/text()"
    elements = input_data.xpath(field_path)
    ms = glue.join(elements)
    return ms.encode("utf-8")


def cell_xpath(et_elem, query):
    """
    given field, a string containing an xpath epxression,
        returns the matching record from the ElementTree
    element et_elem.
    >>> xml_string = '''
    ...     <record>
    ...         <thisfield>value</thisfield>
    ...     </record>'''
    >>> query = "thisfield/text()"
    >>> cell_xpath(et.fromstring(xml_string), query)
    'value'
    """
    query_path = query
    try:
        result = et_elem.xpath(query_path)
    except et.XPathEvalError:
        error = "invalid expression '%s'" % query_path
        sys.exit(error)
    return str(result)


def process_field(input_data, field, glue, rowend):
    """given input_data, the xml for this record,
        returns a string as specified in config for field
    """
    try:
        k = field.keys()[0]
    except AttributeError:
        error = "in data %s there were no keys in field %s" % (
            input_data, field)
        sys.exit(error)
    v = field.values()[0]

    if k == "conditional":
        return cell_conditional(input_data, v, glue, rowend)
    elif k == "string":
        return v
    elif k == "column":
        return cell_column(input_data, v)
    elif k == "multiple":
        return cell_multiple(input_data, v, glue)
    elif k == "range":
        return cell_range(input_data, v, glue, rowend)
    elif k == "table":
        return cell_table(input_data, v, glue, rowend)
        # c_field(input_data, a)
    elif k == "first":
        first_of = []
        for i in v:
            c = cell_column(input_data, i)
            first_of.append(c)
        return next((s for s in first_of if s), '')
    elif k == "xpath":
        return cell_xpath(input_data, v)


def cell_string(input_data, config_elements, glue, rowend):
    """
    Return a string to go into this cell of the results
    input_data =  ElementTree record
    config_elements = a list of dicts
    """
    fs = ""
    cell_string_array = []
    for i, field in enumerate(config_elements):
        this_field = process_field(input_data, field, glue, rowend)
        if this_field:
            cell_string_array.append(this_field)
    if not cell_string_array:
        fs = ""
    else:
        fs = glue.join(cell_string_array)
    return fs


def simplify_emu_xml(et_element):
    """given an etree element, returns an etree element.

    For each node of the input the name is changed to the attribute 'name'.
    If there is no 'name' attribute the node is left unaltered.

    >>> xml_string = '''
    ...     <table name='tissues'>
    ...         <tuple>
    ...             <atom name='tissuetype'>Liver</atom>
    ...         </tuple>
    ...     </table>'''
    >>> wanted = '''
    ...     <tissues>
    ...         <tuple>
    ...             <tissuetype>Liver</tissuetype>
    ...         </tuple>
    ...     </tissues>'''
    >>> xml = et.fromstring(xml_string)
    >>> wanted_xml = et.fromstring(wanted)
    >>> simple_xml = simplify_emu_xml(xml)
    >>> et.tostring(simple_xml) == et.tostring(wanted_xml)
    True

    """
    for elem in et_element.iter():
        xsl_transform = et.XML("""\
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs"
    version="1.0">
    <xsl:output method="xml"/>

    <xsl:template match="*[@name]">
        <xsl:element name="{@name}">
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>

    <xsl:template match="node() | @*">
       <xsl:copy>
           <xsl:apply-templates select="node() | @*"/>
       </xsl:copy>
    </xsl:template>

</xsl:stylesheet>
        """)
        transform = et.XSLT(xsl_transform)
        simplified_xml = transform(et_element)
    return simplified_xml


def read_emu_xml(emu_xml, config):
    """Returns a list of list of dicts

    Iterates through the input EMu XML file and
    + creates an ElementTree record with simplified xml for each record
        - <atom name='irn'>123</atom> -> <irn>123</irn>
    + Transforms each record into a list of dicts.
    + Adds the individual record list of dicts to the general results list

    emu_xml: the emu XML file
    config: the config yaml file
    """
    context = et.iterparse(emu_xml, events=('start', 'end'), encoding='utf-8')

    nesting = 0
    # nesting variable is used to track the depth in the XML tree
    # each EMu record is a tuple at nesting depth 1
    # everything below *that* is a part of that record

    output_list = []

    for event, elem in context:
        if event == 'start':
            if elem.tag != 'atom':
                # The tree only gets deeper at table and tuple nodes
                nesting += 1

        if event == 'end':
            if elem.tag != 'atom':
                nesting -= 1
                if nesting == 1 and elem.tag == 'tuple':
                    # end of this record has been reached
                    # so transform the entire record
                    simplified = simplify_emu_xml(elem)
                    line = create_line_record(simplified, config)
                    for l in line:
                        output_list.append(l)

    return output_list


def read_yaml(yaml_file):
    """Opens a yaml file and returns it as parsed yaml data
    """
    with open(yaml_file, 'r') as stream:
        try:
            yaml_data = yaml.load(stream)
            return yaml_data
        except yaml.YAMLError as exc:
            sys.exit(exc)


def line_as_dicts(line, config):
    """
    Given a simplified EMu XML ElementTree record
        returns a list of lists of dicts

    If there is no duplication specified the list will only have a single entry
    line = ElementTree record
    config = config data from YAML

    """
    columns = config['columns']
    headers = []
    for column in columns:
        headers.append(column['header'])
    line_as_dicts = {}
    # for each dict in the data return a result dict
    for column in columns:
        if 'glue' in column:
            glue = column['glue']
        else:
            glue = ""
        if 'rowend' in column:
            rowend = column['rowend']
        else:
            rowend = ""
        header = column['header']
        elements = column['elements']
        cell = cell_string(line, elements, glue, rowend)
        line_as_dicts[header] = cell
    unidict = {k.decode('utf8'): v.decode('utf8')
               for k, v in line_as_dicts.items()}
    return unidict


def create_line_record(line, config):
    """
    line: an ElementTree record of the simplified emu xml for this line
    config: the yaml config for this report
    check and do duplication if required

    send each individual line to be turned into a list of dicts
    """
    line_dict = []
    if 'duplicate' in config:
        # duplication can done for each record based on a specified table
        # duplication is used at SAM for sending tissue records to the
        # ALA - a record with multiple tissues recorded gets duplicated
        # with reference to the Tissue table the required number of times
        # and a suffix added for each tissue.
        duplicate = config['duplicate']
        if duplicate is None:
            error = "error: a target field must be specified for duplication"
            sys.exit(error)
        try:
            target = duplicate['targettable']
        except KeyError:
            error = ("error: a target table must be specified for"
                     "duplication. Duplication happens for each row"
                     " of the table")
            sys.exit(error)

        remove_xpath = './/' + target
        target_xpath = './/' + target + '/tuple'
        try:
            ind = duplicate['indicator']
        except KeyError:
            error = 'error: an indicator must be specified for duplication.'
            sys.exit(error)
        if len(line.xpath(target_xpath)) > 1:
            for i, n in enumerate(line.xpath(target_xpath)):
                # add the indicator elements as nodes
                working_line = deepcopy(line)
                root = working_line.getroot()
                indicator = et.SubElement(root, ind)
                indicator.text = str(i + 1)
                for r in working_line.xpath(remove_xpath):
                    r.getparent().remove(r)
                table_insert = et.SubElement(root, target)
                table_insert.append(n)
                unidict = []
                unidict = line_as_dicts(working_line, config)
                line_dict.append(unidict)
        else:
            unidict = []
            unidict = line_as_dicts(line, config)
            line_dict.append(unidict)

    else:
        unidict = []
        unidict = line_as_dicts(line, config)
        line_dict.append(unidict)

    return line_dict


def is_valid_file(arg):
    """Confirm that a particular file is a valid extant file
    """
    if os.path.isfile(arg):
        return arg
    else:
        error = "error: The file %s does not exist" % arg
        sys.exit(error)


def make_csv(data, headers, out_file):
    """Generate a csv file
    """
    csv_filename = out_file + ".csv"

    with open(csv_filename, 'wb') as csvfile:
        # BOM (needed by Excel to open UTF-8 file properly)
        csvfile.write(u'\ufeff'.encode('utf8'))
        fieldnames = headers
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for row in data:
            writer.writerow({k: v.encode('utf8') for k, v in row.items()})
            # writer.writerow(row)

    return csv_filename


def make_excel(data, headers, out_file):
    """Generate an Excel file
    """
    from xlsxwriter import Workbook

    filename = out_file + ".xlsx"

    wb = Workbook(filename)
    ws = wb.add_worksheet("Sheet1")
    number_of_columns = len(headers)
    ws.set_column(0, number_of_columns, 15)

    header_row = 0
    for header in headers:
        col = headers.index(header)
        ws.write(header_row, col, header)

    row = header_row + 1
    for line in data:
        for _key, _value in line.items():
            col = headers.index(_key)
            ws.write(row, col, _value)
        row += 1  # enter the next row
    wb.close()

    return filename


def main(emu_file, config_file, output_format, compress=False, silent=True):
    """
    emu_file: the default EMu XML output from EMu exports or report
    config_file: the yaml config file
    output_format: excel, csv, dicts, none
        dicts returns the data as dicts
        for using this data in another report/export filter
    compress: boolean, whether the output file should be
        compressed into a zip file
    silent: boolean, whether the filename should be printed to
        stdout at the end (required by EMu exports)
    """

    config = read_yaml(config_file)
    output_data = read_emu_xml(emu_file, config)

    headers = []
    columns = config['columns']
    for a in columns:
        headers.append(a['header'])

    report_title = config['title']
    dt = time.strftime(" %y%m%d%H%M")
    output_file = report_title + dt

    if output_format == "excel":
        filename = make_excel(output_data, headers, output_file)
    elif output_format == "csv":
        filename = make_csv(output_data, headers, output_file)
    elif output_format == "dicts":
        if 'totalstring' in config:
            totalstring = config['totalstring']
        else:
            totalstring = ""
        return output_data, output_file, headers, report_title, totalstring
        filename = ""
    elif output_format == "none":
        filename = ""
        pass
    if compress is True:
        compressed_filename = report_title + '.zip'
        with zipfile.ZipFile(
                compressed_filename, 'w', zipfile.ZIP_DEFLATED) as myzip:
            myzip.write(filename)
        os.remove(filename)
        filename = compressed_filename
    if silent is False:
        print(filename)
    return filename


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=("Given an EMu export XML file and a yaml mapping file"
                     " generates the specified output format"))
    parser.add_argument('filename',
                        help="EMu XML format File to be converted",
                        type=lambda x: is_valid_file(x))
    parser.add_argument('--configfile', '-c', required=True,
                        help="YAML config file",
                        metavar="FILE",
                        type=lambda x: is_valid_file(x))
    parser.add_argument('--output', '-o',
                        required=False,
                        choices=['csv', 'excel', 'pdf',
                                 'dicts', 'none'],
                        default="none",
                        help=("The format for the output. Valid"
                              " choices are csv, excel, dicts (return output"
                              " data as dicts for further processing) and"
                              " none"))
    parser.add_argument('--compress',
                        action='store_true',
                        default=False,
                        help="compress the result into a zip file")
    parser.add_argument('--silent',
                        action='store_true',
                        default=False,
                        help=("Supress the printing of the name "
                              "of any output files at completion"))
    args = parser.parse_args()

    emu_export_xml = args.filename
    config_yaml = args.configfile
    format_for_output = args.output
    zip_output = args.compress
    supress_filename = args.silent
    filename = main(emu_export_xml,
                    config_yaml,
                    format_for_output,
                    zip_output,
                    supress_filename)
