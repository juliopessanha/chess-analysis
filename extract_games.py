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

print(PGNfolder)

def get_PGN(player):
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
                urllib.request.urlretrieve(month_url+'/pgn', folderpath+".txt")
                print("New folder found %s" % folderpath)
                skip_refiller = False #it's a completely new month, it won't redownload it
        
        if skip_refiller:
            os.remove(folderpath + ".txt")
            urllib.request.urlretrieve(month_url+'/pgn', folderpath+".txt")
            print("Refilling folder %s" % folderpath)
        
        print("%s data solved." % player)
        return(True)
    except KeyError: #if the given player doesn't have an archive nor exists, it'll return as player not found and boolean False
        print("player not found")
        return(False)
    
def extract_data(filepath):
    #Loads the PGN files from the local folders
    #print("Reading PGN")
    with open(filepath) as f:
        #print(f.readlines())
        return f.readlines()
    
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

def transform_data(data, start, end, player):

    pattern = "\"(.*?)\"" #pattern for regular expression delimiting data between ""
    allGames = []
    for i in range(0, len(start)):
        
        inGame = []
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
                
            gamePGN = PGNExtract(game[-1])
                
            inGame.append(gamePGN) #pgn transformed into a string
            
            try: #the id from the game link is the id in the database
                pattern2 = "\"https://www.chess.com/game/live/(.*?)\"" #gets the link our of the equation
                inGame.append(re.search(pattern2, game[20]).group(1)) #same
            except:
                pattern2 = "\"https://www.chess.com/game/daily/(.*?)\"" #gets the link our of the equation
                inGame.append(re.search(pattern2, game[20]).group(1)) #same
            
            
            #Here it goes to the function to count how many times I moved each piece
            pieceMoveCounter(gamePGN, inGame[1], inGame[-6], inGame[-1])

            #print("---")
            #print(inGame)
            allGames.append(inGame)

            
    return(allGames)
        
def main(player):
    dfColumns = ["player", "playerColor", "opponent", "result", "winningReason", "playerElo", "oponentElo", "timeControl", 'date', 'time', 'opening', 'pgn', 'id']
    global pieceMoves
    pieceMoves = {}
    playerExists = get_PGN(player) #tries to download player PGN data
    if playerExists: #If the player exists, then:        
        
        #global df
        df = pd.DataFrame(columns=dfColumns)
        #pieceMoves_df = pd.DataFrame(columns=pieceMovesColumns)
        with os.scandir(PGNfolder + "/" + player.lower()) as folders: #goes through all the player month files
            for file in folders:
                #print(file)
                data = extract_data(file) #load each month file into the memory
                start, end = data_delimiter(data) #defines the limits of each data part
                
                #print(data[start[k]:end[k]])

                allGames = transform_data(data, start, end, player)
                
                df2 = pd.DataFrame(data=allGames, columns=dfColumns)
                df = df.append(df2, ignore_index=True)

        print("Trying to insert into database")
                
    else: #If the player does not exist, it stops
        print("There's no %s data on chess.com" % player)

    print("end")   
    return(df)


if __name__ == "__main__":
    print("-")

    #main("GMKrikor")
