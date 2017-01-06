from __future__ import division
import math
import bs4
import requests
import api
from datetime import datetime
import time


#These times need to be adjusted
lay_odds_limit = 3.51 
match_time_limit = 15 # Places bets on 0 - 0 matches if less than this amount of time has passed.
lay_stake = 4.00 # Can't be lower
exit_time = 75 # Time to exit bet at if no goal is scored
cashout_wait = 30 # seconds Time waited before cashout (and new back odds are read for calculating back_amount)
place_bets = False # False = Paper Trading only. True = Real money trading.




def exitBet(betInfo,marketId, selectionId,lay_amount,lay_odds,back_odds,status):
	if status == 'OPEN':
		back_amount= round((eval(lay_odds)/(back_odds))*lay_amount,2)
		submitted_back_odds = 1.01
		print "back amount: " + str(back_amount) + "\n lay amount: " + str(lay_amount) + "\n back odds:" + str(back_odds) + "\n submitted back odds:" + str(submitted_back_odds) + "\n lay odds: " + lay_odds
		if api.placeBet(marketId,selectionId,'BACK',str(back_amount),str(submitted_back_odds)) == 'SUCCESS':
			logExit(betInfo) #+ ",layAmount: " + str(2))   #Check that bet is successful before logging
			print "EXITED BET: " + str(betInfo)
		else: 
			print "FAILED TO PERFORM EXIT"

def checkExit(betInfo):
	exit_logs = open('./logs/exittedbets.txt','r').read()
	if betInfo in exit_logs:
		return True
	else:
		return False
	#returns true if cashout has already been done

def logExit(betInfo):
	exit_logs = open('./logs/exittedbets.txt','a')
	exit_logs.write(betInfo + '\n')
	exit_logs.close()
	print "EXIT LOGGED"
	# Only do this if bet is placed successfully

def placeBet(betInfo,home_team,away_team,marketId, selectionId,bet_id,result,bet_amount,lay_odds,status):
	if status == 'OPEN':
		if place_bets:
			if checkBetsPlaced(betInfo.split(', backPrice:')[0]) == False:
				if result == '0 - 0':
					if lay_odds < lay_odds_limit:
						if api.placeBet(marketId, selectionId,'LAY',str(bet_amount),str(lay_odds))== 'SUCCESS':	
							logBetsPlaced(betInfo,home_team,away_team)# + ",layAmount: " + str(2)) #Only do if bet was successful. Should also log the price and bet size	
							print "BET PLACED:" + str(betInfo)
						else:
							print "FAILED TO PERFORM BET"						
							print "There is an error below:" +  "\n selectionId: " + str(selectionId) + "\n bet amount: " + str(bet_amount) + "\n lay odds: " + str(lay_odds)

		

def cashOut(betInfo,marketId, selectionId,lay_amount,lay_odds,back_odds,status):
	if back_odds < lay_odds:
		back_odds = lay_odds
	if status == 'OPEN':
		back_odds_predicted = 1.9*eval(lay_odds)
		back_amount = round((eval(lay_odds)/eval(back_odds))*lay_amount,2) #use if using delay before cashout
		back_amount_predicted= round((eval(lay_odds)/back_odds_predicted)*lay_amount,2) # This works awfully
		back_odds_inputted = 1.02 # round(eval(lay_odds),2)
		if api.placeBet(marketId,selectionId,'BACK',str(back_amount),str(back_odds_inputted)) == 'SUCCESS':
			logCashOut(betInfo)#+ ",layAmount: " + str(2))   #Check that bet is successful before logging
			print "CASHOUT PLACED: " + str(betInfo)
		else:
			print "odds are " + str(back_odds_inputted)
			cashOut(betInfo,marketId, selectionId,lay_amount,lay_odds,back_odds,status)
			print "FAILED TO PERFORM CASHOUT"
	else:
		cashOut(betInfo,marketId, selectionId,lay_amount,lay_odds,back_odds,status)

def findProfit(lay_amount,lay_odds,back_odds):
	back_amount = (eval(lay_odds)/eval(back_odds))*eval(lay_amount)
	profit = eval(lay_amount)-back_amount
	return profit

def	checkBetsLines(marketId):
	bet_logs = open('./logs/betlogs.txt','r').readlines()
	for line in bet_logs:
		if marketId in line:
			lay_price = line.split('layPrice: ')[1].split(', homeTeam:')[0]
			return lay_price



def logProfit(profit):
	profit_logs = open('./logs/profitlogs.txt','a')
	profit_logs.write(profit + '\n')
	profit_logs.close()
	print "PROFIT LOGGED"

def checkForScoreChange(scoresInfo):
	score_logs = open('./logs/scorelogs.txt','r').read()
	if scoresInfo.split(', time: ')[0] in score_logs:
		return False
	else:
		return True
	#return true if score changes

def checkNewGames(scoresInfo):
	score_logs = open('./logs/scorelogs.txt','r').read()
	if scoresInfo.split(', homeTeam:')[0] in score_logs:
		return False
	else:
		return True
	# Returns true if the match is new (i.e. if it is not in the file)

def logScores(scoresInfo):
	score_logs = open('./logs/scorelogs.txt','a')
	score_logs.write(scoresInfo + '\n')
	score_logs.close()

def checkBetsPlaced(betInfo):
	bet_logs = open('./logs/betlogs.txt','r').read()
	if betInfo in bet_logs:
		return True
	else:
		return False
	# Returns true if bet has already been placed

def logBetsPlaced(betInfo,home_team,away_team):
	bet_logs = open('./logs/betlogs.txt','a')
	bet_logs.write(betInfo + '\n')
	bet_logs.close()
	print "BET LOGGED " + str(home_team) + " - " + str(away_team)
	# Only do this if bet is placed successfully

def checkCashOut(betInfo):
	cashout_logs = open('./logs/cashoutlogs.txt','r').read()
	if betInfo in cashout_logs:
		return True
	else:
		return False
	#returns true if cashout has already been done

def logCashOut(betInfo):
	cashout_logs = open('./logs/cashoutlogs.txt','a')
	cashout_logs.write(betInfo + '\n')
	cashout_logs.close()
	print "CASHOUT LOGGED"
	# Only do this if bet is placed successfully


def scanner():
	now = datetime.now()
	sourceOne = requests.get('https://www.betfair.com/exchange/football/coupon?id=' + str((now.weekday() + 1)%7 + 1) + '&goingInPlay=false&fdcPage=1').text 
	sourceTwo = requests.get('https://www.betfair.com/exchange/football/coupon?id=' + str((now.weekday() + 1)%7 + 1) + '&goingInPlay=false&fdcPage=2').text 
	sourceThree = requests.get('https://www.betfair.com/exchange/football/coupon?id=' + str((now.weekday() + 1)%7 + 1) + '&goingInPlay=false&fdcPage=3').text 
	sourceFour = requests.get('https://www.betfair.com/exchange/football/coupon?id=' + str((now.weekday() + 1)%7 + 1) + '&goingInPlay=false&fdcPage=4').text 
	soupOne = bs4.BeautifulSoup(sourceOne, "html5lib")
	soupTwo = bs4.BeautifulSoup(sourceTwo, "html5lib")
	soupThree = bs4.BeautifulSoup(sourceThree, "html5lib")
	soupFour = bs4.BeautifulSoup(sourceFour, "html5lib")
	games = soupOne.select('.inplaynow') + soupTwo.select('.inplaynow') #+ soupThree.select('.inplaynow') + soupFour.select('.inplaynow')
	for game in games:
		start = game.select('.start-time')[0].getText().replace("HT","45'").replace("FT","90'")#.replace("-","")
		if '-' in start:
			start = '90'
		market_id = game['class'][1].split('-')[-1]
		home_team = game.select('.home-team')[0].getText()
		away_team = game.select('.away-team')[0].getText()
		resultcheck = game.select('.result')[0].getText()
		if resultcheck == '':
			result = '0 - 0'
		else:
			result = resultcheck
		home_score = result.split(' - ')[0]
		away_score = result.split(' - ')[1]
		market_data = api.getMarketBookBestOffers(market_id)[0]
		market_status = market_data['status']
		in_play = market_data['inplay']
		runners_data = market_data['runners']
		home_data = runners_data[0]
		away_data = runners_data[1]
		draw_data = runners_data[2]
		draw_selectionId = draw_data['selectionId']
		draw_back = draw_data['ex']['availableToBack']
		draw_lay = draw_data['ex']['availableToLay']
		try:
			draw_lay_price = draw_lay[0]['price']
		except IndexError:
			draw_lay_price = '1000'
		try:
			draw_lay_size = draw_lay[0]['size']
		except IndexError:
			draw_lay_size = 0
		try:
			draw_back_price = draw_back[0]['price'] # api.getMarketBookBestOffers(market_id)[0]['runners'][2]['availableToBack'][0]['price']
		except IndexError:
			draw_back_price = '1'
		try:
			draw_back_size = draw_back[0]['size']
		except IndexError:
			draw_back_size = 0
		scoresInfo =  "marketId: " + str(market_id) + ", homeTeam: " + str(home_team) + ", awayTeam: " + str(away_team) + ", homeScore: " + str(home_score) + ", awayScore: " + str(away_score) + ", time: " + now.strftime('%Y/%m/%d %H:%M:%S')
		betInfo = "marketId: " + str(market_id) + ", SelectionId: " + str(draw_selectionId) + ", backPrice: " + str(draw_back_price) + ",layPrice: " + str(draw_lay_price) + ", homeTeam: " + str(home_team) + ", awayTeam: " + str(away_team) + ", time: " + now.strftime('%Y/%m/%d %H:%M:%S')
		if checkNewGames(scoresInfo) == False:
				if checkForScoreChange(scoresInfo) == True:
					if checkCashOut(betInfo.split(', backPrice:')[0]) == False:
						if checkBetsPlaced(betInfo.split(', backPrice:')[0]) == True:
							previous_lay_odds = checkBetsLines(market_id)
							print "sleeping for " + str(cashout_wait) + "s"
							time.sleep(cashout_wait)
							back_odds = api.getMarketBookBestOffers(market_id)[0]['runners'][2]['ex']['availableToBack'][0]['price']
							if back_odds < previous_lay_odds:
								time.sleep(20)
								back_odds = api.getMarketBookBestOffers(market_id)[0]['runners'][2]['ex']['availableToBack'][0]['price']
								if back_odds < previous_lay_odds:
									time.sleep(20)
									back_odds = api.getMarketBookBestOffers(market_id)[0]['runners'][2]['ex']['availableToBack'][0]['price']
									if back_odds < previous_lay_odds:
										time.sleep(20)
										back_odds = api.getMarketBookBestOffers(market_id)[0]['runners'][2]['ex']['availableToBack'][0]['price']
												back_odds = api.getMarketBookBestOffers(market_id)[0]['runners'][2]['ex']['availableToBack'][0]['price']
												cashOut(betInfo,market_id, draw_selectionId,lay_stake,previous_lay_odds,back_odds,market_status) 
									else:
										cashOut(betInfo,market_id, draw_selectionId,lay_stake,previous_lay_odds,back_odds,market_status)
								else:
									cashOut(betInfo,market_id, draw_selectionId,lay_stake,previous_lay_odds,back_odds,market_status)
							else:
								cashOut(betInfo,market_id, draw_selectionId,lay_stake,previous_lay_odds,back_odds,market_status) # make sure to get lay amount and lay odds from file, NOT api							
							profit = findProfit(str(lay_stake),previous_lay_odds,str(draw_back_price))
							print "Cashout: " + str(betInfo)
		if "Starting" in start:
			placeBet(betInfo,home_team,away_team,market_id, draw_selectionId,betInfo.split(', backPrice:')[0],result,lay_stake,draw_lay_price,market_status)
		elif ":" in start:
			placeBet(betInfo,home_team,away_team,market_id, draw_selectionId,betInfo.split(', backPrice:')[0],result,lay_stake,draw_lay_price,market_status)
		elif "'" in start:
			if eval(start.replace("'","")) < match_time_limit:
				placeBet(betInfo,home_team,away_team,market_id, draw_selectionId,betInfo.split(', backPrice:')[0],result,lay_stake,draw_lay_price,market_status)
			elif eval(start.replace("'","")) > exit_time:
				if checkExit(betInfo.split(', backPrice:')[0]) == False:
					if checkBetsPlaced(betInfo.split(', backPrice:')[0]) == True:
						if result == '0 - 0':
							old_lay_odds = checkBetsLines(market_id)
							exitBet(betInfo,market_id, draw_selectionId,lay_stake,old_lay_odds,draw_back_price,market_status)
		else:
			#print "The time stamp doesnt contain ', Starting in, or : --- start = " + start + "betInfo = " + betInfo
			continue
		logScores(scoresInfo)		

while __name__ == "__main__":
	now = datetime.now()
	print "Running program at " + now.strftime('%Y/%m/%d %H:%M:%S')
	scanner()
