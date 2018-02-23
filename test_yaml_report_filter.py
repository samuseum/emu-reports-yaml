import pytest
import lxml.etree as et
from yaml_report_filter import cell_column
from yaml_report_filter import cell_table

test_columns_xml_string ='''
<record>
    <first_column>value one</first_column>
    <second_column>value two</second_column>
</record>
'''

columns_et = et.fromstring(test_columns_xml_string)


def test_nothing():
    assert 1 == 1

def test_cell_column1():
    # string from column
    et_elem = columns_et
    field_that_works = "first_column"
    assert cell_column(et_elem, field_that_works) == "value one"

def test_cell_column2():
    # column in config not in data
    et_elem = columns_et
    absent_field = "missing_column"
    assert cell_column(et_elem, absent_field) == ""

test_tables_xml_string = '''
<record>
    <a_table>
        <tuple>
            <cell_one>r1 c1</cell_one>
        </tuple>
        <tuple>
            <cell_one>r2 c1</cell_one>
        </tuple>
        <tuple>
            <cell_one>r3 c1</cell_one>
        </tuple>
    </a_table>
    <another_table>
        <tuple>
            <cell_one>r1 c1</cell_one>
            <cell_two>r1 c2</cell_two>
        </tuple>
        <tuple>
            <cell_one>r2 c1</cell_one>
            <cell_two>r2 c2</cell_two>
        </tuple>
    </another_table>
</record>
'''

tables_et = et.fromstring(test_tables_xml_string)

def test_cell_table1():
    # single cell from each row
    et_elem = tables_et
    field_dict = {
        'tablename': 'a_table',
            'elements': [
                {
                'column': 'cell_one'
                }
            ]
    }
    assert cell_table(et_elem, field_dict) == "r1 c1r2 c1r3 c1"

def test_cell_table2():
    # single cell from each row,
    # with rowend specified in function call
    et_elem = tables_et
    field_dict = {
        'tablename': 'a_table',
            'elements': [
                {
                'column': 'cell_one',
                }
            ]
    }
    assert cell_table(et_elem, field_dict, rowend = " rowend_argument ") == "r1 c1 rowend_argument r2 c1 rowend_argument r3 c1"

def test_cell_table3():
    # single cell from each row,
    # with rowend specified in field_dict (config)
    # config rowend overrides rowend in function call
    et_elem = tables_et
    field_dict = {
        'tablename': 'a_table',
        'rowend': ' rowend_dict ',
            'elements': [
                {
                'column': 'cell_one',
                }
            ]
    }
    assert cell_table(et_elem, field_dict, " glue_dummy ", " rowend dummy ") == "r1 c1 rowend_dict r2 c1 rowend_dict r3 c1"

def test_cell_table4():
    # glue and rowend specified in config
    et_elem = tables_et
    field_dict = {
        'tablename': 'another_table',
        'glue': ' glue ',
        'rowend': ' rowend ',
            'elements': [
                {
                'column': 'cell_one'
                },
                {
                'column': 'cell_two'
                }
            ]
    }
    assert cell_table(et_elem, field_dict) == "r1 c1 glue r1 c2 rowend r2 c1 glue r2 c2"

def test_cell_table5():
    # glue and rowend specified in function call
    et_elem = tables_et
    field_dict = {
        'tablename': 'another_table',
            'elements': [
                {
                'column': 'cell_one'
                },
                {
                'column': 'cell_two'
                }
            ]
    }
    assert cell_table(et_elem, field_dict, " glue ", " rowend ") == "r1 c1 glue r1 c2 rowend r2 c1 glue r2 c2"

def test_cell_table6():
    # glue and rowend specified in config and function call
    # config overrides function call
    et_elem = tables_et
    field_dict = {
        'tablename': 'another_table',
        'glue': ' glue ',
        'rowend': ' rowend ',
            'elements': [
                {
                'column': 'cell_one'
                },
                {
                'column': 'cell_two'
                }
            ]
    }
    assert cell_table(et_elem, field_dict, " dummy glue ", " dummy rowend ") == "r1 c1 glue r1 c2 rowend r2 c1 glue r2 c2"

def test_cell_table1():
    # column in config not in data
    et_elem = tables_et
    field_dict = {
        'tablename': 'a_table',
            'elements': [
                {
                'column': 'absent_column'
                }
            ]
    }
    assert cell_table(et_elem, field_dict) == ""
