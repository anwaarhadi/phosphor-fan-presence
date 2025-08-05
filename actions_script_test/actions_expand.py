#!/usr/bin/env python3

"""
Usage:

python3 actions_expand.py -f <path_to_events_input_template> -o <path_for_output_expanded_events_file

or

./actions_expand.py -f <path_to_events_input_template> -o <path_for_output_expanded_events_file
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
Expand a group into one or more groups based on expand variables

group_json - list of JSON objects representing groups from a particular event
param_name - Name of the parameter to replace
param_val - Value of parameter to replace with
"""
def expand_groups(group_json, expand_params, event_num):
    full_group_json = []
    for group in group_json:
        # group must have name, interface, and property
        for req_param in ["name", "interface", "property"]:
            if req_param not in group.keys():
                raise Exception(f"{req_param} is a required parameter for groups")
        
        # Copy over group and check expand flag. If true, replace variables for required fields, else just keep copied group
        true_group = {key: value for key, value in group.items() if key != "expand"}
        if group.get("expand", False):
            for param in expand_params:
                true_group["name"] = true_group["name"].replace("$"+param["name"], param["values"][event_num])
        full_group_json.append(true_group)
    
    return full_group_json


"""
Expand an action template into one or more actions based on expand variables

action_json - list of JSON objects representing actios from a particular event
param_name - Name of the parameter to replace
param_val - Value of parameter to replace with
"""
def expand_actions(action_json, expand_params, event_num):
    full_action_json = []
    for action in action_json:
        # action must have name
        if "name" not in action.keys():
            raise Exception("'name' is a required parameter for actions")
        
        # Copy over group and check expand flag.  If true, replace variables
        true_action = {key: value for key, value in action.items() if key != "expand"}
        if action.get("expand", False):
            for param in expand_params:
                for key, value in true_action.items():
                    if key in ["name", "parameter_name", "state_parameter_name"]:
                        true_action[key] = value.replace("$"+param["name"], param["values"][event_num])
                    if key == "zones":
                        true_action[key] = [zone.replace("$"+param["name"], param["values"][event_num]) for zone in value]
                    if key == "groups":
                        # print(param)
                        true_action[key] = expand_groups(value, expand_params, event_num)
        full_action_json.append(true_action)
    
    return full_action_json

"""
Expand a full JSON file

filename - name of JSON file template to expand
"""
def expand_full_json(filename):
    json_template = get_sanitized_json(filename)
    full_json = []
    for event in json_template:
        # event must have name, groups, triggers, and actions
        for req_param in ["name", "groups", "triggers"]:
            if req_param not in event.keys():
                raise Exception(f"'{req_param}' is a required parameter for events")
        
        # Check that there is an expand list. If not, or expand list is empty, copy over event
        expand_params = event.get("expand", [])
        if len(expand_params) == 0:
            full_json.append({key: value for key, value in event.items() if key != "expand"})
            continue

        # Check that all parameters in the expand list have the same length
        num_vals = len(expand_params[0].get("values", []))
        if num_vals == 0:
            raise Exception("Parameters must have at least one value")
        for param in expand_params:
            if len(param.get("values", [])) != num_vals:
                raise Exception("All parameters must have the same number of values.")
        
        # Copy template for however many events are needed then replace fields with parameter values
        expanded_event = [{key: value for key, value in event.items() if key != "expand"} for _ in range(num_vals)]
        for event_num in range(num_vals):
            for param in expand_params:
                expanded_event[event_num]["name"] = expanded_event[event_num]["name"].replace("$"+param["name"], param["values"][event_num])
            expanded_event[event_num]["groups"] = expand_groups(expanded_event[event_num]["groups"], expand_params, event_num)
            if "actions" in expanded_event[event_num].keys():
                expanded_event[event_num]["actions"] = expand_actions(expanded_event[event_num]["actions"], expand_params, event_num)
        
        # Concatenate expanded events to full JSON list
        full_json += expanded_event
    
    return full_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Expand an events.json template into a larger file pased on specified parameters"
    )
    parser.add_argument(
        "-f",
        "--file",
        dest="event_file",
        help="events.json file to expand"
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="expanded_output",
        help="Expanded output file"
    )
    args = parser.parse_args()
    if not args.event_file:
        sys.exit("Missing event template for expansion")
    try:
        full_json = expand_full_json(args.event_file)
        with open(args.expanded_output, "w") as f:
            json.dump(full_json, f, indent=4)
    except Exception as e:
        print(f"An error has occurred: {e}")