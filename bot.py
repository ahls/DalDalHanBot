# bot.py
import os
import discord
import requests
import random
from enum import Enum
from dotenv import load_dotenv
import pandas as pd
df = pd.read_excel(r'fight.xlsx')
rankValueSheet = df.iloc[1:,1:].to_numpy()
print(rankValueSheet)

load_dotenv()
#봇 연결에 필요한 정보
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = ("HAN","DALDAL Clan")#os.getenv('DISCORD_GUILD')
apikey = os.getenv('API_KEY')

#게임 참가에 쓰이는 정보
admins = {"Han#6098","sinnamon#9618"}
positions = ("top","jg","mid","adc","sup")
tier_score = {"IRON": 0, "BRONZE": 4, "SILVER": 8, "GOLD": 12, "PLATINUM": 16, "DIAMOND": 20, "MASTER": 24, "GRANDMASTER": 28, "CHALLENGER": 32}
rank_score = {"I":4, "II":3, "III":2, "IV":1}
players = {} #"플레이어 이름" : 포지션1, 포지션2, 총 랭크 점수
profiles = {} #"디스코드 이름: 게임내 이름, 포지션 1, 포지션 2"
numTeams = 2
import numpy as np

def teamScore(dic):
    total = 0
    for i in dic.keys():
        total += dic[i][2]
    return total

def initAssignment(givenList):
    team1 = {}
    team2 = {}
    team1Score = team2Score = 0;    
    print (givenList)
    print (givenList.keys())
    for i in givenList.keys():
        print (givenList[i][2])
        if(team1Score < team2Score):
            if(len(team1) < 5):
                team1[i]=givenList[i]
                team1Score += givenList[i][2]
            else:
                team2[i]=givenList[i]
                team2Score += givenList[i][2]
                
        else:
            if(len(team2) < 5):
                team2[i]=givenList[i]
                team2Score += givenList[i][2]
            else:
                team1[i]=givenList[i]
                team1Score += givenList[i][2]
    return team1, team2


def tryOpt(team1,team2):
    team1Score = teamScore(team1)
    team2Score = teamScore(team2)
    diff = team1Score-team2Score
    if diff == 0:
        return team1, team2, 0
    #if + -> team 1 more score. if - -> team2 more score
    bestDiff = 99
    bestMember1 = -1
    bestMember2 = -1
    for member1 in (team1.keys()):
        for  member2 in (team2.keys()):
            tempDiff = abs(diff - 2 * (team1[member1][2] - team2[member2][2]))
            if tempDiff < bestDiff :
                bestDiff = tempDiff
                bestMember1 = member1
                bestMember2 = member2
    scoreGain = abs(diff)-bestDiff
    
    if(bestMember1 != -1 and bestMember2 != -1):
        team1[bestMember2]= team2[bestMember2]
        team2[bestMember1]= team1[bestMember1]
        team1.pop(bestMember1)
        team2.pop(bestMember2)
        
    return team1,team2,scoreGain

def getSummonerInfo(userName):
    summonerInfo = (requests.get('https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/' + userName + '?api_key=' + apikey)).json()
    return summonerInfo, "id" in summonerInfo
async def addPlayer(userName,id,pos1,pos2,message):
    leagueInfo = ((requests.get('https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/' + id + '?api_key=' + apikey)).json())[0]
    players[userName] = (pos1, pos2, tier_score[leagueInfo['tier']] + rank_score[leagueInfo['rank']])
    await message.channel.send(f'```Player {userName} successfully JOINED!\n# of Currently joined players: {len(players)}```')

async def positionCheck(input1,input2,message):
    if input1 == input2:
        await message.channel.send('```Please input 2 different positions!\nposition available: top, jg, mid, adc, sup```')
        return False
    if not(input1 in positions and input2 in positions):
        await message.channel.send('```Invalid position!\nposition available: top, jg, mid, adc, sup```')
        return False
    return True

server = {} #들어가는 내용물  - > 서버 이름: [teams, unsassigned, numTeams]
teams = [{},{}] #name and score
unassigned = [] #only name

sorted_players = sorted(players.items(), key=lambda x:x[1][2], reverse=False)


def position_assign_one_p(player,teams):
    preference = player[1][0:2]
    score = player[1][2]
    name = player[0]
    if (preference[0] in teams[0]):
        if (preference[0] in teams[1]):
            if(preference[1] in teams[0]):
                if(preference[1] in teams[1]):
                    unassigned.append([name, score])
                else :
                    teams[1][preference[1]] = [name, score]
            else :
                teams[0][preference[1]] = [name, score]
        else :
            teams[1][preference[0]] = [name, score]
    else :
        teams[0][preference[0]] = [name, score]

#put unassinged ppl to teams
def assign_unassigned(person,teams):
    team0_len = len(teams[0])
    team0_score = 0
    for key in teams[0]:
        team0_score += teams[0][key][1]             
    team1_len = len(teams[1])
    team1_score = 0
    for key in teams[1]:
        team1_score += teams[1][key][1]     
    
    if team0_len == 5:
        for position in positions :
            if not position in teams[1]:
                teams[1][position] = person
                return
    elif team1_len == 5:
        for position in positions :
            if not position in teams[0]:
                teams[0][position] = person
                return    
    else :
        if team0_score > team1_score :
            for position in positions :
                if not position in teams[1]:
                    teams[1][position] = person
                    return
        else :
            for position in positions :
                if not position in teams[0]:
                    teams[0][position] = person
                    return 
            
#adjust score btw teams
def adjust_score(teams):
    
    if len(teams[0]) != 5 or len(teams[1]) !=5: #--> need to warning in the end :: FIXME HAN        
        print ("not enough players")
        return False
    team0_score = 0
    for key in teams[0]:
        team0_score += teams[0][key][1]
    team1_score = 0
    for key in teams[1]:
        team1_score += teams[1][key][1]
    score_diff = team0_score - team1_score
    diff_mul = score_diff*2//abs(score_diff)
    position_diff = []
    for position in positions :
        position_diff.append([position, diff_mul*(teams[0][position][1] - teams[1][position][1])])
    position_diff.sort(key = lambda x:x[1], reverse=True)
    for position in position_diff:
        if (position[1] > 0) and (position[1] < abs(score_diff)) :
            tmp = teams[0][position[0]]
            teams[0][position[0]] = teams[1][position[0]]
            teams[1][position[0]] = tmp
            print(f"adjustment: {teams[0][position[0]]} <-> {teams[1][position[0]]}")
            return True
    
    print(f"NO FURTHER IMPROVEMENT AVAILABLE")
    return False





client = discord.Client()
numargs = 0
try:
    f = open("profiles.txt",'r')
    readFile = f.read().split()
    f.close()
    for i in range(len(readFile)//4):
        j = i * 4
        profiles[readFile[j]] = (readFile[j+1],readFile[j+2],readFile[j+3])
    del readFile
    del f    
except IOError:
    print("Profile does not exist.")

#when the client is connected -> happened 
@client.event
async def on_ready():
    #print(f'{client.user} has connected to Discord!')
    for guild in client.guilds:
        print(GUILD)
        print(apikey)
        if guild.name != GUILD:
            break

        print(
            f'{client.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})\n'
        )
        
@client.event
async def on_message(message):
    
    if message.author == client.user:
        return
    discordName = str(message.author)
    inputMessage = message.content;
    if message.content.startswith('!test'):
        await message.channel.send('Hello world!')
    elif inputMessage == "!load":
        if not str(message.author) in admins:
            await message.channel.send('INVALID ATTEMPT')
            return
        
        
    elif inputMessage == "!save":
        if not str(message.author) in admins:
            await message.channel.send('INVALID ATTEMPT')
            return
        f = open("profiles.txt", "w")
        for i in profiles.keys():
            f.write(f"{i} {profiles[i][0]} {profiles[i][1]} {profiles[i][2]}\n")
        f.close()
        
    elif inputMessage == "!forcequit":
        if not str(message.author) in admins:
            await message.channel.send('INVALID ATTEMPT')
            return
        quit()
        
    elif inputMessage == "!종료":
        if not str(message.author) in admins:
            await message.channel.send('INVALID ATTEMPT')
            return
        f = open("profiles.txt", "w")
        for i in profiles.keys():
            f.write(f"{i} {profiles[i][0]} {profiles[i][1]} {profiles[i][2]}\n")
        f.close()
        quit()
        
    #listing current players
    elif inputMessage == "!list":
        sorted_players = sorted(players.items(), key=lambda x:x[1][2], reverse=False)
        if (len(players) != 0) :
            await message.channel.send(sorted_players)
        else :
            await message.channel.send("No players")            
        return
    #manual
    elif inputMessage == "!help":
        await message.channel.send('1. !test')
        await message.channel.send('2. !list')
        await message.channel.send('3. !join <username> <1st position> <2nd position>')
        await message.channel.send('4. !leave <username>')
        await message.channel.send('5. !help')
        await message.channel.send('6. !maketeam-rank')

    #SET TEAM NUMBERS
    elif inputMessage.startswith('!NumberOfTeams'):
        inputSegment = inputMessage.split()
        if(inputSegment[-1].isnumeric()):
            numTeams = inputSegment[-1]
            
            await message.channel.send(f"Successfully updated the number of players to:{numTeams}")
            return

##############################################################################################################
    #MAKE TEAMS WITH RANKS
    elif inputMessage.startswith('!maketeam-rank'):

            
        teams = [{},{}]
        teams[0],teams[1] = initAssignment(players)
        print (teams[0])
        print("init value-----------")

        print(f"{teams[0]} - total = {teamScore(teams[0])}")
        print(f"{teams[1]} - total = {teamScore(teams[1])}")
        print("diff in teams:", abs(teamScore(teams[0]) - teamScore(teams[1])))
        scoreGained = 99
        limitCounter = 100
        while(scoreGained != 0 and limitCounter > 0):
            teams[0],teams[1],scoreGained = tryOpt(teams[0],teams[1])
            limitCounter -= 1
        print("value after opt-----------")
        print("diff in teams:", abs(teamScore(teams[0]) - teamScore(teams[1])))
        #await message.channel.send(f"team1 = {team1}")
        print_str = "**Team 1:**\n```"
        for index,key in enumerate(teams[0].keys()):
            print_str += f"\t{index+1}. \t{key}\n"
        print_str += "```"
        await message.channel.send(print_str)
        print_str = "**Team 2:**\n```"
        for index,key in enumerate(teams[1].keys()):
            #print (f"\t{index}. \t{key}\n")
            print_str += f"\t{index+1}. \t{key}\n"
        print_str += "```"
        await message.channel.send(print_str)
        #await message.channel.send(f"team1 = {list(team1.keys())}")
        #await message.channel.send(f"team2 = {list(team2.keys())}")
        await message.channel.send(f"diff in teams: {abs(teamScore(teams[0]) - teamScore(teams[1]))}")



    # MAKE TEAM WITH POSITOIONS
    elif inputMessage.startswith('!maketeam-position'):
        teams = [{},{}]
        if len(players) != 10:
            await message.channel.send("player number is not enough")
            #return
        sorted_players = sorted(players.items(), key=lambda x:x[1][2], reverse=False)
        print(sorted_players)
        for player in sorted_players :
            position_assign_one_p(player,teams)
        for person in unassigned :
            assign_unassigned(person,teams)
        for i in range(10) :
            print("ADJUSTMENT IS BEING MADE")
            if not adjust_score(teams):
                break
        #await message.channel.send(f"team1 = {teams[0]}")
        #await message.channel.send(f"team2 = {teams[1]}")
        
        print (teams[0])
        print (teams[1])
        print_dict = {}
        print_str = "**Team 1:**\n```"
        team0_score = 0
        for key in positions:
            team0_score += teams[0][key][1]
            print_dict[key] = teams[0][key][0]
            print_str += f"\t{key.upper()}: \t{teams[0][key][0]}\n"
        print_str += "```"
        await message.channel.send(print_str)
        team1_score = 0
        print_str = "**Team 2:**\n```"
        for key in positions:
            team1_score += teams[1][key][1]
            print_str += f"\t{key.upper()}: \t{teams[1][key][0]}\n"
        print_str += "```"
        await message.channel.send(print_str)
        await message.channel.send(f"diff in teams: {abs( team0_score- team1_score)}")
###############################################################################################################
        
    #참가 스크립트
    elif inputMessage.startswith('!참가'):
        joinText = inputMessage.split()
        if len(joinText) == 1 and discordName in profiles:
            userName = profiles[discordName][0]
            SummonerInfo,found = getSummonerInfo(userName)
            await addPlayer(userName,SummonerInfo['id'],profiles[discordName][1],profiles[discordName][2],message)
            return
        elif len(joinText) < 4:
            await message.channel.send('!참가 <username> <1st position> <2nd position>')
            await message.channel.send('position available: top, jg, mid, adc, sup')
            return
        if not await positionCheck(joinText[-1],joinText[-2],message):
            return   

        userName = "".join(joinText[1:-2])
        userName = userName.lower()
        print(f"Current User name:'{userName}'")
        SummonerInfo, found = getSummonerInfo(userName)
        if not found:
            await message.channel.send(f'```User name {userName} was NOT found!\nPlease check the name again!```')
            return
        if userName in players:
            await message.channel.send(f'```{userName} is already joined!```')
            return
        await addPlayer(userName,SummonerInfo['id'],joinText[-2], joinText[-1],message)
        return
        
    #퇴장 스크립트
    elif inputMessage.startswith('!leave'):
        leaveText = inputMessage.split()
        if len(leaveText) < 2:
            await message.channel.send('```!leave <username>```')
            return
        userName = "".join(leaveText[1:])
        userName = userName.lower()
        if userName in players.keys():
            players.pop(userName)
            await message.channel.send(f'```Player {userName} successfully LEFT!\n# of Currently joined players: {len(players)}```')

##################################################################################################################################
    #Profile script
    elif inputMessage.startswith('!profile'):
        profileText = inputMessage.split()
        if len(profileText) < 2:
            await message.channel.send('```!profile <(update userName position1 position2) / (check)>```')
            return
    
        #profile check
        if profileText[1] == "check":
            if discordName in profiles:
                await message.channel.send(f"{discordName}'s info:\n```In Game Name: {profiles[discordName][0]}\nPrimary Role: {profiles[discordName][1]}, Secondary Role: {profiles[discordName][2]}```")
            else:                
                await message.channel.send(f"```{discordName}'s profile does NOT exist```")
            return
        



        #profile add
        elif profileText[1] == "update":
            if len(profileText) < 5:
                await message.channel.send('```!profile <update userName position1 position2>```')
                return

            if not await positionCheck(profileText[-1],profileText[-2],message):
                return

            userName = "".join(profileText[2:-2])
            userName = userName.lower()      
            SummonerInfo, found = getSummonerInfo(userName)
            if not found:
                await message.channel.send(f'```User name {userName} was NOT found!\nPlease check the name again!```')
                return
            profiles[discordName] = (userName,profileText[-2],profileText[-1])
            print(profiles)
            await message.channel.send(f"```{discordName}'s profile has been updated!```")
            return
           
        

client.run(TOKEN)
