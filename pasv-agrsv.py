#!/usr/bin/env python
'''
@author: Matthew C. Jones, CPA, CISA, OSCP
IS Audits & Consulting, LLC
TJS Deemer Dana LLP

Passive external footprinting

See README.md for licensing information and credits

'''
import ConfigParser
import argparse
import logging
import os

import modules.core
import modules.tools


#------------------------------------------------------------------------------
# Configure Argparse to handle command line arguments
#------------------------------------------------------------------------------
desc = "Passive footprinting automation script"

parser = argparse.ArgumentParser(description=desc)
parser.add_argument("domain", help="Domain to analyze (e.g. example.com)")
parser.add_argument('-c','--config',
                    help='Configuration file. (default: config/default.cfg)',
                    action='store', default='config/default.cfg'
)
parser.add_argument('-o','--output',
                    help='Output directory (overrides default relative path: "output")',
                    action='store', default='output'
)
parser.add_argument('-d','--debug',
                    help='Print lots of debugging statements',
                    action="store_const",dest="loglevel",const=logging.DEBUG,
                    default=logging.WARNING
)
parser.add_argument('-v','--verbose',
                    help='Be verbose',
                    action="store_const",dest="loglevel",const=logging.INFO
)
args = parser.parse_args()

domain = args.domain
config_file = args.config
output_dir = args.output

logging.basicConfig(level=args.loglevel)
logging.info('verbose mode enabled')
logging.debug('Debug mode enabled')

#------------------------------------------------------------------------------
# Get config file parameters
#------------------------------------------------------------------------------
modules.core.check_config(config_file)
config = ConfigParser.SafeConfigParser()
config.read(config_file)

try:
    output_dir = os.path.join(config.get("main_config", "output_dir"), domain)
    website_output_format = config.get("main_config", "website_output_format")
    suppress_out = config.getboolean("main_config", "suppress_out")
except:
    print "Missing required config file sections. Check running config file against provided example\n"
    modules.core.exit_program()


#------------------------------------------------------------------------------
# Main Program
#------------------------------------------------------------------------------

is_output_dir_clean = modules.core.cleanup_routine(output_dir)
ip_list = []
dns_list = []
email_list = []
tools = []
instances = []


print "Parsing tools config file..."
for section in config.sections():
    if section == "main_config":
        pass
    else:
        tool = modules.tools.tool()
        tool.name = section
        if config.has_option(tool.name, "command"):
            tool.command = config.get(tool.name,"command")
        if config.has_option(tool.name, "url"):
            tool.url = config.get(tool.name,"url")
        if config.has_option(tool.name, "run_domain"):
            tool.run_domain = config.getboolean(tool.name,"run_domain")
        if config.has_option(tool.name, "run_ip"):
            tool.run_ip = config.getboolean(tool.name,"run_ip")
        if config.has_option(tool.name, "run_dns"):
            tool.run_dns = config.getboolean(tool.name,"run_dns")
        if config.has_option(tool.name, "email_regex"):
            tool.email_regex = config.get(tool.name,"email_regex")
        if config.has_option(tool.name, "ip_regex"):
            tool.ip_regex = config.get(tool.name,"ip_regex")
        if config.has_option(tool.name, "dns_regex"):
            tool.dns_regex = config.get(tool.name,"dns_regex")
        if config.has_option(tool.name, "cleanup_regex"):
            tool.cleanup_regex = config.get(tool.name,"cleanup_regex")
        if config.has_option(tool.name, "output_subdir"):
            tool.output_subdir = config.get(tool.name,"output_subdir")
        tools.append(tool)

print "\nRunning domain tools..."
for tool in tools:
    if tool.run_domain == True:
        print "\nRunning " + tool.name + "..."
        instance = modules.tools.instance()
        instance.build_instance_from_tool(tool)
        
        instance.target = domain
        instance.output_dir = output_dir
        instance.suppress_out = suppress_out
        instance.website_output_format = website_output_format
        
        instance.run()
        instances.append(instance)
        
        ip_list += instance.ip
        dns_list += instance.dns
        email_list += instance.emails 


#sort and remove duplicate items from lists:
ip_list = sorted(list(set(ip_list)))
dns_list = sorted(list(set(dns_list)))
email_list = sorted(list(set(email_list)))

#Get missing IP addresses from DNS list using nslookup
for target in dns_list:
    instance = modules.tools.instance()
    instance.target = target
    instance.command = "nslookup [TARGET]"
    instance.ip_regex = "Address: (\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b)"
    instance.output_dir = output_dir
    instance.output_subdir = "hosts"
    instance.suppress_out = suppress_out
    instance.website_output_format = website_output_format
    instance.run
    instances.append(instance)

ip_list = sorted(list(set(ip_list)))

#Get missing DNS addresses from IP list using nslookup
for target in ip_list:
    instance = modules.tools.instance()
    instance.target = target
    instance.command = "nslookup [TARGET]"
    instance.dns_regex = "name = (.*)"
    instance.output_dir = output_dir
    instance.output_subdir = "hosts"
    instance.suppress_out = suppress_out
    instance.website_output_format = website_output_format
    instance.run
    instances.append(instance)

dns_list = sorted(list(set(dns_list)))

print "\nRunning host tools..."
for tool in tools:
    if tool.run_ip == True:
        print "\nRunning " + tool.name + "..."
        for target in ip_list:
            print "Checking " + target + "..."
            instance = modules.tools.instance()
            instance.build_instance_from_tool(tool)
            
            instance.target = target
            instance.output_dir = output_dir
            instance.suppress_out = suppress_out
            instance.website_output_format = website_output_format
            
            instance.run()
            instances.append(instance)
            
    if tool.run_dns == True:
        print "\nRunning " + tool.name + "..."
        for target in dns_list:
            print "Checking " + target + "..."
            instance = modules.tools.instance()
            instance.build_instance_from_tool(tool)
            
            instance.target = target
            instance.output_dir = output_dir
            instance.suppress_out = suppress_out
            instance.website_output_format = website_output_format
            
            instance.run()
            instances.append(instance)

str_ip = modules.core.list_to_text(ip_list)
modules.core.write_outfile(output_dir, "summary-ip.txt", str_ip)
print "\nDetected IP addresses:\n" + str_ip + "\n"

str_dns = modules.core.list_to_text(dns_list)
modules.core.write_outfile(output_dir, "summary-dns.txt", str_dns)
print "Detected dns aliases:\n" + str_dns + "\n"

str_emails = modules.core.list_to_text(email_list)
modules.core.write_outfile(output_dir, "summary-emails.txt", str_emails)
print "Detected email addresses:\n" + str_emails + "\n"


print "\nScript execution completed!"