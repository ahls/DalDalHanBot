import random
import cassiopeia as cass
import os
apikey = os.getenv('API_KEY')

cass.set_riot_api_key(apikey)  # This overrides the value set in your configuration/settings.
cass.set_default_region("NA")

champions = cass.get_champions()
number_random_champion = int(input('Enter how many champions you want to pick as random: '))

for get_random_champion in range (number_random_champion):
    random_champion = random.choice(champions)
    print(str(get_random_champion+1) + ". {name}.".format(name=random_champion.name))

