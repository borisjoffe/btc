#!/usr/bin/python

import urllib, urllib2, json, sys, argparse, threading, os
from subprocess import check_output
import config
from time import sleep
if os.name == "posix":
	import curses, termios

exchangeURLs = { 'Mt Gox': ['https://data.mtgox.com/api/2/BTCUSD/money/ticker', 'data/last_local/display', ''], 
				 'CoinBase Sell': ['http://coinbase.com/api/v1/prices/sell', 'subtotal/amount', ''],
				 'CoinBase Buy': ['https://coinbase.com/api/v1/prices/buy', 'subtotal/amount', ''],
				 'CampBX': ['http://campbx.com/api/xticker.php', 'Last Trade', '']
				 #'Bitfloor Bid': ['https://api.bitfloor.com/book/L1/1', 'bid', ''],	# Bitfloor shut down 2013-Apr-17
				 #'Bitfloor Ask': ['https://api.bitfloor.com/book/L1/1', 'ask', '']
			   }

exchanges = exchangeURLs.keys()

# Fees
"""
Coinbase - 1% + $0.15/transaction
Bitfloor - 0.4% for buying BTC, -0.1% for selling BTC (you earn money)
Mt Gox - 0.6% or lower depending on volume + Dwolla ($0.25/transaction)
"""
#coinbaseBuyURL = 'https://coinbase.com/api/v1/account/balance'
btcQty = 1
btcVary = True
DEFAULT_REALTIME_SECONDS = 10	# default number of seconds for realtime ticker
HIGHLIGHT_COLOR = '\x1b[96;1m'
highlightXch = 'CampBX'
HIGHLIGHT_END = '\x1b[0m'

# use ANSI ESC codes for realtime option 
#	http://en.wikipedia.org/wiki/ANSI_escape_code
PREVIOUS_LINE = '\x1b[1F'	# go to beginning of previous line
ERASE_LINE = '\x1b[2K'	# clears entire line in terminal
CURSOR_UP = '\x1b[1A'	# go up one line
CURSOR_DOWN = '\x1b[1B'
CURSOR_FORWARD = '\x1b[1C'
CURSOR_BACK = '\x1b[1D'
SAVE_CURSOR = '\x1b[s'
RESTORE_CURSOR = '\x1b[u'

def buyBTC(btcQty=1, btcVary=True, dryRun=True, verbose=False, confirm=True):
	coinbaseBuyURL = "https://coinbase.com/api/v1/buys"
	print "Getting current price..."
	rate = getRate('CoinBase Buy')
	print "Current price is $" + rate + "/BTC"
	print "Your order total will be about $" + str(float(rate)*float(btcQty)), "(not incl. fees)\n"

	if confirm:
		c = raw_input("Would you like to continue? Type yes to confirm: ")
		if c != "yes":
			print "Did not buy any BTC."
			return

	print "Attempting to buy {0} BTC".format(btcQty)
	payload = { 'qty': btcQty, 'agree_btc_amount_varies': btcVary }
	payload = urllib.urlencode(payload)
	coinbaseBuyURL = coinbaseBuyURL + '?api_key=' + config.api_key
	
	if dryRun:
		print 'url: ' + coinbaseBuyURL + '\npayload: ' + payload
		print "Exiting dry run."
	elif not dryRun:
		r = urllib2.urlopen(url=coinbaseBuyURL, data=payload)
		buyData = json.load(r)
		print "Your purchase has been SUCCESSFULLY COMPLETED" if buyData['success'] else "Purchase failed due to the following error:\n=====\n{0}\n=====".format(json.dumps(buyData['errors']))
		print json.dumps(buyData['transfer']) if buyData['success'] else json.dumps(buyData)

	return 0

def getRate(xch):
	"""Return the price at a certain Exchange specified in exchangeURLs"""
	if not xch:
		print "Error: no exchange name given to getRate()";

	try:
		data = json.load( urllib2.urlopen(exchangeURLs[xch][0]) )
	except Exception as e:
		return str(e)

	keys = exchangeURLs[xch][1].split('/')

	for i in range(len(keys)):	# drill down the json based on forward slash separated keys
		data = data[keys[i]]

	if type(data) is list: # if we're left with a list, get the first element (for Bitfloor?)
		data = data[0]

	data = float(data.replace('$', '')) # temporarily remove dollar signs
	return str('{:>.2f}'.format(data))	# format to 2 decimal places and convert back to string

def showRate(xch, lock=None, async=False, verbose=False, realtime=0):
	"""Outputs nicely formatted prices for specified exchanges asynchronously"""
	if not xch:
		print "Error: no exchange name given to showRate()"
	if not lock and not realtime:
		print "Error: no lock given to showRate()"

	data = getRate(xch)
	#data = "test"

	if data.find('$') == -1: 	# add dollar sign
		data = '$' + data

	if config.use_colors and xch==highlightXch:		# highlight the most important one
		data = HIGHLIGHT_COLOR + data + HIGHLIGHT_END

	xch = xch.ljust(15)	# align it left and pad up to 15 spaces

	#if lock.acquire():
	if lock and realtime<=0:
		print '{xch}: {data}'.format(xch=xch, data=data)
		return '{xch}: {data}'.format(xch=xch, data=data)
		#lock.release()
	if realtime > 0:
		return '{xch}: {data}'.format(xch=xch, data=data)
		#print CURSOR_UP * 1 + CURSOR_FORWARD * 17 + data

def showRates(verbose=False, async=True, realtime=0):
	"""Outputs nicely formatted prices for the exchanges listed in exchangeURLs"""
	if realtime > 0:	# realtime mode (*NIX only)
		if not os.name=="posix":
			print "Error: realtime option is only supported on *NIX systems"
			return

		# TODO
		# make exchanges ordered - n-dim array - name, url, json
		# have exchange use ANSI ESC codes based on index
		# do we need to implement locks for stdout? or make them return values?? (extend Thread class??)
		# how to implement waiting interval before updates
		# remove curses deps and any others which are not required

		#print SAVE_CURSOR + CURSOR_UP
		
		# show initial table - has to be in order the same way to make sure
		#	all prices are displayed
		firstRun = True
		while True:
			try:
				bufferStr =  '=== ' + check_output(['date'])[:-1] + ' ===\n' 	# timestamp
				for xch in exchangeURLs:
					bufferStr +=  showRate(xch, realtime=2) + "\n"
						
				if not firstRun: print (ERASE_LINE + PREVIOUS_LINE) * 6
				print bufferStr[:-1]
				firstRun = False
				sleep(realtime)
			except:
				print "\nExiting."
				sys.exit()

		return

	if async:	# 2 threads can print to stdout (haven't implement locks yet)
		print "Getting prices (fast version, formatting may be off)..."
		print '===', check_output(['date'])[:-1], '===' 	# timestamp
		for xch in exchanges:
			lock = threading.RLock()
			t = threading.Thread(target=showRate, args=[xch, lock]);
			t.start()
		sys.exit()

	print '===', check_output(['date'])[:-1], '===' 	# timestamp
	print "Getting prices..."

	for xch in exchangeURLs:
		data = getRate(xch)

		if data.find('$') == -1: 	# add dollar sign
			data = '$' + data

		if config.use_colors and xch==highlightXch:		# highlight the most important one
			data = HIGHLIGHT_COLOR + data + HIGHLIGHT_END

		xch = xch.ljust(15)	# align it left and pad up to 15 spaces
		print '{xch}: {data}'.format(xch=xch, data=data)

def main():
	parser = argparse.ArgumentParser(description='Buy BTC or Show BTC:USD rates')
	parser.add_argument('--buy', nargs='?', const=1, help="Buy BTC" )
	parser.add_argument('--dry-run', action='store_const', default=False, const=True, help="Simulate buying BTC but do not actually buy anything") 
	parser.add_argument('--verbose', action='store_const', default=False, const=True)
	parser.add_argument('--no-async', action='store_const', default=False, const=True, help="Get prices one by one (slower but formatting is correct)")
	parser.add_argument('--realtime', nargs='?', type=int, const=DEFAULT_REALTIME_SECONDS, help="Show realtime ticker refreshing every REALTIME seconds (Only on UNIX)")

	args = parser.parse_args()
	if args.verbose: print 'args =', args
	#print 'args.buy =', args.buy

	if args.buy:
		buyBTC(btcQty=args.buy, dryRun=args.dry_run, verbose=args.verbose)
	else:
		showRates(verbose=args.verbose, async=not args.no_async, realtime=args.realtime);

if __name__ == "__main__":
	sys.exit(main())
