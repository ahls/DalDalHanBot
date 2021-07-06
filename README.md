## Introduction
DALDALHAN bot, a discord bot, is for making teams in case to have more than 10 people to hang out in League of Legends. This bot can make teams by using 1. only rank in league, and 2. care about preference position and rank.
DALDALHAN Bot is a Discord bot designed to help users in the server form teams to play League of Legends. When making the teams, DALDALHAN Bot will try to balance the team for a fair match by gathering rank information from the Riot API, and the user can specify one of the two priorities: (1)team's total score balance and (2)preferred position.
In addition to the team making commands, the bot has few other helpful commands such as creating a profile for easier use of the bot and the ‘help’ command to see the possible commands list. It also has a random text generator for fun.

## Example scenario
Here are two cases to make teams of 10 people.

  Player 1: Silver 1 mid, top
  Player 2: Silver 1 jg, top
  Player 3: Gold 4 mid, top
  Player 4: Gold 4 top, jg
  Player 5: Gold 3 mid, top
  Player 6: Gold 3 jg, mid
  Player 7: Platinum 4 top, jg
  Player 8: Platinum 4 adc, top
  Player 9: Platinum 2 mid, sup
  Player 10: Diamond 3 top, jg

Case 1. Care only for Rank
Team 1:
    1.     Player 1
    2.     Player 7
    3.     Player 3
    4.     Player 10
    5.     Player 4
Team 2:
    1.     Player 6
    2.     Player 2
    3.     Player 9
    4.     Player 8
    5.     Player 5
diff in teams: 0

Case 2. Care preference position and rank
Team 1:
    TOP:     Player 3
     JG:     Player 2
    MID:     Player 1
    ADC:     Player 8
    SUP:     Player 9
Team 2:
    TOP:     Player 4
     JG:     Player 6
    MID:     Player 5
    ADC:     Player 7
    SUP:     Player 10
diff in teams: 2

## Instructions
Requirements:
Python 3.6.9 version
A file named “.env” in the same directory.
Setup:
Clone this repository.
Fill out the “.env” file as following:

DISCORD_TOKEN="token given by discord"
DISCORD_GUILD=["Server name you want to allow to use this bot"]
API_KEY="API_KEY from Riot Developer website"
Run the bot.py script
When the console displays connected servers, the bot is ready to be used.


## To Make Teams:
Desired participants can join using “!참가” or “!join”, followed by a few attributes:
!(참가 or join) <InGameName> <1stPosition> <2ndPosition>
or simply !(참가 or join) if a profile has been created for the user.
Set the Number of teams participating in the custom using the following command:
!NumberOfTeams <desiredNumber>
It is set to 2 by default.
Make the teams, use the following command:
!make <priority>
priority maybe be either: “rank” or “position”

## To Make a Profile:
To create/update the profile, the user may use the following command:
!profile update <InGameName> <1stPosition> <2ndPosition>
Although the profile update command validates if the given inputs are correct, the user can still check the profile with the following command:
!profile check

