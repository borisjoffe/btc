#!/usr/bin/python

import urllib, urllib2, json, sys, argparse, string, threading, os
from subprocess import check_output
import config
if os.name=="posix":
	import curses, termios

exchangeURLs = { 'Mt Gox': ['https://data.mtgox.com/api/2/BTCUSD/money/ticker', 'data/last_local/display', ''], 
				 'CoinBase Xch': ['https://coinbase.com/api/v1/currencies/exchange_rates', 'btc_to_usd', ''],
				 'CoinBase Buy': ['https://coinbase.com/api/v1/prices/buy', 'amount', ''],
				 'Bitfloor Bid': ['https://api.bitfloor.com/book/L1/1', 'bid', ''],
				 'Bitfloor Ask': ['https://api.bitfloor.com/book/L1/1', 'ask', '']
			   }

#coinbaseBuyURL = 'https://coinbase.com/api/v1/account/balance'
btcQty = 1
btcVary = True
HIGHLIGHT_COLOR = '\x1b[96;1m'
highlightXch = 'CoinBase Buy'
HIGHLIGHT_END = '\x1b[0m'

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
		data = json.load( urllib2.urlopen( exchangeURLs[xch][0] ) )
	except urllib2.URLError:
		return "ERROR: Could not retrieve data"

	keys = exchangeURLs[xch][1].split('/')

	for i in range(len(keys)):	# drill down the json based on forward slash separated keys
		data = data[keys[i]]

	if type(data) is list: # if we're left with a list, get the first element (for Bitfloor?)
		data = data[0]

	data = float(data.replace('$', '')) # temporarily remove dollar signs
	return str('{:>.2f}'.format(data))	# format to 2 decimal places and convert back to string

def showRate(xch, lock, verbose=False):
	"""Outputs nicely formatted prices for specified exchanges asynchronously"""
	if not xch:
		print "Error: no exchange name given to showRate()"
	if not lock:
		print "Error: no lock given to showRate()"

	data = getRate(xch)
	#data = "test"

	if data.find('$') == -1: 	# add dollar sign
		data = '$' + data

	if config.use_colors and xch==highlightXch:		# highlight the most important one
		data = HIGHLIGHT_COLOR + data + HIGHLIGHT_END

	xch = string.ljust(xch, 15)	# align it left and pad up to 15 spaces

	#if lock.acquire():
	print '{xch}: {data}'.format(xch=xch, data=data)
		#lock.release()

def showRates(verbose=False, async=True, realtime=True):
	"""Outputs nicely formatted prices for the exchanges listed in exchangeURLs"""
	if os.name=="posix" and realtime:	# realtime curses mode (*NIX only)
		stdscr = curses.initscr()
		#curses.noecho()
		#curses.cbreak()
		#stdscr.keypad(1)
		win = curses.newwin(200, 80, 0, 0)

		win.addstr( "hello")
		stdscr.refresh()
		stdscr.getch()
		#curses.nocbreak(); stdscr.keypad(0); curses.echo(); 
		curses.endwin()	# end curses
		return

	if async:	# 2 threads can print to stdout (haven't implement locks yet)
		print "Getting prices (fast version, formatting may be off)..."
		print '===', check_output(['date'])[:-1], '===' 	# timestamp
		for xch in exchangeURLs:
			lock = threading.RLock()
			t = threading.Thread(target=showRate, args=[xch, lock]);
			t.start()
		return

	print '===', check_output(['date'])[:-1], '===' 	# timestamp
	print "Getting prices..."

	for xch in exchangeURLs:
		data = getRate(xch)

		if data.find('$') == -1: 	# add dollar sign
			data = '$' + data

		if config.use_colors and xch==highlightXch:		# highlight the most important one
			data = HIGHLIGHT_COLOR + data + HIGHLIGHT_END

		xch = string.ljust(xch, 15)	# align it left and pad up to 15 spaces
		print '{xch}: {data}'.format(xch=xch, data=data)

def main():
	parser = argparse.ArgumentParser(description='Buy BTC or Show BTC:USD rates')
	parser.add_argument('--buy', nargs='?', const=1, help="Buy BTC" )
	parser.add_argument('--dry-run', action='store_const', default=False, const=True, help="Simulate buying BTC but do not actually buy anything") 
	parser.add_argument('--verbose', action='store_const', default=False, const=True)
	parser.add_argument('--no-async', action='store_const', default=False, const=True, help="Get prices one by one (slower but formatting is correct)")
	parser.add_argument('--realtime', action='store_const', default=False, const=True, help="Show realtime ticker (Only on UNIX)")

	args = parser.parse_args()
	if args.verbose: print 'args =', args
	#print 'args.buy =', args.buy

	if args.buy:
		buyBTC(btcQty=args.buy, dryRun=args.dry_run, verbose=args.verbose)
	else:
		showRates(verbose=args.verbose, async=not args.no_async, realtime=args.realtime);

if __name__ == "__main__":
	sys.exit(main())
