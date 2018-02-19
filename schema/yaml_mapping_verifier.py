#!/usr/bin/python3
import os
import sys
import argparse
import yaml
import json
import jsonschema
from jsonschema import validate


def main(json_schema, yaml_mapping):
    """
    Verifies a yaml mapping file against a json schema.
    """
    schema = read_json(json_schema)

    mapping = read_yaml(yaml_mapping)

    try:
        validate(mapping, schema)
        print("file validates okay")
    except jsonschema.exceptions.ValidationError as ve:
        exit(ve)


def read_yaml(yaml_file):
    with open(yaml_file, 'r') as stream:
        try:
            yaml_data = yaml.load(stream)
            return yaml_data
        except yaml.YAMLError as exc:
            sys.exit(exc)


def read_json(json_file):
    with open(json_file, 'r') as stream:
        json_data = json.load(stream)
        return json_data


def is_valid_file(arg):
    if os.path.isfile(arg):
        return arg
    else:
        error = "error: The file %s does not exist" % arg
        sys.exit(error)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verifies a yaml mapping against a RELAX NG schema")

    parser.add_argument('schema',
                        help="jason-schema schema file",
                        metavar="SCHEMA",
                        type=lambda x: is_valid_file(x))
    parser.add_argument('mapping',
                        help="YAML file to be verified",
                        type=lambda x: is_valid_file(x))
    args = parser.parse_args()

    schema = args.schema
    mapping = args.mapping
    main(schema, mapping)
