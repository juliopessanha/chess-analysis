#!/usr/bin/env python
# coding: utf-8

import requests
import json
import os
import urllib.request
import pandas as pd
import re
#import cx_Oracle
from datetime import datetime, timedelta

folder_path = os.path.abspath("./")
PGNfolder = folder_path + "/PGN"

#print(PGNfolder)

def get_PGN(player, pgn = False):
    
    if pgn == False:
        pgn = ''
        
    elif pgn != False:
        pgn = '/pgn'
    
    #Gets the pgn files from the chesscom api and saves it locally by month file
    pgn_archives = requests.get('https://api.chess.com/pub/player/'+player.lower()+'/games/archives')
    #garantees that the player will always be lowercase, in case the user writes it differently
    print("Solving %s online data..." % player)
    try:
        #print(json.loads(pgn_archives.content)["archives"])
        skip_refiller = True #this variable helps to check if I have to remove the last month and redownload it
        if not os.path.exists(PGNfolder):
            #check if the main /pgn folder exist, if not it creates
            os.makedirs(PGNfolder)
            
        for month_url in json.loads(pgn_archives.content)["archives"]:
            #goes through all the archives and check each month
            user_folder = PGNfolder + '/' + month_url.split("/")[-4]
            folderpath = user_folder + "/" + month_url.split("/")[-2] + "-" + month_url.split("/")[-1]

            if not os.path.exists(user_folder):
                #checks if the name folder existis, if not it will create
                os.makedirs(user_folder)
            
            if not os.path.exists(folderpath+".txt"):
                #check if the month file exists, if not it will create
                urllib.request.urlretrieve(month_url + pgn, folderpath+".txt")
                print("New folder found %s" % folderpath)
                skip_refiller = False #it's a completely new month, it won't redownload it
        
        if skip_refiller:
            os.remove(folderpath + ".txt")
            urllib.request.urlretrieve(month_url + pgn, folderpath+".txt")
            print("Refilling folder %s" % folderpath)
        
        print("%s data solved." % player)
        return(True)
    except KeyError: #if the given player doesn't have an archive nor exists, it'll return as player not found and boolean False
        print("player not found")
        return(False)
    
def extract_data(filepath, pgn = True):
    #Loads the PGN files from the local folders
    #print("Reading PGN")
    with open(filepath) as f:
        #print(f.readlines())
        if pgn == True:
            return(f.readlines())
        else:
            data = []
            global data1
            data1 = f.readlines()
            for i in range(len(json.loads(data1[0])['games'])):
                try:
                    data.append(json.loads(data1[0])['games'][i]['pgn'].split('\n'))
                    data[i][-1] = json.loads(data1[0])['games'][i]['time_class'] #=data[i][:-1]
                
                except:
                    pass
            return(data)

def data_delimiter(data):
    #Returns two lists: One with the beginnings and another with the endings of each game in a data list
    start = []
    end = []
    
    for i,j in enumerate(data):
        
        if j.startswith("[Event"):
            start.append(i)
            if i != 0:
                end.append(i - 2)

    end.append(len(data))

    return(start, end)

def PGNExtract(data):
    s = data.split(" ")
    
    game = "1."
    
    for i, j in enumerate(s):
        
        if j != "1.":
            if ("1-0" in j) or ("0-1" in j) or ("1/2-1/2" in j):
                j = j[:-1]
                game = game + " " + j

            elif ("{" not in j) and ("}" not in j) and ("..." not in j):
                game = game + " " + j            
            
    return(game)

def pieceMoveCounter(moves, playerColor, timeControl_is, id_):
    #This function counts how many time I moved each piece
    s = moves.split(" ")
    
    pieceMoves[id_] = {"Q" : 0,
                       "N" : 0,
                       "R" : 0,
                       "K" : 0,
                       "B" : 0,
                       "p" : 0,
                       "O_O" : 0,
                       "O_O_O" : 0,
                       "x" : 0,
                       "check" : 0}
    
    if playerColor == "White":
        somador = 1
        
    elif playerColor == "Black":
        somador = 2
    
    for i, move in enumerate(s):
        if "." in move:
            if ("1-0" in s[i + somador]) or ("1/2-1/2" in s[i+somador]) or ("0-1" in s[i+somador]):
                break
            else:
                #print(s[i+somador])
                if "+" in s[i+somador]:
                    pieceMoves[id_]["check"] += 1

                if "x" in s[i+somador]:
                    pieceMoves[id_]["x"] += 1

                if "Q" in s[i+somador]:
                    pieceMoves[id_]["Q"] += 1

                elif "N" in s[i+somador]:
                    pieceMoves[id_]["N"] += 1

                elif "R" in s[i+somador]:
                    pieceMoves[id_]["R"] += 1

                elif "K" in s[i+somador]:
                    pieceMoves[id_]["K"] += 1

                elif "B" in s[i+somador]:
                    pieceMoves[id_]["B"] += 1

                elif "O-O-O" in s[i+somador]:
                    pieceMoves[id_]["O_O_O"] += 1

                elif "O-O" in s[i+somador]:
                    pieceMoves[id_]["O_O"] += 1

                else:
                    pieceMoves[id_]["p"] += 1

def transform_data(data, player, start = False, end = False):

    pattern = "\"(.*?)\"" #pattern for regular expression delimiting data between ""
    allGames = [] #list that will contain all the games
    if start == False: #if .txt has more than the pgn itself
        counter = data
        pgn_list_spot = -2 #the list has the 'timeClass', so the PGN isn't at the very end
    else: #if the .txt has only the pgn
        counter = start
        pgn_list_spot = -1 #the list will not have the 'timeClass', so the PGN is at the end
        
    for i in range(0, len(counter)):
        
        inGame = []
        #game = data[start[i]].split('\n')
        if start == False: #if .txt has more than the pgn itself
            game = data[i] #game delimitation  

        else: #if the .txt has only the pgn
            game = data[start[i]:end[i]] #game delimitation  

        if game[10].startswith("[ECOUrl"):
            whitePlayer = re.search(pattern, game[4]).group(1)
            if whitePlayer == player: #se o player estiver de brancas
                inGame.append(whitePlayer) #append player
                inGame.append("White") #append player color
                inGame.append(re.search(pattern, game[5]).group(1)) #append black player

            else:
                inGame.append(re.search(pattern, game[5]).group(1)) #append black player
                inGame.append("Black") #append player color
                inGame.append(whitePlayer) #append opponent

            winner = re.search(pattern, game[16]).group(1) #get winner and winning reason
            winner = winner.split(" ")

            if winner[0] == player:
                inGame.append('Winner') #indicates that the player won
                inGame.append(winner[-1]) #winning reason

            elif winner[0] == 'Game':
                inGame.append('Draw') #indicates that the player drew
                inGame.append(winner[-1]) #winning reason

            else:
                inGame.append('Loser') #indicates that the player lost
                inGame.append(winner[-1]) #winning reason

            if whitePlayer == player: #se o player estiver de brancas
                inGame.append(re.search(pattern, game[13]).group(1)) #player ELO
                inGame.append(re.search(pattern, game[14]).group(1)) #opponent ELO

            else: #Se o jogador estiver de pretas
                inGame.append(re.search(pattern, game[14]).group(1)) #Player ELO
                inGame.append(re.search(pattern, game[13]).group(1)) #Opponent ELO

            inGame.append(re.search(pattern, game[15]).group(1)) #Defines time control
            #print(game)
            dateObject = datetime.strptime(re.search(pattern, game[2]).group(1), "%Y.%m.%d") #Defines date in UTC
            time_utc = re.search(pattern, game[12]).group(1) #get the time in UTC

            #Here converts time UTC to UTC-3, since I'm brazilian
            utc_dt = dateObject.strftime("%d/%m/%Y") + " " + time_utc
            utc_dt = datetime.strptime(utc_dt, "%d/%m/%Y %H:%M:%S")
            utc_br = utc_dt - timedelta(hours=3)

            inGame.append(utc_br.strftime("%d/%m/%Y")) #Set date as dd/mm/YYYY

            inGame.append(utc_br.strftime("%H:%M:%S")) #insert time into the list

            pattern2 = "\"https://www.chess.com/openings/(.*?)\"" #gets the link our of the equation
            substring = re.search(pattern2, game[10]).group(1) #same
            
            pattern2 = "(.*?)\."
            #substring2 = re.search(pattern, substring).group(1)
            try: #this will try to remove the ...nf3 stuff
                substring = re.search(pattern2, substring).group(1)
                substring = substring.replace("-1", "")
                substring = substring.replace("-2", "")
                substring = substring.replace("-3", "")
                substring = substring.replace("-4", "")
                substring = substring.replace("-5", "")
                substring = substring.replace("-6", "")
            except: #if there's no stuff like this, continues normally
                substring = substring.replace("-1", "")
                substring = substring.replace("-2", "")
                substring = substring.replace("-3", "")
                substring = substring.replace("-4", "")
                substring = substring.replace("-5", "")
                substring = substring.replace("-6", "")
                
                        
            if "Opening" in substring:
                pattern2 = "(.*?)-Opening" #gets the link our of the equation
                substring = re.search(pattern2, substring).group(1) + "-Opening"#same
                #print(substring)
                
            if "Defense" in substring:
                pattern2 = "(.*?)-Defense" #gets the link our of the equation
                substring = re.search(pattern2, substring).group(1) + "-Defense"#same
                #print(substring)
                
            if "Game" in substring:
                pattern2 = "(.*?)-Game" #gets the link our of the equation
                substring = re.search(pattern2, substring).group(1) + "-Game"#same
                #print(substring)
            
            if "Attack" in substring:
                pattern2 = "(.*?)-Attack" #gets the link our of the equation
                substring = re.search(pattern2, substring).group(1) + "-Attack"#same
                #print(substring)
            
            #print(substring)
            inGame.append(substring)

            gamePGN = PGNExtract(game[pgn_list_spot])

            inGame.append(gamePGN) #pgn transformed into a string
            
            try: #the id from the game link is the id in the database
                pattern2 = "\"https://www.chess.com/game/live/(.*?)\"" #gets the link our of the equation
                inGame.append(re.search(pattern2, game[20]).group(1)) #same
            except:
                pattern2 = "\"https://www.chess.com/game/daily/(.*?)\"" #gets the link our of the equation
                inGame.append(re.search(pattern2, game[20]).group(1)) #same
            
            
            if start == False: #If the .txt files under /PGN has all the data, not only the pgn
                inGame.append(game[-1]) #it adds the timeClass
                 
            else: #If the .txt files under /PGN DO NOT have all the data: ONLY the pgn
                inGame.append("-") #it adds a bit of nothing
                    
            #Here it goes to the function to count how many times I moved each piece
            #pieceMoveCounter(gamePGN, inGame[1], inGame[-6], inGame[-2])

            #print("---")
            #print(inGame)
            allGames.append(inGame)
            
    return(allGames)
     
#######################################################################  
#Get some information to print later by a given dataframe
def get_print_info(dataFrame):
    
    #Total games played
    total_games = dataFrame.shape[0]
    
    #How many games tha player won
    games_won = dataFrame[dataFrame.result == 'Winner'].shape[0]
    #How many games tha player won
    games_lost = dataFrame[dataFrame.result == 'Loser'].shape[0]
    #How many games tha player won
    games_drew = dataFrame[dataFrame.result == 'Draw'].shape[0]
    
    return(games_won, games_lost, games_drew, total_games)

#Returns a percentage. To recude verbosity
def percent(numerator, denominator):
    return(round(((numerator / denominator)*100), 2))

#returns a dataframe with only rows where the player used a specific color and the most played opening
def get_color_opening(df_in, color):
    df_Games = df_in[df_in.playerColor == color] #Gets the chosen color
    df_Games = df_Games[df_Games.opening == df_Games.opening.mode()[0]] #Returns the most played opening in that color
    return(df_Games)

#Print some data from a given dataframe
def color_analysis_print(df_color):
    #Gets the player color
    color = df_color.playerColor.iloc[0]
    #get's some information to print
    games_won, games_lost, games_drew, total_games = get_print_info(df_color)

    percent_win = percent(games_won, total_games)
    percent_draw = percent(games_drew, total_games)
    percent_lost = percent(games_lost, total_games)
    #Print the information
    print("    %s: %s, with %s%% winrate" % (color, df_color.opening.mode()[0], percent_win))
    
#Get the dataframe with the specified time control
def get_specific_df(df_in, timeControl, pgn):

    if pgn == True: #If the .txt files under /PGN contains only the pgn

        if timeControl == 'All Time Controls':
            return(df_in)

        elif timeControl.lower() == 'blitz': #Between 3 and 5 minutes
            dfChess = df_in[(df_in.timeControl == '300') | (df_in.timeControl.str.contains('300\+')) | 
            (df_in.timeControl == '180') | (df_in.timeControl.str.contains('180\+'))]

        elif timeControl.lower() == 'rapid': #Between 10 and 30 minutes
            dfChess = df_in[(df_in.timeControl == '600') | (df_in.timeControl.str.contains('600\+')) | 
            (df_in.timeControl == '900') | (df_in.timeControl.str.contains('900\+')) |
            (df_in.timeControl == '1800') | (df_in.timeControl.str.contains('1800\+'))]

        elif timeControl.lower() == 'bullet': #Under 3 minutes
                dfChess = df_in[(df_in.timeControl == '60') | (df_in.timeControl.str.contains('60\+'))]

        else: #No time control found
            print("There's no %s time control" % (timeControl))
            return(None)
        return(dfChess)        
        
    else: #If the .txt files under /PGN contain more than only the PGN
        if timeControl == 'All Time Controls':
            return(df_in)
        else:
            dfChess = df_in[df_in.timeClass == timeControl.lower()]
            return(dfChess)

class chess():
    
    def __init__(self):
        #dfColumns = ["player", "playerColor", "opponent", "result", "winningReason", "playerElo", "oponentElo", "timeControl", 'date', 'time', 'opening', 'pgn', 'id']
        self.soup = ''
        #self.df = pd.DataFrame(columns=dfColumns)

    def extract(self, player, pgn = False):

        #The pgn function defines if the code will download ONLY the PGN or everything about each game
        #pgn = False. Everything will be download. The .txt will look uglier, but the dataframe will contain
        #      the "timeClass" column
        #pgn = True. Will work as before. The .txt will look pretty, but the dataframe won't contain the 'timeClass' column

        self.pgn = pgn
        dfColumns = ["player", "playerColor", "opponent", "result", "winningReason", "playerElo", "oponentElo", "timeControl", 'date', 'time', 'opening', 'pgn', 'id', 'timeClass']
        global pieceMoves
        pieceMoves = {}
        playerExists = get_PGN(player, pgn = pgn) #tries to download player PGN data
        if playerExists: #If the player exists, then:        

            self.df = pd.DataFrame(columns=dfColumns)
            #pieceMoves_df = pd.DataFrame(columns=pieceMovesColumns)
            with os.scandir(PGNfolder + "/" + player.lower()) as folders: #goes through all the player month files
                print("Creating dataframe")
                for file in folders:
                    #print(file)

                    data = extract_data(file, pgn = pgn) #load each month file into the memory

                    if pgn == True:
                        start, end = data_delimiter(data) #defines the limits of each data part
                        allGames = transform_data(data, player, start, end)
                    #print(data[start[k]:end[k]])
                    else:
                        allGames = transform_data(data, player)#, start, end)
                    
                    #break
                    df2 = pd.DataFrame(data=allGames, columns=dfColumns)
                    self.df = self.df.append(df2, ignore_index=True)
                    
                    if pgn == True: #If the .txt files under /PGN has only the pgn from the site
                                    #the 'timeClass' column is dropped because it's empty
                        self.df.drop(columns=['timeClass'], inplace=True)
                    
            ### TO SORT THE DATAFRAME BY DATETIME
            #Create a array with date and time
            new_datetime = self.df.date + " " + self.df.time

            #Creates a column with "datetime" from the array above
            self.df['datetime'] = pd.to_datetime(new_datetime, format='%d/%m/%Y %H:%M:%S')
            self.df.sort_values(by='datetime', inplace=True) #Sort the dataframe by the datetime column
            self.df.reset_index(drop=True, inplace=True) #Reset the index, since it was sorted
            self.df.drop(columns=['datetime'], inplace=True) #Drop the new datetime dataframe
            self.df['date'] = pd.to_datetime(self.df['date'], dayfirst=True) #Turns the date column into date format
            #self.df = self.df.sort_values(by='date')

        else: #If the player does not exist, it stops
            print("There's no %s data on chess.com" % player)

        print("Done")  


    def stats(self, timeControl = 'All Time Controls', **kwargs):
        ArchEnemy = bool(kwargs.get('ArchEnemy', False)) #Define if it's gonna show the arch enemy
        afterDate = kwargs.get('after', False) #define starting date to show on stats
        beforeDate = kwargs.get('before', False) #Define last date to show on stats
        opponent = kwargs.get('opponent', False) #Define an specific opponent
        #Get the dataframe from the specific time control
        dfChess = get_specific_df(self.df, timeControl, self.pgn)

        if afterDate != False: #If the user chose a date to start
            dfChess = dfChess[dfChess.date >= str(afterDate)]

        if beforeDate != False: #If the user chose an ending date
            dfChess = dfChess[dfChess.date <= str(beforeDate)]

        if (opponent != False): #If the user chose an specific opponent
            dfChess = dfChess[dfChess.opponent.str.lower() == str(opponent).lower()]

        try:

            games_won, games_lost, games_drew, total_games = get_print_info(dfChess)

            percent_win = percent(games_won, total_games)
            percent_draw = percent(games_drew, total_games)
            percent_lost = percent(games_lost, total_games)

            print("--------------------------------------------------")
            player = self.df.player.iloc[0]
            print("   Chess analysis for %s  - %s" % (player, timeControl.title()))
            print("--------------------------------------------------")
            
            if timeControl != 'All Time Controls':
                rating = dfChess.playerElo.iloc[-1]
                print('Current ELO: %s' % rating)
                peakRating = pd.to_numeric(dfChess.playerElo).max()
                print('Peak ELO: %s' % peakRating)

            print("\n%s played %s games\n\n  Wins %s (%s%%)\n  Draws %s (%s%%)\n  Loses %s (%s%%)" % (player, total_games, games_won, percent_win \
                                                                                , games_drew, percent_draw, games_lost, percent_lost))

            #########################################################################
            print('\nMost played opening as')

            try:
                df_whiteGames = get_color_opening(dfChess, 'White')
                color_analysis_print(df_whiteGames)
                del df_whiteGames
            except:
                print("    White: No games found")

            try:    
                df_blackGames = get_color_opening(dfChess, 'Black')
                color_analysis_print(df_blackGames)
                del df_blackGames
            except:
                print("    Black: No game found")

            #########################################################################

            if ArchEnemy == True:
                #The opponent the player most played agaisnt
                df_mostPlayed = dfChess[dfChess.opponent == dfChess.opponent.mode()[0]]
                print('\n-----------------\n\nArch-enemy: %s\n' % (df_mostPlayed.opponent.iloc[0]))

                #Some info to print
                games_won, games_lost, games_drew, total_games = get_print_info(df_mostPlayed)

                percent_win = percent(games_won, total_games)
                percent_draw = percent(games_drew, total_games)
                percent_lost = percent(games_lost, total_games)

                print('%s won %s games out of %s against %s\n' % \
                    (player, games_won, total_games, df_mostPlayed.opponent.iloc[0]))

                del df_mostPlayed
                print('  Wins: %s%%\n  Draws: %s%%\n  Loses: %s%%\n' % (percent_win, percent_draw, percent_lost))

        except:
            print("No games found")

if __name__ == "__main__":
    print("-")
