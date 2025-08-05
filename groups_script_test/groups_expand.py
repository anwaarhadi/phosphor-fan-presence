#!/usr/bin/env python3

"""
Usage:

python3 groups_expand.py -f <path_to_events_input_template> -o <path_for_output_expanded_events_file

or

./groups_expand.py -f <path_to_events_input_template> -o <path_for_output_expanded_events_file
"""

import argparse
import re
import sys
import json


"""
Parse in a JSON file into a Python dictionary list

filename - Path to the JSON file to parse in
"""
def get_sanitized_json(filename):
    lines = []
    out = []
    with open(filename, "r") as file:
        lines = file.readlines()

    for line in lines:
        # remove comment lines
        match = re.search(r"\s*\/\/", line)
        if match is None:
            out.append(line)

    return json.loads("".join(out))


"""
Expand a full JSON file

filename - name of JSON file template to expand
"""
def expand_full_json(filename):
    json_template = get_sanitized_json(filename)
    full_json = []
    for group in json_template:
        # Groups must have name and members parameters filled out
        if "name" not in group.keys() or "members" not in group.keys():
            raise Exception("'name' and 'members' are required fields")
        
        # check if there is an expand list, if not or expand list is empty, copy over group
        expand_params = group.get("expand", [])
        if len(expand_params) == 0:
            full_json.append({key: value for key, value in group.items() if key != "expand"})
            continue

        # check that all parameters in the expand list have the same length for the values field
        num_vals = len(expand_params[0].get("values", []))
        if num_vals == 0:
            raise Exception("Parameters must have at least one value")
        for param in expand_params:
            if len(param.get("values", [])) != num_vals:
                raise Exception("All parameters must have the same number of values.")
        
        # copy template for however many groups are needed then replace the name and members field with parameters
        expanded_group = [{key: value for key, value in group.items() if key != "expand"} for _ in range(num_vals)]
        for group_num in range(num_vals):
            for param in expand_params:
                expanded_group[group_num]["name"] = expanded_group[group_num]["name"].replace("$"+param["name"], param["values"][group_num])
                expanded_group[group_num]["members"] = [member.replace("$"+param["name"], param["values"][group_num]) for member in expanded_group[group_num]["members"]]
        
        # concatenate the expanded group items to the full JSON list
        full_json += expanded_group
    return full_json
        

            


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Expand a groups.json template into a larger file pased on specified parameters"
    )
    parser.add_argument(
        "-f",
        "--file",
        dest="groups_file",
        help="groups.json file to expand"
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="expanded_output",
        help="Expanded output file"
    )
    args = parser.parse_args()
    if not args.groups_file:
        sys.exit("Missing group template for expansion")
    try:
        full_json = expand_full_json(args.groups_file)
        with open(args.expanded_output, "w") as f:
            json.dump(full_json, f, indent=4)
    except Exception as e:
        print(f"An error has occured: {e}")