import time

# Define dialogue between Shrek and Donkey
dialogue = [
    ("Shrek", "What are you doing in my swamp?"),
    ("Donkey", "Oh, come on, Shrek, you don't mean that."),
    ("Shrek", "Yes, I do! I'm an ogre! Ogres are like onions."),
    ("Donkey", "They stink?"),
    ("Shrek", "Yes. No!"),
    ("Donkey", "Oh, they make you cry."),
    ("Shrek", "No!"),
    ("Donkey", "Oh, you leave them out in the sun, they get all brown, start sprouting little white hairs."),
    ("Shrek", "No! Layers! Onions have layers. Ogres have layers. Onions have layers. You get it? We both have layers."),
    ("Donkey", "Oh, you both have layers. Oh. You know, not everybody likes onions."),
    ("Shrek", "Cake! Everybody loves cakes! Cakes have layers."),
    ("Donkey", "I don't care what everyone likes! Ogres are not like cakes."),
    ("Shrek", "You know what else everybody likes? Parfaits. Have you ever met a person, you say, 'Let's get some parfait,' they say, 'Hell no, I don't like no parfait'? Parfaits are delicious."),
    ("Donkey", "I don't care! Ogres are like onions! End of story! Bye-bye! See you later."),
    ("Donkey", "Parfaits may be the most delicious thing on the whole damn planet."),
]

# Function to print the dialogue with pauses
def print_dialogue(dialogue, delay=20):
    for character, line in dialogue:
        print(f"{character}: {line}")
        time.sleep(delay)

# Execute the dialogue printing
print_dialogue(dialogue)
