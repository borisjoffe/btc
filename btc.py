#!/usr/bin/python

import urllib, urllib2, json, sys, argparse, string
from subprocess import check_output
import config

exchangeURLs = { 'Mt Gox': ['https://data.mtgox.com/api/2/BTCUSD/money/ticker', 'data/last_local/display', ''], 
				 'CoinBase Xch': ['https://coinbase.com/api/v1/currencies/exchange_rates', 'btc_to_usd', ''],
				 'CoinBase Buy': ['https://coinbase.com/api/v1/prices/buy', 'amount', ''],
				 'Bitfloor Bid': ['https://api.bitfloor.com/book/L1/1', 'bid', ''],
				 'Bitfloor Ask': ['https://api.bitfloor.com/book/L1/1', 'ask', '']
			   }

#coinbaseBuyURL = 'https://coinbase.com/api/v1/account/balance'
btcQty = 1
btcVary = True

def buyBTC(btcQty=1, btcVary=True, dryRun=True, verbose=False):
	coinbaseBuyURL = "https://coinbase.com/api/v1/buys"
	#print "Connecting to CoinBase API..."
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


def showRates(verbose=False):
	print "Getting prices..."

	for xch in exchangeURLs:
		exchangeURLs[xch][2] = urllib2.urlopen( exchangeURLs[xch][0] )
		if verbose: print "Got", xch

	print '===', check_output(['date'])[:-1], '==='

	for xch in exchangeURLs:
		keys = exchangeURLs[xch][1].split('/')

		data = json.load( exchangeURLs[xch][2] )
		for i in range(len(keys)):	# drill down the json based on forward slash separated keys
			data = data[keys[i]]

		if type(data) is list: # if we're left with a list, get the first element
			data = data[0]

		data = float(data.replace('$', '')) # temporarily remove dollar signs
		data = str('{:>.2f}'.format(data))	# format to 2 decimal places and convert back to string

		if data.find('$') == -1:
			data = '$' + data
		xch = string.ljust(xch, 15)
		print '{xch}: {data}'.format(xch=xch, data=data)

def main():
	parser = argparse.ArgumentParser(description='Buy BTC or Show BTC:USD rates')
	parser.add_argument('--buy', nargs='?', const=1 )
	parser.add_argument('--dry-run', action='store_const', default=False, const=True) 
	parser.add_argument('--verbose', action='store_const', default=False, const=True)

	args = parser.parse_args()
	if args.verbose: print 'args =', args
	#print 'args.buy =', args.buy

	if args.buy:
		buyBTC(btcQty=args.buy, dryRun=args.dry_run, verbose=args.verbose)
	else:
		showRates(verbose=args.verbose);

if __name__ == "__main__":
	sys.exit(main())
