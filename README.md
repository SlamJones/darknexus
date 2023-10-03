# Diablo Clone

This file will act as both a README, and a Game Design  
Document.  In it, I will highlight the various features  
and functions of the game, both implemented and planned.  




## Summary / Purpose

This is a practice project, designed and created by  
Slam Jones, with the intention to practice general  
programming skills, problem solving skills, and game   
design principles.  

Based on how (reliatively) slow Python is at runtime,  
this project is unlikely to develop into a retail product,  
but the techniques and ideas generated here could be  
put to work in a potential retail product.  Due to this,  
target FPS (frames per second) is 30, rather than the  
more common 60 fps.  

Rather, its main function is to help me learn how to  
program effectively with tangible results, how to design  
and implement various game features such as: randomized  
loot, hit detection, mob spawning, changing maps, creating  
and displaying dialog trees with various possible player  
choices with varying results.  

Furthermore, the intention is to learn how to solve the  
many various programming problems that arise while  
undertaking such a task, with the overall intention of  
sharpening my game design and programming skills.  




## Story / Premise

Originally intended to be a clone of the old Blizzard ARPG  
'Diablo,' but with a few minor tweaks.  

Has since evolved to a slightly more unique premise:  

The player character is a salvage robot aboard a ship of  
humans.  The salvage crew finds a massive derelict alien  
space station and decides to send their robotic frontman  
(the player) inside to see what can be salvaged and sold  
for profit.  

The player soon discovers that all is not what it seems in  
the old derelict station, as they use an assortment of  
weapons and gadgets to destroy the various alien bugs,  
security robots, and mysterious sentient aliens that  
hamper the salvage crews progress.  

Playing as a robot amongst humans has the potential to  
open the door for philisophical quandries, such as the  
human crew asking each other if they think the robot  
(the player character) has free will, or wondering how  
the manner in which the player goes about their tasks  
reflects any level of humanity.  




## Player Controls  

Player controls the character using the mouse and keyboard.  
Basic movement control is done via either the Arrow Keys,  
or using WASD.  

Player uses weapon by clicking on the screen when a weapon  
is equipped.  Upon doing so, a projectile will be fired  
from the equipped weapon in the direction of the click.  
Player can pick up items from the ground, interact with  
NPCs, and possibly other interactions via the Enter key.  

Interacting with an NPC (usually a member of the players  
salvage ship crew) will bring up a dialog box, in which  
will appear a portrait of the NPC, their dialog, and  
a list of responses which the player can choose from.  
Different reponses often yield different reactions from  
the NPC.  


### Map Movement

When player moves the character: the character remains in  
place on the screen, and the map, and all objects on it  
(referred to as map objs) are moved around the character.  

To avoid confusion, there are three total sets of coords:  

'map x' and 'map y' refer to their position on the map.  

'screen x' and 'screen y' refer to where they are actually  
drawn on the screen at the present moment.  

'xy offset' refers to the difference between the two, and  
can be used to convert from one set to the other.  

Objects are evaluated as to their position on or off the  
screen, and only nearby objects are rendered on-screen.  

Objects are rendered at 1.5x screen size, so that they  
appear smoothly as they move into view.  This number can  
be adjusted based on lag caused by unnecessary drawn items.  

When a new map object is rendered, the player GUI is  
redrawn, so that it always appears above any other drawn  
items.  




## NPCs, Dialog

Potential for different crew reactions based on player  
actions.  If player frequently chooses to exterminate  
enemies that could be dealt with diplomatically, the crew  
will become more nervous around the player bot.  

Similarly, if the player chooses empathetic choices, the  
crew may wonder if there is some empathetic intelligence  
buried within the bots programming.  

Player may also be presented with options to speak in  
non-sequiters, which could convince the crew that the  
player bot is malfunctioning or otherwise glitched.  

Could potentially lead to philosophical or comedic  
converstaions amongst the human crewmembers.  




## Character XP, Leveling

Player character can gain xp from killing mobs, salvaging  
components, and other various tasks.  Gaining sufficient  
xp results in the character leveling up, which increases  
their stats and provides the player with 'stat points,'  
which the player can spend to increase specific stats  
even further.  

Player character is able to equip several pieces of armor,  
as well as a weapon, which will assist them in defeating  
any foes they encounter.  These items have properties  
which increase player stats.  Most pieces of armor will  
add to the armor rating stat, which reduces incoming  
damage by a flat % based on player and enemy levels, and  
total armor rating.  Weapons, naturally, increase the  
characters damage output.  




## Character Classes

Player is able to choose one of three options for their  
controlled robot:  


### The Heavy

Specializes in close-range weaponry, and mitigating  
incoming damage.  They are the 'tank' class:  
specializing in surviving incoming damage while dealing  
relatively low but consistent damage to enemies.  
Equivalent fantasy class is Warrior.  


### The Soldier

Specializes in long-range weaponry,  
and has several skills which affect their equipped weapon.  
Equivalent fantasy class is Ranger.  


### The Technomancer

Specializes in area-of-effect (AOE) weapons and high-tech  
gadgets.  They are the 'glass cannon' class: they deal  
lots of damage, but can be killed easily.  
Equivalent fantasy class is Wizard.  




## Basic (Reference) Stats

Basic Stats are used as reference points for player/mob  
power at specific levels.  Basic stats should increase by  
an average of 25% per level.  

Basic stats should lead to an average TTK (time-to-kill)  
of about 2 seconds for an average-level mob.  This can  
be adjusted to make fights slower and more tactical,  
or quicker and more action-y.  


### Mob Basic Stats:

At any given level, mobs of type should have approx stats:  

Weak Mobs: 25% basic stats  
Average Mobs: 50% basic stats  
Hard Mobs: 100% basic stats  
Mini-Boss: 150% basic stats  
Boss: 200%+ basic stats  

Note: Bosses and mini-bosses have health stacked higher than  
damage, to reduce chance of player being 1-hit killed,  
and to make bosses more bullet-spongy.  Also can be  
adjusted as needed to modify pacing of game or levels.  


### Hero Approximate Level Stats:

Hero is also bound to the Basic Reference stats, which,  
again, act as guidelines to keep difficulty scaling  
linearly as player progresses through the levels.  

No Gear: 50% basic stats  
Common Gear: 75% basic stats  
Uncommon Gear: 100% basic stats  
Rare: 125% basic stats  
Epic: 150% basic stats  
Legendary: 200%+ basic stats  




## Weaponry and Gear

Player may also be equipped with a default projectile  
weapon that is used when a weapon is not equipped.  

SLAP (Self-defence Light Attack Pistol) is a possible  
name.  
Very Low Damage, High Firerate, Low Range, High Accuracy  
Unlimited Ammo?  Or uses mana?  
Should allow player to escape from some situations;  
should not act as a main weapon.  
Some possible customizations?  But again, should never  
be so powerful that player uses it as their main weapon.  

All weapons use Ammo, which is a feature that I might  
remove since it doesn't add much to the player  
experience as a whole, other than inventory management.  


### Quickbar

(This function is not hooked up yet)  

Player has a row of quick actions, numbered 1 - 8.  
The intention is that player can assign various items,  
such as potions, scrolls/gadgets, skills, and weapons  
to these quick actions, which can then be called upon  
by pressing the corresponding key.  

Example: player sets Quick Action 1 to a specific Pistol.  
When pressing 1 on their keyboard, the player character  
will then switch to the Pistol item.  If the item  
referenced is not longer in the players inventory, or  
the item in not equipped, then the Quick Action reference  
will be removed.  


### Projectile Instructions / Recursion

Projectile system allows for recursion in projectiles:  
a projectile can spawn other projectiles based on  
instructions given from the weapon that spawned it.  

For example, a projectile with the "shatter" instruction,  
upon hitting an object, will spawn a "shotgun" type burst  
of pellets from the impact point.  The angle of spread,  
number of pellets, damage dealt, damage element, and many  
other parameters, including further instructions, can be  
specified.  


### Hit Boxes

Projectiles uses a hybrid of two types of hitbox detection:  

#### Projectile Hit Detection

Basic projectile hit detection checks the projectile against  
all possible hittable objects, including colliders,  
destroyables, and mobs.  The downside to this is, if a  
projectile is fast enough to completely bypass a collider,  
then no hit is detected.  

Example: a wall collider has a width of 50 pixels.  A weapon  
fired at the wall has a per-tick speed of 60 pixels.  There  
is a strong chance that the projectile will completely pass  
through the collider without triggering a collision event.  

#### Hitscan Hit Detection

To assuage this issue, I have also added a hitscan detection  
function.  It takes the start point and end point of a  
projectile and calculates if it hits anything between those  
two points.  

This allows projectiles to be nearly any speed while still  
allowing them to trigger collision events when passing through  
a collider, mob, or other object.  

The downside to the hitscan addition is that each projectile  
must conduct additional checks per tick, slowing the entire  
simulation down slightly.  The other issue is that the  
resultant 'explosion' image may not correctly match the edge  
of the collider, resulting in a projectile that appears to  
explode before it reaches the wall, even though it does not.  


### Weapon Types

There are many types of equippable weapons, including, but
not limited to:  

Pistols  
Submachine Guns (SMGs)  
Shotguns  
Assault Rifles  
Grenade Launchers  

And more exotic weapons, often class-specific such as:  

Ion Wave Cannons (hitscan cone AOE) for Heavy  
Railguns (hitscan, high passthru) for Soldier  
Arc Blasters (hitscan, chains to other nearby enemies),  
Plasma Cannons (high damage, slow movement speed, high  
passthru, explodes), for Technomancer.  




## Gear Modification/Enchantments

A weapon enchantment/modification system is planned, but  
the exact nature of it is not decided yet.  Possible  
options are:  

Diablo-style enchantments (Ex. Pistol of the Bat (+2 Dex))  

Borderlands-style randomized components (Heavy barrel  
gives +20% damage but -10% range)  

Or a different style of weapons randomization altogether.  


### Item Rarity 

This also ties into the common item rarity trope, where  
modified items have their rarities increased.  
 
No mods: Common  
1 Mod: Uncommon  
2 Mods: Rare  
3 Mods: Epic  
4 Mods: Legendary  
 
Epic and Legendary items may also have unique effects and  
modifiers not found in other items.  




## Damage Types

Damage types are planned but not implemented yet.  Exact  
resistances and vulnerabilities are dependant upon enemy  
species, the strengths listed are just general guidelines,  
and can be adjsuted to suit a specific enemy.  
 
Kinetic/Physical (Default damage type)  
Fire  (Strong vs Organic)  
Ice  (Strong vs Organic)  
Corrosive  (Strong vs Armor)  
Toxic (Strong vs Organic)  
Electric (Strong vs Robotic)  
EMP (V Strong vs Robotic)  




## Salvage (Gameplay Feature)

Salvaging gameplay should involve one or more mini-games,  
centered around safely disconnecting, removing, or  
otherwise acquiring bits of technology that can be  
studied, recycled, or used by the player and/or the NPC  
salvage crew.  

Several types of salvage mini-games are intended, and  
can be as simple as clicking several objects in the  
correct order, or could be established mini-games, such  
as Minesweeper- or Bejeweled-type mini-games.  




## Destroyables / Loot Boxes

Maps also contain 'destroyables,' which are generally  
loot-filled static objects that the player can shoot in  
order to reveal their contents.  Small Barrels, for  
example, tend to drop a couple coins, possible potions,  
ammo, and in some cases, a piece of armor or a weapon.  

Different types of destroyables yield different types  
and amounts of loot.  A Small Gear Locker, for example,  
won't have any coins or potions, but will always have  
a few pieces of gear (armor or weapons).  




## Assets

Most art assets used were generated by a free AI, which  
is the free version of Craiyon.com.  

Consequently, many of the images will have the Craiyon  
logo in the lower-right corner.  

Some art assests were hand-drawn by me in MS Paint.  

All art assets used are only rough approximations of  
the end product, and are subject to change as needed.  

No audio assets are in use, although it appears that  
Python has audio-related libraries available, so it is  
an option.  




## Target OS

Game was developed using Python 3, in ChromeOS, using the  
Linux environment.  

Compability with other systems has not yet been tested,  
but I expect that most other Linux installs can play the  
game.  




## End of Document

Thanks for reading!  
