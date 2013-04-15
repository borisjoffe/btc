#!/usr/bin/python
import os, sys

config_filename = 'config.py'

def main():
	if os.access(config_filename, os.F_OK):	# if file exists
		print "A configuration file already exists." 
		c = raw_input("Are you sure you want to overwrite this? (type yes to override): ")
		if c != "yes":
			return

	f = open(config_filename, 'w');
	f.write('use_colors = False\n');

	key = raw_input("Paste Coinbase API Key (from https://coinbase.com/account/integrations)\napi_key=")
	f.write('api_key = ' + key + '\n')
	f.close()

if __name__ == "__main__":
	sys.exit(main())
