# bot.py
import os
import discord
import requests
import random
import asyncio
from enum import Enum
from dotenv import load_dotenv
import cassiopeia as cass
import pandas as pd
import numpy as np
#df = pd.read_excel(r'fight.xlsx')
rankValueSheet = np.genfromtxt("fight.csv",delimiter = ',')
#print(rankValueSheet)

class server:
    def __init__(self):
        self.players = {}
        self.team = [{},{}]
        self.numTeams = 2
        self.unassigned = []
        self.server = 'na1'
        self.teamsFSM = {}
        self.remain_dic = {}
        self.currentLeader = ''

def teamScore(dic):
    total = 0
    for i in dic.keys():
        total += dic[i][2]
    return total

def initAssignment(givenList):
    team1 = {}
    team2 = {}
    team1Score = team2Score = 0;    
    #print (givenList)
    #print (givenList.keys())
    for i in givenList.keys():
        #print (givenList[i][2])
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

def initAssignment3(givenList):
    #WORKING ON THIS HAN
    team1 = {}
    team2 = {}
    team3 = {}
    team1Score = team2Score = team3Score = 0;    
    #print (givenList)
    #print (givenList.keys())
    for index, i in enumerate(givenList.keys()):
        if index%3 == 0:
            team1[i] = givenList[i]
            team1Score += givenList[i][2]
        elif index%3 == 1:
            team2[i] = givenList[i]
            team2Score += givenList[i][2]
        elif index%3 == 2:
            team3[i] = givenList[i]
            team3Score += givenList[i][2]        #print (givenList[i][2])
    return team1, team2, team3

def tryOpt3(team1,team2,team3):
    #WORKING ON THIS HAN
    team1Score = teamScore(team1)
    team2Score = teamScore(team2)
    team3Score = teamScore(team3)

    over_avg = []
    right_avg = []
    under_avg = []

    totalScore = team1Score + team2Score + team3Score

    allteam = {"0":[team1, totalScore - 3*team1Score], "1":[team2, totalScore - 3*team2Score], "2":[team3, totalScore - 3*team3Score]}

    #0 means team1, 1 means team2, 2 means team3
    if (totalScore - 3*team1Score) < 0:
        over_avg.append("0")
    elif (totalScore - 3*team1Score) == 0:
        right_avg.append("0")
    elif (totalScore - 3*team1Score) > 0:
        under_avg.append("0")

    if (totalScore - 3*team2Score) < 0:
        over_avg.append("1")
    elif (totalScore - 3*team2Score) == 0:
        right_avg.append("1")
    elif (totalScore - 3*team2Score) > 0:
        under_avg.append("1")

    if (totalScore - 3*team3Score) < 0:
        over_avg.append("2")
    elif (totalScore - 3*team3Score) == 0:
        right_avg.append("2")
    elif (totalScore - 3*team3Score) > 0:
        under_avg.append("2")

    if (team1Score == team2Score) and (team1Score == team3Score):
        return team1, team2, team3

    #FIXME: Now need to calculation in this for loop
    for overteam in over_avg:
        for underteam in under_avg:
            bestDiff = 99
            bestMember1 = -1
            bestMember2 = -1
            for member1 in (allteam[overteam][0].keys()):
                for  member2 in (allteam[underteam][0].keys()):
                    if abs(allteam[overteam][1]) >= abs(allteam[underteam][1]):
                        diff = abs(allteam[underteam][1])
                    else:
                        diff = abs(allteam[overteam][1])
                    tempDiff = abs(diff - 2 * ( allteam[overteam][0][member1][2] - allteam[underteam][0][member2][2]))
                    if tempDiff < bestDiff :
                        print ("this")
                        print (tempDiff)
                        print (bestDiff)
                        bestDiff = tempDiff
                        bestMember1 = member1
                        bestMember2 = member2
            if(bestMember1 != -1 and bestMember2 != -1):   
                allteam[underteam][0][bestMember1]= allteam[overteam][0][bestMember1]
                allteam[overteam][0][bestMember2]= allteam[underteam][0][bestMember2]
                allteam[underteam][0].pop(bestMember2)
                allteam[overteam][0].pop(bestMember1)
        
    return team1,team2,team3

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

def getSummonerInfo(userName,gameServer):
    summonerInfo = (requests.get('https://'+gameServer+'.api.riotgames.com/lol/summoner/v4/summoners/by-name/' + userName + '?api_key=' + apikey)).json()
    return summonerInfo, "id" in summonerInfo
async def addPlayer(userName,id,pos1,pos2,message,playerPool,gameServer):
    data = ((requests.get('https://'+gameServer+'.api.riotgames.com/lol/league/v4/entries/by-summoner/' + id + '?api_key=' + apikey)).json())
    leagueInfo = [{ k:v for (k, v) in i.items()} for i in data if i.get('queueType') == 'RANKED_SOLO_5x5']

    printrank = leagueInfo[0]['rank']
    printtier = leagueInfo[0]['tier']
    playerPool[userName] = (pos1, pos2, 
        rankValueSheet[ rank_score[leagueInfo[0]['rank']]][tier_score[leagueInfo[0]['tier']]])
    await message.channel.send(f'```Player {userName} successfully JOINED! (Tier: {printtier}, Rank: {printrank})\n# of Currently joined players: {len(playerPool)}```')

async def positionCheck(input1,input2,message):
    if input1 == input2:
        await message.channel.send('```Please input 2 different positions!\nposition available: top, jg, mid, adc, sup```')
        return False
    if not(input1 in positions and input2 in positions):
        await message.channel.send('```Invalid position!\nposition available: top, jg, mid, adc, sup```')
        return False
    return True
    
def position_assign_one_p(player,teams,unassigned):
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
        #print ("not enough players")
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
            #print(f"adjustment: {teams[0][position[0]]} <-> {teams[1][position[0]]}")
            return True
    
    #print(f"NO FURTHER IMPROVEMENT AVAILABLE")
    return False
    
    
load_dotenv()
#봇 연결에 필요한 정보
TOKEN = os.environ['DISCORD_TOKEN']
GUILD = os.environ['DISCORD_GUILD']
apikey = os.environ['API_KEY']

print (TOKEN)
print (GUILD)
print (apikey)
#게임 참가에 쓰이는 정보
admins = {"Han#6098","sinnamon#9618"}
positions = ("top","jg","mid","adc","sup")
possibleServers = ("br1", "eun1", 'euw1', 'jp1', 'kr', 'la1','la2', 'na1', 'oc1', 'ru', 'tr1')
tier_score = {"IRON": 0, "BRONZE": 1, "SILVER": 2, "GOLD": 3, "PLATINUM": 4, "DIAMOND": 5, "MASTER": 6, "GRANDMASTER": 7, "CHALLENGER": 8}
rank_score = {"I":3, "II":2, "III":1, "IV":0}
#"플레이어 이름" : 포지션1, 포지션2, 총 랭크 점수
profiles = {} #"디스코드 이름: 게임내 이름, 포지션 1, 포지션 2"
numTeams = 2

servers = {} #들어가는 내용물  - > 서버 이름: [teams, unsassigned, numTeams]

#재미로 넣은거
property = ["각잡힌","정상적인","심술궃은","깔끔한","깨끗한","주름접힌", "주름없는","완전 새 것같은", "오래된","녹슨","빛바랜","괴이한","기괴한","금속재질의","아이언의","단단한","부드러운","굳센","유연한","챌린져의","브론즈의", "거대한","날카로운","위협적인","더러운","아름다운", "", "훌륭한", "멋진", "때가 낀", "어두운", "밝은", "뜨거운", "차가운", "길다란", "찰랑거리는", "엄청난", "작은", "귀여운", "못생긴"]
soundProp = ["짧은", "큰", "알수없는", "듣기 거북한", "분노에 찬", "끔찍한", "엄청난", "형용할 수 없는", "구슬픈", "조그만", "한에 찬", "서러운"]
element = ("불의", "얼음", "비전", "전설의", "소멸", "화염")
weapon = ["둔기를","쇠빠따를","꽉 쥔 주먹을", "젓가락을","중지를", "새끼 손가락을", "십자가를", "갓 담근 김치를", "엘보를", "니킥을", "똥덩어리를", "연양갱을", "손끝을", "식칼을", "장미칼을", "짱돌을", "쇠파이프를","각목을"]
body = ["명치에","관자놀이에","7번 척추뼈에","면상에","급소에", "인중에", "어깨에", "정강이에", "무릎에", "마빡에", "이마에"]
method = ["개 쌔게 갈겼다.","휘둘렀다.", "내던졌다.", "후려쳤다", "정확히 찔렀다.", "터치했다.", "가볍게 문질렀다."]
how = ["이상한 소리를 내며 " , "" ,"괴상한 자세로 ", "멋진 포즈와 함께 ", "눈물을 머금고 ", "분노에 가득차 ", "신이나서 ", "콧노래를 부르며 ", "찡찡대며 ", f"{random.choice(soundProp)} 휘파람을 부르며"]
who = ["지나가던 개가", "당신이", "당신의 교수님이", "모든 것을 지켜보던 개발자가", "교장선생님이", "마트 아저씨가", "버스 운전기사가", "경찰아저씨가", "대통령이", "대마왕이", "철수가", "영희가", "철수와 영희가", "반 친구가", "유명 스트리머가", "건물주가", "백만장자가", "일론 머스크가", "외계인이", "누렁이가", "황소가" , "원숭이가", "개구리가", "뱁새가", "엔지니어가", "상담사가", "범죄자가", "다리우스가", "드레이븐이", "마이스터 이가", "티모가"]
feature = ["눈매를 ","마음씨를 ", "얼굴을 ", "손을 ", "손톱을 ", "발톱을 ", "머리칼을 ", "심장을 ", "뇌를 ", "어깨를 ", "무릎을 ", "팔꿈치를 ", "이마를 "]
describedFeature = f"{property[random.randrange(25)]} {feature[random.randrange(13)]}"
featureEnding = ["소유한", "빼고 다 가진", "가지지 못한", "지닌", "가지고 있는", "보유한", "제외하고 자랑할게 없는", "자랑스럽게 생각하는"]
featureJoins = [" 지녔으며 "," 가지고 있으며 ", " 소유했으며 ", " 가지진 못했지만 "," 보유했으며 ", " 가졌고 ", " 소유했고 ", " 탑재한 "]
groups = ["중국 공안당에게", "FBI에게", "러시아 경찰에게","경찰에게", "성난 사람들에게", "무서운 형들에게", "무서운 언니들에게", "화가 잔뜩난 부모님에게"]
beginning = [f"{random.choice(element)} 마법 주문을 외우자,", f"{random.choice(property)} {random.choice(weapon)} 달달한 봇의 {random.choice(body)} {random.choice(method)}.", "강렬한 눈빛으로 달달한 봇을 바라봤고,", "명령을 하자,", "힘을 방출하자,", "심한 욕을 하자,", "속사포 랩을 내뱉자,"]
reaction = [f"{random.choice(soundProp)} 소리를 지르며", f"{random.choice(soundProp)} 단말마와 함께", "소리조차 지르지 못하고", f"당신에게 {random.choice(soundProp)} 저주를 퍼부으며", f"{random.choice(soundProp)} 소리로 울부짖으며",  f"{random.choice(property)} 자세를 취하며", "온몸이 뒤틀리며"]
ending = ["사라졌다.","원자 단위로 분해되었다.", "쓰러졌다.", "바스라졌다.", "먼지가 되었다.", "무지개 다리를 건넜다." , "사망했다.","성불했다.", "분쇄되었다.", "신비해졌다.", f"{random.choice(groups)} 잡혀갔다.", "모두의 기억속에서 잊혀졌다.", "눈물을 흘렸다.", "울었다." , "엄마에게 이르러 갔다.", "도망갔다.", "후퇴했다.", "몸을 웅크렸다.", "퍼엉 하고 터졌다.", "폭발했다.", "서렌을 쳤다."]
propertyLen = len(property)
featureLen = len(feature)
selfHate = ["정체성이 혼란한","자기 혐오에 빠진", "자아를 잃어버린", "쉐도우 복싱에 심취한", "정신이 오락가락하는", "잠이 덜깬", "거울에 비친 자신의 모습을 본", "폰 액정에 반사된 자신의 얼굴을 본"]
explainBattle = ["기나긴 혈투 끝에", "몇번의 합을 겨룬 후", "단숨에", "눈 깜짝할 사이에", f"약 {random.randrange(0,1000)}초 후,", "반격의 반격을 거듭한 끝에"] 
victory = ["{victor}(은)는 {defeated}에게 패배가 무엇인지 알려주었다.", "{victor}(은)는 {defeated}에게 인생의 쓴맛을 보여주었다.", "{victor}(은)는 {defeated}에게 굴욕감을 주었다.", "{victor}(은)는 {defeated}을 산산조각 냈다.",  "{victor}의 손에 의해 {defeated}(이)가 쓰러졌다.", "{defeated}(이)가 {victor}에게 패배를 인정했다.", "{defeated}(이)가 {victor}에게 항복을 선언했다.", "{victor}(이)가 {defeated}의 울음보를 터트렸다.","{defeated}의 자존감은 {victor}에 의해 박살났다."]
dagul = ["호기롭게", "바보같이", "멍청하게", "용맹하게"]
joiningWords = ["그리고", "그 뒤,", "둘은 잠시 숨을 고르고", "그 찰나에"]
def conjoinFeatures():
    numba = random.randrange(4)
    if(numba == 0):
        textToReturn = random.choice(property)
        return textToReturn
    textToReturn = f"{property[random.randrange(propertyLen)]} {feature[random.randrange(featureLen)]}"

    while numba < 2:
        textToReturn += featureJoins[random.randrange(8)]
        if numba == 1:
            textToReturn += random.choice(property)
            return textToReturn
        textToReturn += f"{property[random.randrange(propertyLen)]} {feature[random.randrange(featureLen)]}"
        numba = random.randrange(4)
        
            
    textToReturn += random.choice(featureEnding)
    return textToReturn

battleBegin = [f"야생의 {conjoinFeatures()}{{init}} 이 풀숲에서 튀어나와 {conjoinFeatures()}{{target}}(을)를 공격하였다!", f"{conjoinFeatures()}{{init}}(은)는 끼고 있던 장갑을 {conjoinFeatures()}{{target}}의 {random.choice(property)}{random.choice(body)} 던졌다.", f"{conjoinFeatures()} {{init}}(이)가 {conjoinFeatures()} {{target}}에게 {random.choice(soundProp)} 욕을 했고, 둘은 싸움을 시작했다.", f"{conjoinFeatures()}{{init}}이 {conjoinFeatures()}{{target}} 에게 정정당당한 승부를 요청했다."]




client = discord.Client()
numargs = 0


#프로파일 불러읽음
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
    print(f'{client.user} has connected to Discord!')
    print(f"Allowed servers: {GUILD}")
    for guild in client.guilds:
    
        print(guild.name)
        servers[guild.name] = server()
        print("Was added to the servers list")
        if not guild.name in GUILD:
            print("being broken")
            break

        print(
            f'{client.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})\n'
        )
        
        
#####################################
###### 커맨드 부분 여기서 부터 시작 ##########
#####################################
@client.event
async def on_message(message):
    
    if message.author == client.user:
        return
    discordName = str(message.author)
    inputMessage = message.content;
    currentServer = servers[message.guild.name]
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
        
    elif inputMessage == "!ㅂㅂ":
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
        sorted_players = sorted(currentServer.players.items(), key=lambda x:x[1][2], reverse=False)
        if (len(currentServer.players) != 0) :
            await message.channel.send(sorted_players)
        else :
            await message.channel.send("No players")            
        return
    #manual
    elif inputMessage == "!help":
        text = \
"Game Related:\n```\
1. !참가 or join <username> <1st position> <2nd position>\n   (if has profile is made) !참가\n\
2. !leave <username>\n\
3. !flush (only available for Admins)\n\
4. !NumberOfTeams <number of teams>\n\
5. !set_server <br1, eun1, euw1, jp1, kr, la1,la2, na1, oc1, ru, tr1>\n\
6. !make <\"position\" or \"rank\">\n\
7. !team-lead leader <first leader-discord name-> <second leader-discord name->\n\
8. !team-lead select <player-league user name->```\
Profile Related```\
1. !profile update <username> <1st position> <2nd positions>\n\
2. !profile check```\
Other```\
1. !결투 <empty or @mention>\n\
2. !random-pick <number of random champions>\n\
3. !credit\n\
4. !checkrole```\
Debugging```\
1. !test\n\
2. !list\n\
3. !ㅂㅂ or !quit```"

        await message.channel.send(text)
##############################################################################################################
    #MAKE RANDOM PICK
    elif inputMessage.startswith('!random-pick'):
        inputSegment = inputMessage.split()
        cass.set_riot_api_key(apikey)  # This overrides the value set in your configuration/settings.
        cass.set_default_region("NA")

        champions = cass.get_champions()
        number_random_champion = int(inputSegment[-1])
        random_champs = []

        while len(random_champs) < number_random_champion :
            random_champion = random.choice(champions)
            #print (random_champion)
            if not random_champion.name in random_champs : 
                random_champs.append(random_champion.name)
        #print (random_champs)
        await message.channel.send(f"{number_random_champion} random champ is\n```{random_champs}```")
        return
                
    #SET TEAM NUMBERS
    elif inputMessage.startswith('!NumberOfTeams'):
        inputSegment = inputMessage.split()
        if(inputSegment[-1].isnumeric()):
            currentServer.numTeams = inputSegment[-1]
            
            await message.channel.send(f"Successfully updated the number of players to:{currentServer.numTeams}")
            return
        else:
            await message.channel.send("Something was odd about that command! Check out !help command!")
            return
    
    elif inputMessage.startswith('!set_server'):
        inputSegment = inputMessage.split()
        if(inputSegment[-1] in possibleServers):
            currentServer.server = inputSegment[-1]
            
            await message.channel.send(f"Successfully updated the server to:{currentServer.server}")
            return
        else:
            await message.channel.send("Something was odd about that command! Check out !help command!")
            return
    
    elif inputMessage == "!checkServerName":
        await message.channel.send(f"current server's name is : {message.guild}")


##############################################################################################################
    #MAKE TEAMS WITH RANKS
    elif inputMessage =='!make rank':

        if len(currentServer.players) == 0:
            await message.channel.send(":thinking:\nWeird... Nobody, including yourself, wanted to play...")
            return
        elif len(currentServer.players) == 1:
            await message.channel.send(f"Nobody wanted to play with {discordName}...\nHow sad :cry:")
            return
     
        teams = [{},{}]
        teams[0],teams[1] = initAssignment(currentServer.players)
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
        if teamScore(teams[0]) - teamScore(teams[1]) > 0:
            #team 0 seems to winner
            await message.channel.send(f"Team 1 have the upper hand for {abs(teamScore(teams[0]) - teamScore(teams[1]))} points")
        elif teamScore(teams[0]) - teamScore(teams[1]) == 0:
            await message.channel.send(f"Team 1 and Team 2 has same score")
        elif teamScore(teams[0]) - teamScore(teams[1]) < 0:
            await message.channel.send(f"Team 2 have the upper hand for {abs(teamScore(teams[0]) - teamScore(teams[1]))} points")              
        #await message.channel.send(f"diff in teams: {abs(teamScore(teams[0]) - teamScore(teams[1]))}")

    elif inputMessage =='!make rank3':

        if len(currentServer.players) == 0:
            await message.channel.send(":thinking:\nWeird... Nobody, including yourself, wanted to play...")
            return
        elif len(currentServer.players) == 1:
            await message.channel.send(f"Nobody wanted to play with {discordName}...\nHow sad :cry:")
            return
        elif len(currentServer.players) == 2:
            await message.channel.send(f"!make rank3 is not allowed for two people :zany_face:")
            return 

        teams = [{},{},{}]
        #WORKING ON THIS HAN
        teams[0],teams[1],teams[2] = initAssignment3(currentServer.players)
        print (teams[0])
        print("init value-----------")

        print(f"{teams[0]} - total = {teamScore(teams[0])}")
        print(f"{teams[1]} - total = {teamScore(teams[1])}")
        print(f"{teams[2]} - total = {teamScore(teams[2])}")
        print(f"total score for teams: team1 = {teamScore(teams[0])}, team2 = {teamScore(teams[1])}, team3 = {teamScore(teams[2])}")
        #NEED TO WORK tryOpt3 thing
        #scoreGained = 99
        limitCounter = 50
        while(limitCounter > 0):
            #teams[0],teams[1],teams[2],scoreGained = tryOpt3(teams[0],teams[1],teams[2])
            teams[0],teams[1],teams[2] = tryOpt3(teams[0],teams[1],teams[2])
            limitCounter -= 1
        print("value after opt-----------")
        print(f"total score for teams: team1 = {teamScore(teams[0])}, team2 = {teamScore(teams[1])}, team3 = {teamScore(teams[2])}")
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
        print_str = "**Team 3:**\n```"
        for index,key in enumerate(teams[2].keys()):
            #print (f"\t{index}. \t{key}\n")
            print_str += f"\t{index+1}. \t{key}\n"
        print_str += "```"
        await message.channel.send(print_str)

        await message.channel.send(f"Team 1 score : {teamScore(teams[0])} points")
        await message.channel.send(f"Team 2 score : {teamScore(teams[1])} points")
        await message.channel.send(f"Team 3 score : {teamScore(teams[2])} points")



    # MAKE TEAM WITH POSITOIONS
    elif inputMessage == '!make position':
        teams = [{},{}]
        if len(currentServer.players) != numTeams * 5:
            await message.channel.send("Not enough players are available.")
            return
        sorted_players = sorted(currentServer.players.items(), key=lambda x:x[1][2], reverse=False)
        print(sorted_players)
        for player in sorted_players :
            position_assign_one_p(player,teams,currentServer.unassigned)
        for person in currentServer.unassigned :
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
            print_str += f"\t{key.upper():>3}: \t{teams[0][key][0]}\n"
        print_str += "```"
        await message.channel.send(print_str)
        team1_score = 0
        print_str = "**Team 2:**\n```"
        for key in positions:
            team1_score += teams[1][key][1]
            print_str += f"\t{key.upper():>3}: \t{teams[1][key][0]}\n"
        print_str += "```"
        await message.channel.send(print_str)
        await message.channel.send(f"diff in teams: {abs( team0_score- team1_score)}")

    elif inputMessage.startswith('!team-lead'):
        joinText = inputMessage.split() 
        if len(joinText) < 3:
            await message.channel.send('!team-lead leader <first leader-discord name-> <second leader-discord name->')
            await message.channel.send('!team-lead select <joiner-league user name->')
            return            

        if joinText[1] == 'leader':
            if len(message.mentions) != 2:
                await message.channel.send('only available for two teams')
                return

            currentServer.remain_dic = dict(sorted(currentServer.players.items(), key=lambda x:x[1][2], reverse=True))

            for mentioned in message.mentions:
                currentServer.teamsFSM[mentioned.name] = [0,]

            #make first team get the first shot
            currentServer.currentLeader = message.mentions[0].name

            await message.channel.send(f'select first player, {currentServer.currentLeader}')
            await message.channel.send(f'Available player list: {list(currentServer.remain_dic.keys())}')
        elif joinText[1] == 'select':
            key0,key1 = currentServer.teamsFSM.keys()
            val0 = currentServer.teamsFSM[key0]
            val1 = currentServer.teamsFSM[key1]

            selected_player = joinText[2:]
            selected_player_str = ' '.join([str(elem) for elem in selected_player])

            if (message.author.name != currentServer.currentLeader) : 
                await message.channel.send(f'You are not team leader, {message.author.name}')
                return              
            if (selected_player_str not in list(currentServer.remain_dic.keys() )) :
                #invalid username
                await message.channel.send(f'This player is not in the list. List: {list(currentServer.remain_dic.keys())}')
                return 
                
            #1. username need to insert to FSM, 2. score for the FSM should be added, 3. discord print      
            currentServer.teamsFSM[message.author.name].append(selected_player_str)
            currentServer.teamsFSM[message.author.name][0] += currentServer.remain_dic[selected_player_str][2] 
            currentServer.remain_dic.pop(selected_player_str) 
            await message.channel.send(f'player {selected_player_str} is added to fight team')
            await message.channel.send(f'Your team score: {currentServer.teamsFSM[message.author.name][0]}')

            if (currentServer.teamsFSM[key0][0] < currentServer.teamsFSM[key1][0]):
                currentServer.currentLeader = key0
            else:
                currentServer.currentLeader = key1

            if(currentServer.remain_dic == {}):
                await message.channel.send(f'No more selectable player')
                await message.channel.send(f'Team1 : Leader = {key0}, [Total Score, Member] = {val0}')
                await message.channel.send(f'Team2 : Leader = {key1}, [Total Score, Member] = {val1}')
                return

            await message.channel.send(f'Please select player, {currentServer.currentLeader}')
            await message.channel.send(f'Available player list: {list(currentServer.remain_dic.keys())}')

###############################################################################################################
        
    #참가 스크립트
    elif inputMessage.startswith('!참가') or inputMessage.startswith("!join"):
        joinText = inputMessage.split()     
        if len(joinText) == 1 and discordName in profiles:
            userName = profiles[discordName][0]
            SummonerInfo,found = getSummonerInfo(userName,currentServer.server)
            await addPlayer(userName,SummonerInfo['id'],profiles[discordName][1],profiles[discordName][2],message,currentServer.players,currentServer.server)
            return
        elif len(joinText) < 4:
            await message.channel.send('!참가 <username> <1st position> <2nd position>')
            await message.channel.send('position available: top, jg, mid, adc, sup')
            return
        if not await positionCheck(joinText[-1],joinText[-2],message):
            return   

        userName = "".join(joinText[1:-2])
        userName = userName.lower()
        #print(f"Current User name:'{userName}'")
        SummonerInfo, found = getSummonerInfo(userName,currentServer.server)
        if not found:
            await message.channel.send(f'```User name {userName} was NOT found!\nPlease check the name or this channel\'s server!!```')
            return
        if userName in currentServer.players:
            await message.channel.send(f'```{userName} is already joined!```')
            return
        await addPlayer(userName,SummonerInfo['id'],joinText[-2], joinText[-1],message,currentServer.players,currentServer.server)
        return
        
    #퇴장 스크립트
    elif inputMessage.startswith('!leave'):
        leaveText = inputMessage.split()
        if(inputMessage == "!leave"):
            if not discordName in profiles:
                await message.channel.send(f"```{discordName} does not have a profile made!```")
                await message.channel.send('```!leave <username>```')
                return
                
            elif profiles[discordName][0] in currentServer.players:
                currentServer.players.pop(profiles[discordName][0])
                await message.channel.send(f'```Player {profiles[discordName][0]} successfully LEFT!\n# of Currently joined players: {len(currentServer.players)}```')                
                return
            else:
                await message.channel.send(f"```Player {profiles[discordName][0]} didn't join yet.```")
                return

        userName = "".join(leaveText[1:])
        userName = userName.lower()
        if userName in currentServer.players:
            currentServer.players.pop(userName)
            await message.channel.send(f'```Player {userName} successfully LEFT!\n# of Currently joined players: {len(currentServer.players)}```')
        else:
            await message.channel.send(f'```Player {userName} does not exist!```')
        
    #flush/leave all
    elif inputMessage == '!flush':
        await message.channel.send('```starting to flush all players...```')
        if str(message.author) in admins:
            currentServer.players = {}
            await message.channel.send('```...all players are LEFT```')
        elif message.author.guild_permissions.administrator:
            currentServer.players = {}
            await message.channel.send('```...all players are LEFT```')
        else :
            await message.channel.send(f'```Only Admin can flush list```')       
     
    elif inputMessage == '!checkrole':
        if str(message.author) in admins:
            await message.channel.send(f'```{discordName} is developer```')
        elif message.author.guild_permissions.administrator:
            await message.channel.send(f'```{discordName} is admin```')
        else :
            await message.channel.send(f'```{discordName} is joiner```')

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
            SummonerInfo, found = getSummonerInfo(userName, currentServer.server)
            if not found:
                await message.channel.send(f'```User name {userName} was NOT found!\nPlease check the name again!```')
                return
            profiles[discordName] = (userName,profileText[-2],profileText[-1])
            #print(profiles)
            await message.channel.send(f"```{discordName}'s profile has been updated!```")
            return
           
##############################################################
        #기타 스크립트

    elif inputMessage.startswith('!credit'):
        await message.channel.send('```HAN: Art, Producing, Programming \nSinnamon: Programming```')        
        
    elif inputMessage == "!print chart":
        print(rankValueSheet)
        
    elif inputMessage.startswith("!결투"):
        
        if inputMessage == "!결투":
            text =f"{conjoinFeatures()} {random.choice(who)} {random.choice(how)}{random.choice(beginning)} 달달한 봇은 {random.choice(reaction)} {random.choice(ending)}"
            await message.channel.send(text)
        #누군가를 지목하면
        elif message.mentions:
            #print(len(message.mentions))    
            #자기 이름 써있으면 생기는 이벤트
            for mention in message.mentions:
                if mention == message.author:
                    text = f"{random.choice(selfHate)} {message.author.name}(이)가 자신을 공격했고, {random.choice(explainBattle)} {random.choice(victory).format(defeated = message.author.name)}."
                    await message.channel.send(text)
                    return
            #다굴 맞는 이벤트
            if len(message.mentions) > 1:
                text = f"{message.author.name}(이)가 {random.choice(dagul)} 다른 이들을 향해 달려 들었지만, 역시 다굴엔 장사가 없었다."
            #한명에게 결투
            elif (len(message.mentions) == 1):
                challenged = message.mentions[0].name
                text = random.choice(battleBegin).format(init = message.author.name,target = challenged)
                text += f" {random.choice(explainBattle)} "
                if random.randrange(2) == 1:
                    #승리
                    
                    text += random.choice(victory).format(victor = message.author.name,defeated = challenged)
                else:
                    #패배
                    text += random.choice(victory).format(victor = challenged,defeated = message.author.name)
                await message.channel.send(text)
        #누군가를 지목하지 못했을때
        else:
            text = f"{message.author.name}(은)는 누군가를 지목하여 결투를 하고싶었지만, 너무 긴장한 나머지 아무도 지목하지 못했다."
            await message.channel.send(text)
        
    
client.run(TOKEN)
