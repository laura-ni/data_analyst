# coding: utf-8

# OpenStreetMap Case Study Python Codes
import csv
import codecs
import pandas as pd
import pprint
import re
import requests
import xml.etree.cElementTree as ET
import cerberus
import schema # note: refers to the schema.py file attached in this directory
import os

### Set my working directory and get the xml file from Open Street Map website
# HOME = os.path.expanduser('~')
# PATH= os.path.join(HOME,'repos/data_analyst_old/Case_Study_and_Project_Helper')
# os.chdir(PATH)
# # finish the rest of this yourself
# print(os.getcwd())

#Download data from the Openstreet Map Web site
SAMPLE_URL = "http://overpass-api.de/api/map?bbox=-74.0133,40.7245,-73.9574,40.7734"

# note: change this to your real datafile if you're using this code for your project
OSM_PATH = "NYMap.xml"
#OSM_PATH = 'example.xml'

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
# LOWER_COLON = re.compile(r'^([a-z]|_):+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

def get_XML_data(URL, FILENAME):

    # make the request but have it stream instead of reading all data into memory at once
    r = requests.get(URL, stream=True)

    try:
        # print the URL to debug in event that error gets thrown
        print("Request URL:",r.url)

        # Throw an error for bad status codes
        r.raise_for_status()

        # use iter_lines to parse each line one by one
        events = r.iter_lines()

        # write each line, line by line, into a writable file
        with open (FILENAME, 'w') as f:
            for line in events:
                f.write(line.decode('utf-8'))
                f.write("\n") # this is necessary to maintain the formatting in the file

        # success messages
        print("File write was success!")
        print("If this was a sample test set, open the file to make sure data looks complete")

    except Exception as e:
        print (e)

    finally:
        r.close()

#Functions for shape element in the xml file

def load_secondary_tags(tag_elem, id_value, default_tag_type='regular'):
    if PROBLEMCHARS.search(tag_elem.attrib["k"]):
        return None
    elif LOWER_COLON.search(tag_elem.attrib["k"]):
            k_list = tag_elem.attrib["k"].split(":",1)
            type_ = k_list[0]
            key = k_list[1]
    else:
        key = tag_elem.attrib["k"]
        type_ = default_tag_type

    return {
        "id": id_value,
        'key': key,
        "value": tag_elem.attrib["v"],
        'type': type_
        }

def load_node_tag(node_element):
    node_attribs = {}
    for item in NODE_FIELDS:
        node_attribs[item] = node_element.attrib[item]

    # Find node_tags
    list_child_tag = node_element.findall("tag")
    node_tags = []
    if list_child_tag and list_child_tag != None:
        for tag_elem in list_child_tag:
            dic_tag = load_secondary_tags(tag_elem = tag_elem, id_value = node_element.attrib["id"])
            if dic_tag:
                node_tags.append(dic_tag)

    return {
            'node': node_attribs,
            'node_tags': node_tags
             }

def load_way_tag(way_element):
    way_attribs = {}
    for item in WAY_FIELDS:
        way_attribs[item] = way_element.attrib[item]


    # Find way_nodes
    count = 0
    way_nodes = []
    for node_elem in way_element.iter(tag = "nd"):
        dic_way_node = {}
        dic_way_node["id"] = way_element.attrib["id"]
        dic_way_node["node_id"] = node_elem.attrib["ref"]
        dic_way_node["position"] = count
        way_nodes.append(dic_way_node)
        count += 1

    # Find way_tags
    list_way_tag = way_element.findall("tag")
    way_tags = []
    if list_way_tag:
        for tag_elem in list_way_tag:
            dic_tag = load_secondary_tags(tag_elem = tag_elem, id_value = way_element.attrib["id"])
            if dic_tag:
                way_tags.append(dic_tag)

    return  {
            'way': way_attribs,
            'way_nodes': way_nodes,
            'way_tags': way_tags
        }

def shape_element(element):

    #Load node element
    if element.tag == 'node':
        return load_node_tag(element)

    #Load way element
    elif element.tag == 'way':
        return load_way_tag(element)


### Codes for reading the xml file into csv files

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.items())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)

        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    # note: this was unnecessary and done strictly for python 2 since it doesn't automatically read unicode
    # commented out writerow since it's overriding an existing method which should work fine in python 3
    # if using windows and data doesn't write as unicode, you can find a way on your own or use original
    # python 2 code
    """Extend csv.DictWriter to handle Unicode input"""

    """ def writerow(self, row):
        # change .iteritems() method to .items() (python 3 uses .items()) and figure out how to enforce unicode
        # note: the following is dictionary comprehension, similar to list comprehension but for dicts
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })
    """
    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
        codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
        codecs.open(WAYS_PATH, 'w') as ways_file, \
        codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
        codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()


        #added this
        count = 0
        node_count = 0
        node_tag_count = 0
        way_count = 0
        way_node_count = 0
        way_tag_count = 0
        for element in get_element(file_in, tags=('node', 'way')):

            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    node_count += 1
                    node_tag_count += len(el['node_tags'])

                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    way_count += 1
                    way_node_count += len(el['way_nodes'])
                    way_tag_count += len(el['way_tags'])

                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
        print("node: ", node_count)
        print("node_tag: ", node_tag_count)
        print("way: ", way_count)
        print("way_node: ", way_node_count)
        print("way_tag: ", way_tag_count)



if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    get_XML_data(SAMPLE_URL, OSM_PATH)
    process_map(OSM_PATH, validate=True)

    # ### Codes for Clean the street names in the ways_tags.csv
    #
    # I will not touch the original xml here. Because, it takes time to turn the xml fime into csv. If the file is bigger, it will take more time. It's an timely expensive calculation. I will use the csv files to do the next cleaning step. So, I use pandas to read the file into a data frame. Then, I investigate the street names to see if there are any problems.

    df_ways_tags = pd.read_csv('ways_tags.csv')


    #Check the street name type
    short_street_name = set()
    for index, row in df_ways_tags.iterrows():
        if row['key'] == 'street':
            street_value = row['value']
            street_type = street_value.split(' ')[-1]
            short_street_name.add(street_type)

    print(short_street_name)



    # The code above helped me to find the unique street name type. There were some weird street types which caught my eyes. I wrote the code below to check what exactly these streets were.

    weird_street_name = ['D','Americas','633','Bowery','A', 'St', 'B', 'C']
    street_name = set()
    for index, row in df_ways_tags.iterrows():
        if row['key'] == 'street' and  row['value'].split(' ')[-1] in weird_street_name:
            street_name.add(row['value'])
    print(street_name)

    for index, row in df_ways_tags.iterrows():
        if row['key'] == 'street' and  row['value'] == '633':
            print(row)


    for index, row in df_ways_tags.iterrows():
        if row['key'] == 'street' and row['value'] == 'W 35th St':
            print('Made change to the row of index %s' % index)
            df_ways_tags.set_value(index, 'value', 'W 35th Street')




    #   By using the three code boxes above, I check the street with weird names. Actually, most of them are fine. I found one street with name of 633. This data may be a bad input. Because, there's no such street. I will keep my mind of this data. Besides, I correct the street name of 'W 35th st' to ' W 35th Street'.
    #
    #   Now, the street names are cleaned.

    # ### Codes for investigating the postcodes

    #looking for postcodes with irregular formats
    bad_postcode = []
    postcode = re.compile(r'^\d{5}$')
    for index, row in df_ways_tags.iterrows():
        if row['key'] == 'postcode' and row['value']:
            m = postcode.match(row['value'])
            if not m:
                bad_postcode.append((index, row['value']))
    print(bad_postcode)

    # I find there are 6 bad postcodes. I will change them into the correct format. Regarding the postcode of '83', I will set the postcode as None.

    get_postcode = re.compile(r'(?<!\d)\d{5}(?!\d)')

    #Correct the postcode
    for index, postcode in bad_postcode:
        if postcode:
            m2 = get_postcode.search(postcode)
            if m2:
                print("%s -> %s" % (postcode, m2.group(0)))
                df_ways_tags.set_value(index, 'value', m2.group(0))
            else:
                print("can't fix %s, set as None" % postcode)
                df_ways_tags.set_value(index, 'value', None)


    #Write the data frame to a new csv file.
    df_ways_tags.to_csv('ways_tags_clean.csv', index=False)
