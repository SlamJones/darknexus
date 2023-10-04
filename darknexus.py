#!/usr/bin/env python3

import random
import os
import json
import math
from graphics import GraphWin, Rectangle, Line, Point, Circle, Text, update, Image, Entry
from time import time,sleep
from datetime import datetime
from screeninfo import get_monitors


## CONVERT ALL AMBIGUOUS "X1", "X2", "X", ETC TO A MORE CLEAR FORM
## MAP_X1       is where it is located on the game map, in the files
## SCREEN_X1    is where it appears on the screen at a given time
## OFFSET_X1    is the difference between the two


## Item data is loaded from json file ##
def import_data():
    path = os.path.join('data','data.json')
    with open(path,'r') as file:
        data = json.load(file)
    data = process_data(data)
    return(data)


## After importing data, we need to process it to use it in game
def process_data(data):
    for item in data:
        item = process_data_item(item)
    return(data)


## Given a data item, process any encapsulated data items
## Convert any encountered digits to int, whenever possible
def process_data_item(data_item):
    print("def process_data_item received {}".format(data_item))
    if type(data_item) in [dict,list]:
        for subitem in data_item:
            subitem = process_data_item(subitem)
    elif data_item.isdigit():
        data_item = int(data_item)
    print("def process_data_item returning {}".format(data_item))
    return(data_item)


#"loot_table": [
#    {"chance": 80, "item": {"per_stack": [4,8], "type": "coins"}, "quantity": 4},
#    {"chance": 70, "item": {"loot_level": 1, "type": "potion"}, "quantity": 1},
#    {"chance": 30, "item": {"loot_level": 1, "type": "ammo"}, "quantity": 6},
#    {"chance": 20, "item": {"loot_level": 1, "type": "weapon"}, "quantity": 1}]

## Based on given loot table, determine actual items contained in container
def loot_table_drop(win,data,loot_table,screen_x,screen_y,interact_radius,center):
    loot_to_drop = []
    for loot_item in loot_table:
        #print("item in loot_table: {}".format(loot_item))
        for i in range(loot_item["quantity"]): # If there are multiple copies of an item to be rolled
            if roll(0,100) < loot_item["chance"]: # If the roll is sucessful
                if loot_item["item"]["type"] == "coins":
                    per_stack = random.randrange(loot_item["item"]["per_stack"][0],loot_item["item"]["per_stack"][1])
                    
                    # Based on coin stack size, set an appropriate image/icon for it #
                    if per_stack < 5:
                        img = "img/Coin_1.png"
                    elif per_stack < 10:
                        img = "img/Coin_3.png"
                    elif per_stack < 20:
                        img = "img/Coin_6.png"
                    elif per_stack < 35:
                        img = "img/Coin_12.png"
                    else:
                        img = "img/Coin_20.png"
                        
                    # Create the coin item itself using chosen image
                    item = new_item("Coins","coins","common",img,"coins {}".format(per_stack),
                                    "value {}".format(per_stack),"A handful of coins.",{})
                    item = drop_item(win,item,screen_x,screen_y,interact_radius,center)
                    loot_to_drop.append(item)
                else: # If the loot item is anything other than coins
                    item = new_random_item_from_level(data,loot_item["item"]["loot_level"],loot_item["item"]["type"])
                    item = drop_item(win,item,screen_x,screen_y,interact_radius,center)
                    print("def new_random_item_from_level returned {}".format(item["name"]))
                    if item != None: # As long as an item of some sort is returned
                        loot_to_drop.append(item) # Add it to the loot_to_drop list
    
    return(loot_to_drop) # Should return a list of items that can be immediately dropped to the floor


## If a destroyable is hit by a projectile (or hitscan), it explodes and drops its contents
def destroy_destroyable(win,data,map_objs,destroyable,center):
    # Get a list of loot that is to be dropped
    loot_table = []
    for item in destroyable["loot"]:
        loot_table.append(item)
    screen_x,screen_y = destroyable["map_x1"]-int(center[0]),destroyable["map_y1"]-int(center[1])
    interact_radius = 64
    loot_to_drop = loot_table_drop(win,data,loot_table,screen_x,screen_y,interact_radius,center)
    print("def loot_table_drop returned {} items".format(len(loot_to_drop)))
    for item in loot_to_drop: # Iterate through list of loot to be dropped
        drop_item(win,item.copy(),screen_x,screen_y,interact_radius,center) # Drop said item
        map_objs.append(item) # Add each item to map_objs
    
    map_objs.remove(destroyable) # Then remove the destroyable itself
    destroyable["obj"].undraw()
    return(win,map_objs)
                                                                              

## Given an item type and loot level, pick a random item from data that matches those and return it
def new_random_item_from_level(data,loot_level,item_type):
    new_item = {}
    valid_choices = []
    for item in data["items"][item_type]:
        if int(item["loot_level"]) == int(loot_level):
            valid_choices.append(item)  # Populate list with items that match loot_level and item_type
    print("def new_random_item_from_level has {} valid_choices".format(len(valid_choices)))            
    data_item = random.choice(valid_choices) # Then pick an item from the list at random
    for item_stat in data_item.keys():
        try:
            new_item[item_stat] = data_item[item_stat].copy()
        except:
            new_item[item_stat] = data_item[item_stat]
    return(new_item)

    
## Given destroyable data from data file, build and return destroyable
def new_destroyable(destroyable):
    nd = destroyable.copy()
    if "img" in destroyable.keys():
        nd["obj"] = Image(Point(destroyable["map_x1"],destroyable["map_y1"]),destroyable["img"])
    else:
        if nd["shape"] == "rect":
            nd["obj"] = Rectangle(Point(destroyable["map_x1"],destroyable["map_y1"]),
                                  Point(destroyable["map_x2"],destroyable["map_y2"]))
        elif nd["shape"] == "circ":
            nd["obj"] = Circle(Point(destroyable["map_x1"],destroyable["map_y1"]),destroyable["radius"])
        nd["obj"].setFill(destroyable["fill_color"])
        nd["obj"].setOutline(destroyable["outline_color"])
        nd["obj"].setWidth(3)
    nd["tangible"] = True
    return(nd)

    
## Given collider data from data file, build and return the collider
def new_collider(collider):
    nc = collider.copy()
    if "img" in nc.keys():
        nc["obj"] = Image(Point(collider["map_x1"],collider["map_y1"]),collider["img"])
    else:
        if nc["shape"] == "rect":
            nc["obj"] = Rectangle(Point(collider["map_x1"],collider["map_y1"]),Point(collider["map_x2"],collider["map_y2"]))
        elif nc["shape"] == "circ":
            nc["obj"] = Circle(Point(collider["map_x1"],collider["map_y1"]),collider["radius"])
        nc["obj"].setFill(collider["fill_color"])
        nc["obj"].setOutline(collider["outline_color"])
        nc["obj"].setWidth(3)
    nc["tangible"] = True
    return(nc)


## Check if item has requirements
## Determine if character meets thos requirements
## Return True if they do, False if not
def check_item_reqs(character,item):
    for req in item["req"].keys():
        if type(item["req"][req]) is int:
            if int(character[req]) < int(item["req"][req]):
                return(False)
        else:
            if character[req] != item["req"][req]:
                return(False)
    return(True)


## Given an item name, find the item in data and return it
## If item not found in data, returns None
def new_item_from_name(data,item_name):
    new_item = {}
    for category in data["items"].keys():
        for data_item in data["items"][category]:
            if data_item["name"] == item_name:
                for item_stat in data_item.keys():
                    try:
                        new_item[item_stat] = data_item[item_stat].copy()
                    except:
                        new_item[item_stat] = data_item[item_stat]
                return(new_item)
    return(None)


## Modify a piece of gear by adding a random enchantment
## This generally adds stat or damage bonuses
def add_random_enchantment(old_item,tier,data):
    item = old_item.copy()
    if "hasPrefix" in item.keys():
        item["rarity"] = "rare"
        choice = "suffix"
    elif "hasSuffix" in item.keys():
        item["rarity"] = "rare"
        choice = "prefix"
    else:
        choice = random.choice(["suffix","prefix"])
        item["rarity"] = "uncommon"
        
    enchant = random.choice(data["enchantments"]["tier {}".format(tier)][choice])
    
    print(">>>>  Adding enchantment {}".format(enchant))
    
    if choice == "prefix":
        item["name"] = "{} {}".format(enchant[0],item["name"])
        item["hasPrefix"] = True
    else:
        item["name"] = "{} {}".format(item["name"],enchant[0])
        item["hasSuffix"] = True
        
    effect = enchant[1].split()
    if effect[0] == "dmg":
        item["damage"][0] += int(effect[1])
        item["damage"][1] += int(effect[2])
        
    elif effect[0] in ["str","stam","dex","int","armor"]:
        if effect[0] in item["effect"].keys():
            item["effect"][effect[0]] += int(effect[1])
        else:
            item["effect"][effect[0]] = int(effect[1])
            

    return(item)


## Key repeat delay modification
def set_xset():
    os.system('xset r rate {}'.format(20))
    
## Reset key repeat delay to default
def reset_xset():
    os.system('xset r rate')
    
## Get the size of the main monitors screen
def get_screen_size():
    m = get_monitors()
    return(m[0].width,m[0].height)

## Open a window of given size x and y ##
def open_window(name,width,height):
    win = {}
    win["width"],win["height"] = width,height
    win["win"] = GraphWin(name,width,height,autoflush=False)
    win["win"].setBackground("black")
    print("Window: {} x {}".format(win["width"],win["height"]))
    return(win)

## Undraw everything on the screen ##
def undraw_all(win):
    item_list = win["win"].items
    item_list = item_list.copy()
    for i in item_list:
        i.undraw()
    return(win)

## Close the window, return the window object ##
def close_window(win):
    win["win"].close()
    return(win)



##
## MATH CALCULATIONS AND WHATWHAT ##
## Should be pretty self-explanitory ##
##
def calculate_move_xy(direction,speed):
    move_x = speed * math.sin(math.radians(direction))
    move_y = speed * math.cos(math.radians(direction))
    return(move_x,move_y)

def calculate_end_point(direction,speed,origin_x,origin_y):
    disp_x,disp_y = calculate_move_xy(direction,speed)
    end_x = origin_x + disp_x
    end_y = origin_y + disp_y
    return(end_x,end_y)
    
def coords_to_direction(x,y):
    return(math.atan2(y,x)/math.pi*180)

def direction_between_points(x1,y1,x2,y2):
    return(math.atan2(x2-x1,y2-y1)/math.pi*180)

def opposite_direction(direction):
    if direction > 180:
        return(direction - 180)
    return(direction + 180)

def calc_distance_between_points(p1,p2):
    a = abs(p2[0] - p1[0])
    b = abs(p2[1] - p1[1])
    #print("(def calc_dist) p1: {}, p2: {} = {}".format(p1,p2,a+b))
    return(a+b)
##
##
##


##
##
## PROJECTILE FUNCTIONS ##
##
##


## Determine if weapon has ammo or not
def check_weapon_ammo(weapon):
    if weapon["ammo"][0] <= 0:
        return(False)
    return(True)
        
        
## Weapon damage is character damage?
## Replace with more accurate in-depth functions
def set_damage(char):
    return(char["weapon"]["damage"])


## Used by autoguns, finds the nearest mob and returns direction and distance to it
def dir_to_nearest_mob(win,char,mobs):
    distance = 10000
    nearest_mob = None
    direction = 0
    for mob in mobs:
        new_distance = distance_between_objects(char,mob)
        if new_distance < distance:
            distance = new_distance
            nearest_mob = mob
            
    if nearest_mob != None:        
        #print(mob)
        direction = direction_between_points(
            char["obj"].getAnchor().getX(),char["obj"].getAnchor().getY(),
            nearest_mob["obj"].getAnchor().getX(),nearest_mob["obj"].getAnchor().getY())
            
    return(direction,distance)
    
    
## Some skills/gear have autoweapons
## Autoweapons will automatically fire projectiles at mobs in range
## Works very similar to regular fire_projectile
def fire_auto_projectile(win,char,autogun,mobs):
    projectiles = []
    if autogun["ammo"] > 0:
        radius = autogun["radius"]
        aim_dir,distance = dir_to_nearest_mob(win,char,mobs)
        max_dist = autogun["range"]

        if distance < (max_dist/2):
            autogun["ammo"] -= 1
            passthru = autogun["passthru"]
            char_dir = char["direction"]
            o = ""
            screen_ox,screen_oy = char["obj"].getAnchor().getX(),char["obj"].getAnchor().getY()
            
            if autogun["type"] == "Basic":
                ox,oy = char["obj"].getAnchor().getX(),char["obj"].getAnchor().getY()
                projectiles = [spawn_projectile(win,char,screen_ox,screen_oy,radius,passthru,
                                                aim_dir,autogun["damage"],max_dist,o,autogun["speed"])]

            elif autogun["type"] == "Spread":
                number = autogun["pellets"]
                angle = autogun["angle"]
                angles = calc_angles_from_max(number,angle)
                screen_ox,screen_oy = char["obj"].getAnchor().getX(),char["obj"].getAnchor().getY()
                projectiles = []
                for i in range(number):
                    projectile = spawn_projectile(
                        win,char,screen_ox,screen_oy,radius,passthru,aim_dir+angles[i],autogun["damage"],
                        max_dist,o,autogun["speed"])
                    projectiles.append(projectile)
                    
    return(projectiles)


## When player attempts to fire a shot
## Check if weapon has enough ammo
## If it does, then fire a projectile
def shoot_button(win,character,projectiles):
    #print("def shoot_button called")
    reloaded = False
    if check_weapon_ammo(character["weapon"]):
        new_projectiles=fire_projectile(win,character)
        for projectile in new_projectiles:
            projectiles.append(projectile)
    else:
        no_ammo_warning(win)
        character,character["weapon"] = attempt_reload_weapon(character,character["weapon"])
        if character["weapon"]["ammo"][0] == character["weapon"]["ammo"][1]:
            reloaded = True
    #print("def shoot_button returning {}".format(projectiles))
    return(projectiles,reloaded)


## If player hits 'reload' key, attempt to reload equipped weapon
## Returns True if reload occured, or False if it failed
def reload_manually(character):
    reloaded = False
    print("Attempting manual reload")
    reload_amount = character["weapon"]["ammo"][1] - character["weapon"]["ammo"][0]
    if reload_amount > 0:
        character,character["weapon"] = attempt_reload_weapon(character,character["weapon"])
        reloaded = True
    return(character,reloaded)


## Maybe scroll text saying no ammo?
## Maybe a 'click' no ammo sound?
def no_ammo_warning(win):
    pass


## Check if player has correct ammo
## If so, then reload weapon
def attempt_reload_weapon(character,weapon):
    #print(character["inventory"])
    for item_slot in character["inventory"]:
        if character["inventory"][item_slot] != None:
            print("Checking item {}".format(character["inventory"][item_slot]["name"]))
            if "ammo_type" in character["inventory"][item_slot].keys() and character["inventory"][item_slot]["type"] == "ammo":
                print("Ammo type: {}, weapon ammo type: {}".format(
                   character["inventory"][item_slot]["ammo_type"],weapon["ammo_type"])) 
                if character["inventory"][item_slot]["ammo_type"] == weapon["ammo_type"]:
                    if character["inventory"][item_slot]["quantity"] > 1:
                        character["inventory"][item_slot]["quantity"] -= 1
                    else:
                        character["inventory"][item_slot] = None
                    weapon["ammo"][0] = weapon["ammo"][1]
                    print("Reloaded {}".format(weapon["name"]))
                    return(character,weapon)
    
    return(character,weapon)


## A basic projectile with no special qualities
def fire_basic(win,char,radius,passthru,char_dir,o,max_dist,damage):
    screen_ox,screen_oy = char["obj"].getAnchor().getX(),char["obj"].getAnchor().getY()
    projectiles = [spawn_projectile(win,char,screen_ox,screen_oy,radius,passthru,char_dir,damage,max_dist,o,
                                    char["weapon"]["speed"])]
    return(projectiles)


## Spread projectiles act as a shotgun, firing a fan spread of projectiles centered on characters direction
def fire_spread(win,char,radius,passthru,char_dir,o,max_dist,damage):
    number = char["weapon"]["pellets"]
    angle = char["weapon"]["angle"]
    angles = calc_angles_from_max(number,angle)
    screen_ox,screen_oy = char["obj"].getAnchor().getX(),char["obj"].getAnchor().getY()
    projectiles = []
    for i in range(number):
        projectile = spawn_projectile(
            win,char,screen_ox,screen_oy,radius,passthru,char_dir+angles[i],damage,max_dist,o,char["weapon"]["speed"])
        projectiles.append(projectile)
    return(projectiles)


## Wide projectiles spawn a line of projectiles, perpendicular to character direction
## Does not really work at the moment
def fire_wide(win,char,radius,passthru,char_dir,o,max_dist,damage):    
    ox,oy = char["obj"].getAnchor().getX(),char["obj"].getAnchor().getY()
    if char["direction"] == 0 or char["direction"] == 180:
        ox2 = ox - 25
        ox3 = ox + 25
        oy2,oy3 = oy,oy
    elif char["direction"] == 90 or char["direction"] == 270:
        oy2 = oy - 25
        oy3 = oy + 25
        ox2,ox3 = ox,ox
    elif char["direction"] > 270 or char["direction"] < 90:
        ox2 = ox - 25
        ox3 = ox + 25
        oy2,oy3 = oy,oy
    else:
        oy2 = oy - 25
        oy3 = oy + 25
        ox2,ox3 = ox,ox
    projectile1 = spawn_projectile(
        win,char,ox,oy,radius,passthru,char_dir,damage,max_dist,o,char["weapon"]["speed"])
    projectile2 = spawn_projectile(
        win,char,ox2,oy2,radius,passthru,char_dir,damage,max_dist,o,char["weapon"]["speed"])
    projectile3 = spawn_projectile(
        win,char,ox3,oy3,radius,passthru,char_dir,damage,max_dist,o,char["weapon"]["speed"])
    projectiles = [projectile1,projectile2,projectile3]

    return(projectiles)


## Split projectiles spawn a circle of projectiles when they hit an object
def fire_split(win,char,radius,passthru,char_dir,o,max_dist,damage):
    o = [{"type":"split","delay":0,"projectiles":char["weapon"]["pellets"],"recursion":0}]
    ox,oy = char["obj"].getAnchor().getX(),char["obj"].getAnchor().getY()
    projectiles = [spawn_projectile(
        win,char,ox,oy,radius,passthru,char_dir,damage,max_dist,o,char["weapon"]["speed"])]
    
    return(projectiles)


## Shatter projectiles spawn a fan of projectiles when they hit an object
def fire_shatter(win,char,radius,passthru,char_dir,o,max_dist,damage):
    o = [{"type":"shatter","delay":0,"projectiles":char["weapon"]["pellets"],"max_angle":char["weapon"]["angle"],"recursion":0}]
    ox,oy = char["obj"].getAnchor().getX(),char["obj"].getAnchor().getY()
    projectiles = [spawn_projectile(
        win,char,ox,oy,radius,passthru,char_dir,damage,max_dist,o,char["weapon"]["speed"])]
    
    return(projectiles)
    
    
## When told to do so,determines what types of projectiles to create and spawn
## Uses characters equipped weapon to determine projectile variables
def fire_projectile(win,char):
    print("\ndef fire_projectile called with weapon {}".format(char["weapon"]["name"]))
    radius = char["weapon"]["proj_radius"]
    char["weapon"]["ammo"][0] -= 1
    passthru = char["weapon"]["passthru"]
    char_dir = char["direction"]
    o = ""
    max_dist = char["weapon"]["range"]
    
    damage = calculate_damage_range(char)
    damage = random.randrange(damage[0],damage[1])
    
    if char["weapon"]["fire_type"] == "Basic":
        projectiles = fire_basic(win,char,radius,passthru,char_dir,o,max_dist,damage)
        
    elif char["weapon"]["fire_type"] == "Spread":
        projectiles = fire_spread(win,char,radius,passthru,char_dir,o,max_dist,damage)
            
    elif char["weapon"]["fire_type"] == "Wide":
        projectiles = fire_wide(win,char,radius,passthru,char_dir,o,max_dist,damage)
    
    elif char["weapon"]["fire_type"] == "Split":
        projectiles = fire_split(win,char,radius,passthru,char_dir,o,max_dist,damage)
    
    elif char["weapon"]["fire_type"] == "Shatter":
        projectiles = fire_shatter(win,char,radius,passthru,char_dir,o,max_dist,damage)
    
    ## ADVANCED PROJECTILE TYPES THAT ARE NOT USED IN GAME YET ##
    ## Probably better ways of creating them? ##
    
    #elif char["weapon"]["fire_type"] == "Split (Recursive 1)":
    #    o = [{"type":"split","delay":0,"projectiles":char["weapon"]["pellets"],"recursion":1}]
    #    ox,oy = char["obj"].getAnchor().getX(),char["obj"].getAnchor().getY()
    #    projectiles = [spawn_projectile(
    #        win,char,ox,oy,radius,passthru,char_dir,damage,max_dist,o,char["weapon"]["speed"])]
    
    #elif char["weapon"]["fire_type"] == "Split Shatter":
    #    o = [{"type":"shatter","delay":0,"projectiles":char["weapon"]["pellets"],"max_angle":char["weapon"]["angle"],"recursion":0},
    #        {"type":"split","delay":0,"projectiles":char["weapon"]["pellets"],"recursion":0}]
    #    ox,oy = char["obj"].getAnchor().getX(),char["obj"].getAnchor().getY()
    #    projectiles = [spawn_projectile(
    #        win,char,ox,oy,radius,passthru,char_dir,damage,max_dist,o,char["weapon"]["speed"])]
    
    #elif char["weapon"]["fire_type"] == "Split > Shatter":
    #    o = [{"type":"shatter","delay":1,"projectiles":char["weapon"]["pellets"],"max_angle":char["weapon"]["angle"],"recursion":0},
    #        {"type":"split","delay":0,"projectiles":char["weapon"]["pellets"],"recursion":0}]
    #    ox,oy = char["obj"].getAnchor().getX(),char["obj"].getAnchor().getY()
    #    projectiles = [spawn_projectile(
    #        win,char,ox,oy,radius,passthru,char_dir,damage,max_dist,o,char["weapon"]["speed"])]
        
    #print("  def fire_projectile returning {}".format(projectiles))
    return(projectiles)
    
    
## Draw all items, in order, in received to_draw list
## Not really used at the moment, maybe unnecessary?
def draw_to_draw(win,to_draw):
    print("def draw_to_draw called")
    for item in to_draw:
        item.draw(win["win"])
   
    
def spawn_projectile(win,origin,origin_x,origin_y,radius,passthru,direction,damage,max_dist,other,speed):
    to_draw = []
    projectile = {}
    #origin_x, origin_y = origin["obj"].getAnchor().getX(),origin["obj"].getAnchor().getY()
    projectile["obj"] = Circle(Point(origin_x,origin_y), radius)
    projectile["obj"].setFill("aqua") #settings["hero_color"]["value"])
    projectile["origin_x"],projectile["origin_y"] = origin_x,origin_y
    projectile["direction"] = direction
    projectile["damage"] = damage
    projectile["speed"] = speed
    projectile["dir_x"],projectile["dir_y"] = calc_projectile_direction(projectile)
    projectile["dir_x"] += origin["move"][0]
    projectile["dir_y"] += origin["move"][1]
    projectile["origin"] = origin["name"]
    projectile["passthru"] = passthru
    projectile["max_distance"] = max_dist
    projectile["distance"] = 0
    projectile["other"] = other
    projectile["obj"].draw(win["win"])
    #to_draw.append(projectile["obj"])
    #draw_to_draw(win,to_draw)
    #print("  def spawn_projectile returning {}".format(projectile))
    return(projectile)


## Iterate through all projectiles, move them by their given movespeed instructions
## If any have moved far enough, delete them
def move_projectiles(win,projectiles):
    #print("  def move_projectiles received {} projectiles".format(len(projectiles)))
    for projectile in projectiles:
        if projectile != None:
            ## Move the item on-screen ##
            #print("    projectile has movespeed of {}x{}".format(projectile["dir_x"],projectile["dir_y"]))
            projectile["obj"].move(projectile["dir_x"],projectile["dir_y"])
            projectile["distance"] += (abs(projectile["dir_x"])+abs(projectile["dir_y"]))
            ## Check if item has gone beyond playfield bounds ##
            if check_projectile_deletion(win,projectile) or (projectile["distance"] >= projectile["max_distance"]):
                projectile["obj"].undraw()
                projectiles.remove(projectile)
                #if settings["debug_mode"]["value"]:
                #    print("Projectile deleted")
    return(projectiles)


## Based on projectile location and direction, determine projectile movespeed instruction
## Wording can be clarified to remove ambiguousness
def calc_projectile_direction(projectile):
    direction = projectile["direction"]
    origin_screen_x,origin_screen_y = projectile["obj"].getCenter().getX(),projectile["obj"].getCenter().getY()
    move_x,move_y = calculate_move_xy(direction,projectile["speed"])
    return(move_x,move_y)
                                        

## Determine if a projectile has moved far enough that it should be deleted
## This is so projectiles don't just travel infinitely through time and space
## Because that would slow everything down quite a bit
def check_projectile_deletion(win,projectile):
    #screen_centerX,screen_centerY=projectile["obj"].getCenter().getX(),projectile["obj"].getCenter().getY()
    if projectile["distance"] >= projectile["max_distance"]:
        print("\nprojectile reached max distance: deleting")
        return(True)
    return(False)


## Get distance between the centers of two circular objects
def distance_between_objects(obj1,obj2):
    print("def distance_between_objects called")
    screen_o1x,screen_o1y = obj1["obj"].getAnchor().getX(),obj1["obj"].getAnchor().getY()
    o1r = obj1["obj"].getRadius()
    screen_o2x,screen_o2y = obj2["obj"].getAnchor().getX(),obj2["obj"].getAnchor().getY()
    o2r = obj2["obj"].getRadius()
    dx = math.pow((screen_o1x - screen_o2x),2)
    dy = math.pow((screen_o1y - screen_o2y),2)
    distance = (math.sqrt(dx + dy))
    return(distance)


## Determine if a projectile phyiscally contacts another object of certain types
## Some object types are not checked for hits
def check_projectile_hit(projectile,mobs,map_objs,xy_offset):
    ## If it hits a mob, returns both mob and projectile
    ## If it hits a collider, it returns only the projectile
    ## If it hits nothing, it returns None
    
    proj_screen_x,proj_screen_y = projectile["obj"].getCenter().getX(),projectile["obj"].getCenter().getY()
    proj_r = projectile["obj"].getRadius()
    for mob in mobs:  # Check against all listed mobs
        if mob["tangible"] and mob["type"] not in ["vendor"]: # If mob can be hit at the moment and is not a vendor
            if "radius" in mob.keys(): # If object is a circle
                #mob_x,mob_y = mob["obj"].getAnchor().getX(),mob["obj"].getAnchor().getY()
                try:
                    mob_screen_x,mob_screen_y = mob["obj"].getCenter().getX(),mob["obj"].getCenter().getY()
                except:
                    mob_screen_x,mob_screen_y = mob["obj"].getAnchor().getX(),mob["obj"].getAnchor().getY()
                mob_r = mob["radius"]
                dx = math.pow((proj_screen_x - mob_screen_x),2)
                dy = math.pow((proj_screen_y - mob_screen_y),2)
                distance = (math.sqrt(dx + dy))
                max_hit_dist = mob_r + proj_r
                if distance <= (mob_r + proj_r):
                    print(">>> NON-hitscan hit registered")
                    return([mob,projectile]) # Return the mob that was hit, and the projectile
            else: # Otherwise, the shape is rectangle
                mob_screen_x1,mob_screen_y1 = mob["obj"].getP1().getX(),mob["obj"].getP1().getY()
                mob_screen_x2,mob_screen_y2 = mob["obj"].getP2().getX(),mob["obj"].getP2().getY()
                if (proj_screen_x > mob_screen_x1-projectile["obj"].getRadius()) and (
                    proj_screen_x < mob_screen_x2+projectile["obj"].getRadius()) and (
                    proj_screen_y > mob_screen_y1-projectile["obj"].getRadius()) and ( 
                    proj_screen_y < mob_screen_y2+projectile["obj"].getRadius()): 
                    print(">>> NON-hitscan hit registered")
                    return([mob,projectile])
                
    return(None) # Return nothing


## Determine if a hit occurred between received start and end points
## Does not account for projectile radius (but maybe it should?)
## Can undoubtedly be optimized for speed
def check_hitscan_hit(projectile,mobs,map_objs,xy_offset,screen_start,screen_end):
    ## If it hits a mob, returns both mob and projectile
    ## If it hits a collider, it returns only the projectile
    ## If it hits nothing, it returns None
    
    #print(">>>>        def check_hitscan_hit called")
    
    proj_screen_x,proj_screen_y = projectile["obj"].getCenter().getX(),projectile["obj"].getCenter().getY()
    proj_r = projectile["obj"].getRadius()
    for mob in mobs:  # Check against all listed mobs
        if mob["tangible"] and mob["type"] not in ["vendor"]: # If mob can be hit at the moment and is not a vendor
            if mob["shape"] == "circ": #if "radius" in mob.keys(): # If object is a circle
                #mob_x,mob_y = mob["obj"].getAnchor().getX(),mob["obj"].getAnchor().getY()
                try:
                    mob_screen_x,mob_screen_y = mob["obj"].getCenter().getX(),mob["obj"].getCenter().getY()
                except:
                    mob_screen_x,mob_screen_y = mob["obj"].getAnchor().getX(),mob["obj"].getAnchor().getY()
                    
                mob_r = mob["radius"]
                
                ## Some math stuff
                ## Equations n shit
                ## Determines if a line passes through a circle
                ax = screen_start[0] - mob_screen_x
                ay = screen_start[1] - mob_screen_y
                bx = screen_end[0] - mob_screen_x
                by = screen_end[1] - mob_screen_y
                
                a = (bx - ax)**2 + (by - ay)**2
                b = 2*(ax*(bx-ax) + ay*(by - ay))
                c = (ax**2) + (ay**2) - (mob_r**2)
                disc = (b**2) - (4*a*c)
                if disc > 0:
                    #print(">>>   hitscan has disc of {}".format(disc))
                    #return([mob,projectile])#None,projectile])
                
                    sqrtdisc = math.sqrt(disc)
                    t1 = (-b + sqrtdisc)/(2*a)
                    t2 = (-b - sqrtdisc)/(2*a)
                    
                    #print("    t1: {},  t2: {}".format(t1,t2))

                    if (0 < t1 < 1) or (0 < t2 < 1):
                        print(">>>   Hitscan hit registered against a circle!")
                        return([mob,projectile]) # Return the mob that was hit, and the projectile
            else: # If the shape is not a circle, then the shape is rectangle
                ## GET EACH CORNER OF THE RECTANGLE
                mob_screen_x1,mob_screen_y1 = mob["obj"].getP1().getX(),mob["obj"].getP1().getY()
                mob_screen_x2,mob_screen_y2 = mob["obj"].getP2().getX(),mob["obj"].getP2().getY()
                
                ## BREAK DOWN RECTANGLE INTO 4 LINE SEGMENTS
                projectile_segment = [screen_start,screen_end]
                
                segs =  []  #oLOLOLololOLOLo
                segs.append([[mob_screen_x1,mob_screen_y1],[mob_screen_x2,mob_screen_y1]])
                segs.append([[mob_screen_x2,mob_screen_y1],[mob_screen_x2,mob_screen_y2]])
                segs.append([[mob_screen_x1,mob_screen_y2],[mob_screen_x2,mob_screen_y2]])
                segs.append([[mob_screen_x1,mob_screen_y1],[mob_screen_x1,mob_screen_y2]])
                
                ## Then check out projectile path against each of the line segments in turn
                for mob_segment in segs:
                    ## TEST HITSCAN AGAINST EACH LINE
                    intersected = intersects(projectile_segment,mob_segment)
                    if intersected: ## IF CONDITIONS MET, THEN
                        print(">>>   Hitscan hit registered against a rectangle!")
                        return([mob,projectile]) # Return the mob that was hit, and the projectile
                
                #return([None,projectile]) ## USE THIS IF IT HITS SOMETHING UNIDENTIFIABLE
                
    return(None) # Return nothing


## Used in determining hitscan hits
## Math is hard :(
def intersects(s0,s1):
    dx0 = s0[1][0] - s0[0][0]
    dx1 = s1[1][0] - s1[0][0]
    dy0 = s0[1][1] - s0[0][1]
    dy1 = s1[1][1] - s1[0][1]
    
    p0 = (dy1*(s1[1][0] - s0[0][0])) - (dx1*(s1[1][1] - s0[0][1]))
    p1 = (dy1*(s1[1][0] - s0[1][0])) - (dx1*(s1[1][1] - s0[1][1]))
    p2 = (dy0*(s0[1][0] - s1[0][0])) - (dx0*(s0[1][1] - s1[0][1]))
    p3 = (dy0*(s0[1][0] - s1[1][0])) - (dx0*(s0[1][1] - s1[1][1]))
    return((p0*p1<=0)&(p2*p3<=0))


## Determine if character can move in desired direction
## Return True if they can make the move
## Return False if the cannot make the move
def check_move_colliders(character,map_objs,move):
    move_to = [character["map_x"]-move[0],character["map_y"]-move[1]] # Calculate where character will be after move completes
    for item in map_objs:  # Iterate through all map_objs
        if item["type"] in ["collider","mob"] and item["drawn"]:  # Only check colliders that are currently drawn
            if item["shape"] == "rect": # If it is a rectangle
                if move_to[0] > item["map_x1"]-character["radius"] and move_to[0] < item["map_x2"]+character["radius"] and (
                    move_to[1] > item["map_y1"]-character["radius"]+100 and move_to[1] < (
                        item["map_y2"]+character["radius"]+100)):
                    #print("Collided with {} at {},{} x {},{}".format(
                    #    item["name"],item["x1"],item["y1"],item["x2"],item["y2"]))
                    return(False)
                
            elif item["shape"] == "circ": # If it is a circle
                if move_to[0] > item["map_x1"]-character["radius"]-item["radius"] and (
                    move_to[0] < item["map_x1"]+character["radius"]+item["radius"]) and (
                    move_to[1] > item["map_y1"]-character["radius"]+100-item["radius"]) and (
                    move_to[1] < item["map_y1"]+character["radius"]+100+item["radius"]):
                    return(False)
    return(True)



## Upon hitting an object, shatter projectiles will spawn several more projectiles in a circular pattern
def instruct_split(projectiles,instruction):
    i_copy = instruction.copy()
    if instruction["recursion"] > 0:
        recursion = instruction["recursion"] - 1
        instruction = {
            "type":"split","projectiles":projectile["other"][0]["projectiles"],
            "recursion":recursion,"delay":0}
    else:
        instruction = {"type":"none","recursion":0,"delay":0}
    o = []
    if len(hit[1]["other"]) > 1:
        for i in hit[1]["other"]:
            if i != i_copy:
                #o.append(instruction)
                o.append(i)
    o.append(instruction)
    radius = hit[1]["obj"].getRadius()
    offset = hit[0]["radius"] + settings["extra_radius"]["value"]
    passthru = hit[1]["passthru"]
    max_dist = round(hit[1]["max_distance"]*0.75)
    if settings["debug_mode"]["value"]:
        print(instruction)
        print(hit[1])
    ox,oy = hit[0]["obj"].getAnchor().getX(),hit[0]["obj"].getAnchor().getY()

    projectile_list = []
    #print(projectile)
    #print(projectile.keys())
    for i in range(0,360,int(360/projectile["other"][0]["projectiles"])):
        projectile_list.append(spawn_projectile(
            win,hit[1],ox,oy-offset,radius,passthru,i,hit[1]["damage"],
            max_dist,o,projectile["speed"]))

    for p in projectile_list:
        projectiles.append(p)
    
    return(projectiles)


## Upon hitting an object, shatter projectiles will spawn several more projectiles in a fan pattern
def instruct_shatter(projectiles,instruction):
    i_copy = instruction.copy()
    max_angle = projectile["other"][0]["max_angle"]
    if instruction["recursion"] > 0:
        recursion = instruction["recursion"] - 1
        instruction = {
            "type":"split","projectiles":projectile["other"][0]["projectiles"],
            "recursion":recursion,"max_angle":max_angle,"delay":0,"speed":projectile["speed"]}
    else:
        instruction = {"type":"none","recursion":0,"max_angle":max_angle,"delay":0,"speed":0}
    o = []
    if len(hit[1]["other"]) > 1:
        for i in hit[1]["other"]:
            if i != i_copy:
                #o.append(instruction)
                o.append(i)
    o.append(instruction)
    radius = hit[1]["obj"].getRadius()
    offset=hit[0]["radius"] + settings["extra_radius"]["value"]
    passthru = hit[1]["passthru"]
    max_dist = round(hit[1]["max_distance"]*0.75)
    if settings["debug_mode"]["value"]:
        print(instruction)
        print(hit[1])
    ndir1 = hit[1]["direction"]
    ndir2 = hit[1]["direction"] + (instruction["max_angle"]/2)
    ndir3 = hit[1]["direction"] - (instruction["max_angle"]/2)
    ox,oy = hit[0]["obj"].getAnchor().getX(),hit[0]["obj"].getAnchor().getY()
    ox1,oy1 = calculate_end_point(ndir1,offset,ox,oy)
    ox2,oy2 = calculate_end_point(ndir2,offset,ox,oy)
    ox3,oy3 = calculate_end_point(ndir3,offset,ox,oy)

    projectile_list = []
    for i in range(int(ndir3),int(ndir2)+1,int(max_angle/projectile["other"][0]["projectiles"])):
        projectile_list.append(spawn_projectile(
            win,hit[1],ox,oy-offset,radius,passthru,i,hit[1]["damage"],
            max_dist,o,projectile["speed"]))

    for p in projectile_list:
        projectiles.append(p)

    return(projectiles)


## Currently checking every projectile against every mob each frame ##
## This creates lag when large amounts of projectiles exist ##
def check_for_projectile_hits(win,data,character,game_bar,projectiles,mobs,destroyables,colliders,map_objs,center,vfx):
    #print("def check_for_projectile_hits called")
    hit_mob = ""
    for projectile in projectiles:
        if projectile != None:
            
            ## Check mobs first ##
            hit = check_projectile_hit(projectile,mobs,map_objs,center)
            if hit == None:
                start = [projectile["obj"].getCenter().getX(),projectile["obj"].getCenter().getY()]
                end = [projectile["obj"].getCenter().getX()+projectile["dir_x"],
                       projectile["obj"].getCenter().getY()+projectile["dir_y"]]
                hit = check_hitscan_hit(projectile,mobs,map_objs,center,start,end)
            #print(" def check_projectile_hit returned {}".format(hit))
            if hit != None:
                if hit[0] != None:
                    ## Flash hit mob, remove health ##
                    mob_copy = hit[0].copy()
                    hit[0]["health"] -= hit[1]["damage"]
                    flash_mob(hit[0])
                    ## Slow down mob slightly ##
                    hit[0]["speed"] = hit[0]["speed"] * 0.9

                    ## Undraw and cull projectile ##
                    if projectile["passthru"] <= 0:
                        hit[1]["obj"].undraw()
                        projectiles.remove(hit[1])
                    else:
                        projectile["passthru"] -= 1

                    ## Check the 'other' for special projectile instruction strings ##
                    #print(hit[1]["other"])
                    for instruction in hit[1]["other"]:
                        #print(instruction)
                        if instruction["delay"] > 0:
                            instruction["delay"] -= 1
                            #print(instruction)
                        else:
                            if instruction["type"] == "split":
                                projectiles = instruct_split(projectiles,instruction)
                                ## MODULARIZED THIS BIT OF CODE ##
                                ## MAKE SURE IT WORKS BEFORE DELETING COMMENTED LINES ##
                                
                                #i_copy = instruction.copy()
                                #if instruction["recursion"] > 0:
                                #    recursion = instruction["recursion"] - 1
                                #    instruction = {
                                #        "type":"split","projectiles":projectile["other"][0]["projectiles"],
                                #        "recursion":recursion,"delay":0}
                                #else:
                                #    instruction = {"type":"none","recursion":0,"delay":0}
                                #o = []
                                #if len(hit[1]["other"]) > 1:
                                #    for i in hit[1]["other"]:
                                #        if i != i_copy:
                                #            #o.append(instruction)
                                #            o.append(i)
                                #o.append(instruction)
                                #radius = hit[1]["obj"].getRadius()
                                #offset = hit[0]["radius"] + settings["extra_radius"]["value"]
                                #passthru = hit[1]["passthru"]
                                #max_dist = round(hit[1]["max_distance"]*0.75)
                                #if settings["debug_mode"]["value"]:
                                #    print(instruction)
                                #    print(hit[1])
                                #ox,oy = hit[0]["obj"].getAnchor().getX(),hit[0]["obj"].getAnchor().getY()
                                #
                                #projectile_list = []
                                #print(projectile)
                                #print(projectile.keys())
                                #for i in range(0,360,int(360/projectile["other"][0]["projectiles"])):
                                #    projectile_list.append(spawn_projectile(
                                #        win,hit[1],ox,oy-offset,radius,passthru,i,hit[1]["damage"],
                                #        max_dist,o,projectile["speed"]))
                                #
                                #for p in projectile_list:
                                #    projectiles.append(p)

                            if instruction["type"] == "shatter":
                                projectiles = instruct_shatter(projectiles,instruction)
                                ## MODULARIZED THIS BIT OF CODE ##
                                ## MAKE SURE IT WORKS BEFORE DELETING COMMENTED LINES ##
                                
                                #i_copy = instruction.copy()
                                #max_angle = projectile["other"][0]["max_angle"]
                                #if instruction["recursion"] > 0:
                                #    recursion = instruction["recursion"] - 1
                                #    instruction = {
                                #        "type":"split","projectiles":projectile["other"][0]["projectiles"],
                                #        "recursion":recursion,"max_angle":max_angle,"delay":0,"speed":projectile["speed"]}
                                #else:
                                #    instruction = {"type":"none","recursion":0,"max_angle":max_angle,"delay":0,"speed":0}
                                #o = []
                                #if len(hit[1]["other"]) > 1:
                                #    for i in hit[1]["other"]:
                                #        if i != i_copy:
                                #            #o.append(instruction)
                                #            o.append(i)
                                #o.append(instruction)
                                #radius = hit[1]["obj"].getRadius()
                                #offset=hit[0]["radius"] + settings["extra_radius"]["value"]
                                #passthru = hit[1]["passthru"]
                                #max_dist = round(hit[1]["max_distance"]*0.75)
                                #if settings["debug_mode"]["value"]:
                                #    print(instruction)
                                #    print(hit[1])
                                #ndir1 = hit[1]["direction"]
                                #ndir2 = hit[1]["direction"] + (instruction["max_angle"]/2)
                                #ndir3 = hit[1]["direction"] - (instruction["max_angle"]/2)
                                #ox,oy = hit[0]["obj"].getAnchor().getX(),hit[0]["obj"].getAnchor().getY()
                                #ox1,oy1 = calculate_end_point(ndir1,offset,ox,oy)
                                #ox2,oy2 = calculate_end_point(ndir2,offset,ox,oy)
                                #ox3,oy3 = calculate_end_point(ndir3,offset,ox,oy)
                                #
                                #projectile_list = []
                                #for i in range(
                                #    int(ndir3),int(ndir2)+1,int(max_angle/projectile["other"][0]["projectiles"])):
                                #    projectile_list.append(spawn_projectile(
                                #        win,hit[1],ox,oy-offset,radius,passthru,i,hit[1]["damage"],
                                #        max_dist,o,projectile["speed"]))
                                #
                                #for p in projectile_list:
                                #    projectiles.append(p)


                    ## If mob health has dropped to 0 or less ##
                    ## Add animation info to the mob itself ##
                    ## And return the list of mobs ##
                    if hit[0]["health"] <= 0:
                        ## MOB INHERITS DIRECTION/SPEED FROM PROJECTILE ##
                        hit[0]["direction"],hit[0]["speed"] = hit[1]["direction"],hit[1]["speed"]/2
                        #hit[0]["direction"] = opposite_direction(hit[0]["direction"])
                        death_options = ["explode","pop"]
                        choice = random.choice(death_options)
                        #if choice == "explode":
                        #    hit[0] = explode_mob(win,hit[0])
                        #elif choice == "pop":
                        #    hit[0] = pop_mob(win,hit[0])
                        mobs.remove(hit[0])

                else:
                    projectiles.remove(hit[1])
                    hit[1]["obj"].undraw()
                        
            ## Check destroyables second ##
            if hit == None: # If no hit was registered yet
                hit = check_projectile_hit(projectile,destroyables,map_objs,center)
                if hit == None:
                    start = [projectile["obj"].getCenter().getX(),projectile["obj"].getCenter().getY()]
                    end = [projectile["obj"].getCenter().getX()+projectile["dir_x"],
                           projectile["obj"].getCenter().getY()+projectile["dir_y"]]
                    hit = check_hitscan_hit(projectile,destroyables,map_objs,center,start,end)
                if hit != None:
                    #print(">>    Registered hit against a destroyable: {}".format(hit))
                    if hit[0] != None:
                        #print("hit destroyable {}".format(hit))
                        character,game_bar = gain_xp(win,character,5,game_bar)
                        win,map_objs = destroy_destroyable(win,data,map_objs,hit[0],center)
                        screen_x,screen_y = hit[0]["map_x1"]-int(center[0]),hit[0]["map_y1"]-int(center[1])
                        
                        explosion = new_explosion(win,screen_x,screen_y)
                        vfx.append(explosion)
                        map_objs.append(explosion)
                        
                        destroyables.remove(hit[0])
                        
                    if projectile["passthru"] <= 0:
                        hit[1]["obj"].undraw()
                        projectiles.remove(hit[1])
                    else:
                        projectile["passthru"] -= 1
                        
            
            ## Check colliders last ##
            if hit == None: # If no hit was registered yet
                hit = check_projectile_hit(projectile,colliders,map_objs,center)
                if hit == None:
                    start = [projectile["obj"].getCenter().getX(),projectile["obj"].getCenter().getY()]
                    end = [projectile["obj"].getCenter().getX()+projectile["dir_x"],
                           projectile["obj"].getCenter().getY()+projectile["dir_y"]]
                    hit = check_hitscan_hit(projectile,colliders,map_objs,center,start,end)
                #print("hit (vs colliders) {}".format(hit))
                if hit != None:
                    #print(">>    Registered hit against a collider with projectile {}".format(hit[1]))
                    hit[1]["obj"].undraw()
                    projectiles.remove(hit[1])
                    explosion = new_explosion(win,hit[1]["obj"].getCenter().getX(),hit[1]["obj"].getCenter().getY())
                    vfx.append(explosion)
                    map_objs.append(explosion)
            
    return(projectiles,mobs,destroyables,colliders,map_objs,character,game_bar,vfx)


def calc_angles_from_max(number,angle):
    print("def calc_angles_from_max called")
    between = int(angle / (number-1))
    max_angle = int(angle / 2)
    angle_list = []
    for i in range(-max_angle,max_angle+1,between):
        angle_list.append(i)
    return(angle_list)

##
##
## END PROJETILE FUNCTIONS
##
##



## When player hits 'escape' during gameplay
## Pause the game and display a list of options
## Display two animated 'tokens' so that screen does not appear completely frozen
def pause_menu(win):
    to_draw, buttons = [], []
    
    outer_box = new_button(win["width"]*0.25,win["height"]*0.05, win["width"]*0.5, win["height"]*0.8,
                           "","","black","white","white",30)
    to_draw.append(outer_box["button"])
    to_draw.append(outer_box["text"]) 
    
    menu_title = Text(Point(win["width"]/2,win["height"]*0.125), "PAUSED")
    menu_title.setTextColor("white")
    menu_title.setSize(32)
    menu_title.setStyle("bold")
    to_draw.append(menu_title)
    
    menu_token_l = Circle(Point(win["width"]*0.3,win["height"]*0.125), 20)
    menu_token_l.setFill("gray0")
    menu_token_l.setOutline("red")
    to_draw.append(menu_token_l)
    
    menu_token_r = Circle(Point(win["width"]*0.7,win["height"]*0.125), 20)
    menu_token_r.setFill("gray0")
    menu_token_r.setOutline("red")
    to_draw.append(menu_token_r)
    
    resume_box = new_button(win["width"]*0.33,win["height"]*0.25, win["width"]*0.33, 80,
                           "Resume","resume","dark olive green","white","yellow",24)
    buttons.append(resume_box)
    to_draw.append(resume_box["button"])
    to_draw.append(resume_box["text"]) 
    
    save_box = new_button(win["width"]*0.33,win["height"]*0.4, win["width"]*0.33, 80,
                           "Save Game","save","dark slate gray","white","yellow",24)
    buttons.append(save_box)
    to_draw.append(save_box["button"])
    to_draw.append(save_box["text"]) 
    
    load_box = new_button(win["width"]*0.33,win["height"]*0.55, win["width"]*0.33, 80,
                           "Load Game","load","dark slate gray","white","yellow",24)
    buttons.append(load_box)
    to_draw.append(load_box["button"])
    to_draw.append(load_box["text"]) 
    
    exit_box = new_button(win["width"]*0.33,win["height"]*0.7, win["width"]*0.33, 80,
                           "Exit Game","exit","dark red","white","yellow",24)
    buttons.append(exit_box)
    to_draw.append(exit_box["button"])
    to_draw.append(exit_box["text"]) 
    
    # Initizalize token variables used for animation
    token_number = 0
    token_dir = "up"
    
    for item in to_draw:
        item.draw(win["win"])
        
    play = True
    
    while play:
        ## Put some sort of animation here so screen is not totally frozen when paused ##
        ## Token circle will slowly fade between white to black ##
        ## Token counts up to 100, then back down to 0, and repeat ad nauseum ##
        if token_dir == "up":
            if token_number < 100:
                token_number += 1
            else:
                token_dir = "down"
        else:
            if token_number > 0:
                token_number -= 1
            else:
                token_dir = "up"
        menu_token_l.setFill("gray{}".format(token_number))
        menu_token_r.setFill("gray{}".format(token_number))
        
        ## Refresh monitor at 30fps ##
        ## Kept low to prevent pc from using too much energy on this ##
        update(30)
        
        ## Check if user clicked the mouse
        click = win["win"].checkMouse()
        
        ## If a click was registered
        if click != None:
            clicked_on = interpret_click(win,buttons,click) ## Figure out what was clicked on
            if clicked_on != None: ## If a button was clicked on, do something
                if clicked_on == "resume":  ## IF RESUMING GAME
                    for item in to_draw:
                        item.undraw()
                    return(win,"")
                elif clicked_on == "save": ## NOT HOOKED UP YET
                    pass
                elif clicked_on == "load": ## NOT HOOKED UP YET
                    pass
                elif clicked_on == "exit": ## EXIT TO MAIN MENU
                    return(win,"exit")
    
    return(win,"")




## Rather than type out 11 lines of code per button, use this function to do it in 1 line ##
def new_button(screen_x1,screen_y1,x_size,y_size,text,function,fill_color,text_color,outline_color,text_size):
    button = {}
    button["button"] = Rectangle(Point(screen_x1, screen_y1),Point(screen_x1+x_size,screen_y1+y_size))
    button["button"].setFill(fill_color)
    button["button"].setOutline(outline_color)
    button["button"].setWidth(2)
    button["text"] = Text(Point(screen_x1+(x_size/2),screen_y1+(y_size/2)),text)
    button["text"].setTextColor(text_color)
    button["text"].setSize(text_size)
    button["function"] = function
    button["fill_color"] = fill_color
    button["text_color"] = text_color
    button["outline_color"] = outline_color
    
    return(button)


## Work in Progress
## Intended to allow player to assign specific items to specific hotkeys
## So when player presses hotkey, the item is equipped or used
def assign_hotkey(win,character,hotkey,item,game_bar):
    character["hotkey"][hotkey] = item # Set hotkey to item
    return(win,character,game_bar)


## If player hits a key associated with a hotkey, interpret it here ##
## Hotkeys usually relate to items in inventory ##
## Store hotkey info in game_bar or in character?? ##
def use_hotkey(win,character,hotkey,game_bar):
    #for item in game_bar:
    #    print(item)

    if character["hotkey"][hotkey] != None: ## If something is assigned to this hotkey
        for item in character["inventory"]: ## Iterate through character inventory
            if item is character["hotkey"][hotkey]:  ## If the referenced item is here
                character,item,game_bar = use_item(win,character,item,game_bar) ## Then use that item
                print("Hotkey {} points to item {}".format(hotkey,item))
                return(win,character,game_bar)
    character["hotkey"][hotkey] = None ## If the item is not found, then clear the reference
    return(win,character,game_bar)


## Takes a list of buttons and a click ##
## Returns the function of the button, if any, that was clicked on ##
## Otherwise returns None ##
def interpret_click(win,buttons,click):
    click_x, click_y = click.getX(), click.getY()
    for button in buttons:
        screen_x1 = button["button"].getP1().getX()
        screen_y1 = button["button"].getP1().getY()
        screen_x2 = button["button"].getP2().getX()
        screen_y2 = button["button"].getP2().getY()
        
        ## Make sure x1 and y1 are lower than x2 and y2
        if screen_x1 > screen_x2:
            screen_x1,screen_x2 = screen_x2,screen_x1
        if screen_y1 > screen_y2:
            screen_y1,screen_y2 = screen_y2,screen_y1
        
        ## Then determine if the click falls within these bounds
        if click_x >= screen_x1 and click_x <= screen_x2 and click_y >= screen_y1 and click_y <= screen_y2:
            ## If it does, then provide feedback to player in the form of a button flash
            ## This method actually pauses the game for 0.2 of a second
            ## A better method is required!
            button["button"].setFill("white")
            button["text"].setTextColor("black")
            update()
            sleep(0.15)
            button["button"].setFill(button["fill_color"])
            button["text"].setFill(button["text_color"])
            update()
            sleep(0.05)
            print("Clicked on {}".format(button["function"]))
            return(button["function"])
    
    return(None)


## Sometimes when loading a level, game will lag for a few seconds
## In those cases, throw a loading screen in to make it clear that the game did not freeze
## Makes players a bit more patient with loading times
## Maybe have a few different loading screen images to choose from?
def draw_loading_screen(win):
    win = undraw_all(win)
    loading_screen = {}
    loading_screen["img"] = Image(Point(win["width"]/2,win["height"]/2),"img/LCD_Screen_1.png")
    loading_screen["img"].draw(win["win"])
    loading_screen["text"] = Text(Point(win["width"]/2,win["height"]/3), "LOADING...")
    loading_screen["text"].setSize(30)
    loading_screen["text"].setTextColor("white")
    loading_screen["text"].setStyle("bold")
    loading_screen["text"].setFace("courier")
    loading_screen["text"].draw(win["win"])
    update()
    return(win,loading_screen)


## Gray can be represented by gray0 (white) to gray100 (black)
## Start with black and fade to white
## Divide sleep time by half per color
## So that the fade time is exponential
def fade_to_black(win):
    sleep_time = 1
    for number in range(101):
        color = "gray{}".format(100 - number)
        win["win"].setBackground(color)
        update()
        sleep(sleep_time)
        sleep_time = sleep_time/2
    
    return(win)


## After starting program, and before reaching main menu
## Titles tell us who made the game and the name of the game
## Can have as many slides as we need, but 2 is probably enough
def titles(win):
    win["win"].setBackground("white")
    win = undraw_all(win)
    slides = [["img/LCD_Screen_3.png","SlamTek Presents"],["img/LCD_Screen_2.png","Dark Nexus"]]
    play = True
    
    win = fade_to_black(win) # Fade from black to white (should look kinda cool)
    
    # Iterate through slide list, displaying the chosen image, then drawing the text on top of that
    for slide in slides:
        title_image = Image(Point(win["width"]/2,win["height"]/2),slide[0])
        title_image.draw(win["win"])
        title = Text(Point(win["width"]/2,win["height"]/3),slide[1])
        title.setTextColor("white")
        title.setSize(36)
        title.draw(win["win"])
        
        # Draw to screen, wait, then undraw and move to next slide
        update()
        sleep(2)
        title.undraw()
    return


## Main menu of the game
## Allows player to start a new game, load a saved game, or exit the game
## Has a background image that slowly scrolls across the screen, and reverses when reaching the screen edge
def main_menu(win):
    win = undraw_all(win) # Clear anything already drawn to the screen
    to_draw,buttons = [],[] # Initialize some necessary variables
    
    ## Collect data from data file
    data = import_data()
    
    win["win"].setBackground("web maroon")
    
    bg_img_list = ["img/Title_Wide.png"] # Can allow for multiple background images eventually
    
    bg_img = Image(Point(win["width"],win["height"]/2),bg_img_list[0])
    img_width = bg_img.getWidth()
    img_height = bg_img.getHeight()
    to_draw.append(bg_img)
    
    title = Text(Point(win["width"]/2,120),"Dark Nexus")
    title.setTextColor("white")
    title.setSize(36)
    to_draw.append(title)
    
    nb = new_button(win["width"]/4,300,win["width"]/2,100,"NEW GAME","new game","black","white","white",24)
    buttons.append(nb)
    to_draw.append(nb["button"])
    to_draw.append(nb["text"]) 
    
    nb = new_button(win["width"]/4,500,win["width"]/2,100,"LOAD GAME","load game","black","white","white",24)
    buttons.append(nb)
    to_draw.append(nb["button"])
    to_draw.append(nb["text"]) 
    
    nb = new_button(win["width"]/4,win["height"]-300,win["width"]/2,100,"EXIT GAME","exit game","black","white","white",24)
    buttons.append(nb)
    to_draw.append(nb["button"])
    to_draw.append(nb["text"]) 

    for item in to_draw:
        item.draw(win["win"])
        
    play = True
    move_left = True
    while play:
        if bg_img.getAnchor().getX() > win["width"]:
            move_left = False
        elif bg_img.getAnchor().getX() < 0:
            move_left = True
        
        if move_left:
            bg_img.move(0.1,0)
        else:
            bg_img.move(-0.1,0)
        
        ## Try to update screen at 60fps for smoothness
        update(60)
        
        key = win["win"].checkKey()
        click = win["win"].checkMouse()
        
        if click != None:
            clicked_on = interpret_click(win,buttons,click)
            if clicked_on != None:
                if clicked_on == "new game":
                    character = new_character(win)
                    if character != None:
                        game(win,character,data)
                    win = undraw_all(win)
                    for item in to_draw:
                        item.draw(win["win"])
                    win["win"].setBackground("red4")
    
                elif clicked_on == "load game":
                    pass
                elif clicked_on == "exit game":
                    play = False
    
    
    return


## New character screen, player comes here from Main Menu
## Shows possible character selections, along with their relevant stats and sprite
## Player can set characters name
## Maybe allow player to choose a protrait for dialog as well?
def new_character(win):
    reset_xset()
    win = undraw_all(win)
    
    to_draw,buttons = [],[]
    
    win["win"].setBackground("black")
    bg_img = Image(Point(win["width"]/2,win["height"]/2),"img/Doorway_1.png")
    to_draw.append(bg_img)
    
    title = Text(Point(win["width"]/2,100),"NEW CHARACTER")
    title.setTextColor("white")
    title.setSize(36)
    to_draw.append(title)
    
    subt = Text(Point(win["width"]*0.75,250),"Choose your character")
    subt.setTextColor("white")
    subt.setSize(20)
    to_draw.append(subt)
    
    desc_box = Rectangle(Point(200,200),Point(win["width"]/2,800))
    desc_box.setFill("black")
    desc_box.setOutline("white")
    desc_box.setWidth(4)
    to_draw.append(desc_box)
    
    desc_title = Text(Point((win["width"]/2)-300,240),"Heavy")
    desc_title.setTextColor("white")
    desc_title.setSize(20)
    to_draw.append(desc_title)
    
    desc_text = Text(Point((win["width"]/2)-300,400),"Str: 30\nStam: 15\nDex: 10\nInt: 5")
    desc_text.setTextColor("white")
    desc_text.setSize(14)
    to_draw.append(desc_text)
    
    name_entry = Entry(Point((win["width"]/2)-400,750),20)
    name_entry.setSize(24)
    name_entry.setText("Hero")
    to_draw.append(name_entry)
    
    
    nb = new_button(win["width"]*0.65,300,win["width"]/4,80,"HEAVY","heavy","black","white","white",18)
    buttons.append(nb)
    to_draw.append(nb["button"])
    to_draw.append(nb["text"]) 
    
    nb = new_button(win["width"]*0.65,400,win["width"]/4,80,"SOLDIER","soldier","black","white","white",18)
    buttons.append(nb)
    to_draw.append(nb["button"])
    to_draw.append(nb["text"]) 
    
    nb = new_button(win["width"]*0.65,500,win["width"]/4,80,"TECHNOMANCER","technomancer","black","white","white",18)
    buttons.append(nb)
    to_draw.append(nb["button"])
    to_draw.append(nb["text"]) 
    
    nb = new_button(win["width"]-250,win["height"]-200,200,80,"GO BACK","go back","black","white","white",18)
    buttons.append(nb)
    to_draw.append(nb["button"])
    to_draw.append(nb["text"]) 
    
    nb = new_button((win["width"]/2)+100,win["height"]-200,300,80,"START GAME","start game","black","white","white",24)
    buttons.append(nb)
    to_draw.append(nb["button"])
    to_draw.append(nb["text"]) 
    
    
    ## Set stat defaults for Heavy, as it is selected by default ##
    cstr = 30
    cstam = 15
    cdex = 10
    cint = 5
    selected = "heavy"
    img = "img/Heavy_A.png"
    
    
    char_img = Image(Point(300,400),img)
    to_draw.append(char_img)
    
    
    for item in to_draw:
        item.draw(win["win"])
    
    play = True
    move_left = True
    while play:
        click = win["win"].checkMouse()

        if click != None:
            clicked_on = interpret_click(win,buttons,click)
            if clicked_on != None:
                if clicked_on == "heavy":
                    desc_title.setText("{}".format(clicked_on.capitalize()))
                    cstr = 30
                    cstam = 15
                    cdex = 10
                    cint = 5
                    img = "img/Heavy_A.png"
                    char_img.undraw()
                    char_img = Image(char_img.getAnchor(), img)
                    char_img.draw(win["win"])
                    desc_text.setText("Str: {}\nStam: {}\nDex: {}\nInt: {}".format(cstr,cstam,cdex,cint))
                    selected = clicked_on
                elif clicked_on == "soldier":
                    desc_title.setText("{}".format(clicked_on.capitalize()))
                    cstr = 10
                    cstam = 10
                    cdex = 30
                    cint = 10
                    img = "img/Soldier_A.png"
                    char_img.undraw()
                    char_img = Image(char_img.getAnchor(), img)
                    char_img.draw(win["win"])
                    desc_text.setText("Str: {}\nStam: {}\nDex: {}\nInt: {}".format(cstr,cstam,cdex,cint))
                    selected = clicked_on
                elif clicked_on == "technomancer":
                    desc_title.setText("{}".format(clicked_on.capitalize()))
                    cstr = 10
                    cstam = 5
                    cdex = 15
                    cint = 30
                    img = "img/Technomancer_A.png"
                    char_img.undraw()
                    char_img = Image(char_img.getAnchor(), img)
                    char_img.draw(win["win"])
                    desc_text.setText("Str: {}\nStam: {}\nDex: {}\nInt: {}".format(cstr,cstam,cdex,cint))
                    selected = clicked_on
                elif clicked_on == "go back":
                    character = None
                    play = False    
                elif clicked_on == "start game":
                    character = {}
                    character["name"] = name_entry.getText()
                    character["class"] = selected
                    character["level"] = 1
                    character["coins"] = 100
                    character["xp"] = [0,100]
                    character["str"] = cstr
                    character["stam"] = cstam
                    character["dex"] = cdex
                    character["int"] = cint
                    character["hp"] = [cstam*5,cstam*5]
                    character["mp"] = [cint*5,cint*5]
                    character["stat_points"] = 1
                    character["skill_points"] = 1
                    character["helm"] = None
                    character["armor"] = None
                    character["weapon"] = None
                    character["shield"] = None
                    character["rings"] = [None,None]
                    character["inventory"] = {}
                    character["bools"] = {}
                    character["hotkey"] = {
                        "1": None, "2": None, "3": None, "4": None, "5": None, "6": None, "7": None, "8": None}
                    
                    for i in range(1,6):
                        for j in range(1,11):
                            character["inventory"]["{} {}".format(i,j)] = None
                    
                    character["map"] = 0
                    character["map_x"] = win["width"]/2
                    character["map_y"] = win["height"]/2
                    character["move_speed"] = 8
                    
                    character["obj"] = Image(Point(win["width"]/2,(win["height"]/2)-130),img)
                    #character["obj"] = Circle(Point(win["width"]/2,(win["height"]/2)-100),20)
                    #character["fill_color"] = "blue4"
                    #character["obj"].setFill(character["fill_color"])
                    #character["outline_color"] = "aqua"
                    #character["obj"].setOutline(character["outline_color"])
                    #character["obj"].setWidth(5)
                    character["radius"] = 25
                    play = False
    set_xset()
    return(character)


## Many gear items add bonus stats when equipped
## This checks them all and returns total stat for a character
def calc_total_stat(character,stat_name):
    total_stat = character[stat_name] # Get base unmodified stat from character
    for item_slot in ["weapon","armor","helm","shield"]:
        if character[item_slot] != None: # If there is an item in the item slot
            if stat_name in character[item_slot]["effect"]: # Check the item effects for stats
                total_stat += int(character[item_slot]["effect"][stat_name]) # Modify the returned stat
    return(total_stat)


## Draw the left-side panel, which displays many character stats
## If player has stat points, allows player to assign those points to specific stats
## Uses whole numbers instead of fractions: not compatible with other monitor resolutions
def draw_char_sheet(win,character):
    char_sheet = {}
    char_sheet["to_draw"],char_sheet["buttons"] = [],[]
    
    box = Rectangle(Point(0,0),Point(win["width"]/2,win["height"]))
    box.setFill("slate gray")
    box.setOutline("bisque")
    box.setWidth(4)
    char_sheet["box"] = box
    char_sheet["to_draw"].append(box)
    
    name_box = new_button(25,30,(win["width"]/2)-50,60,character["name"],"name box","beige","black","black",24)
    name_box["button"].setWidth(4)
    char_sheet["name_box"] = name_box
    char_sheet["to_draw"].append(name_box["button"])
    char_sheet["to_draw"].append(name_box["text"])
    
    class_box = new_button(25,100,(win["width"]/2)-50,60,
                           "Level {} {} ({} / {} xp)".format(
                               character["level"],character["class"],int(character["xp"][0]),int(character["xp"][1])),
                           "class box","beige","black","black",20)
    class_box["button"].setWidth(4)
    char_sheet["class_box"] = class_box
    char_sheet["to_draw"].append(class_box["button"])
    char_sheet["to_draw"].append(class_box["text"])
    
    hp_box = new_button(25,200,(win["width"]/4)-40,60,
                        "HP: {} / {}".format(character["hp"][0],character["hp"][1]),"hp box","beige","black","black",18)
    hp_box["button"].setWidth(4)
    char_sheet["hp_box"] = hp_box
    char_sheet["to_draw"].append(hp_box["button"])
    char_sheet["to_draw"].append(hp_box["text"])
    
    mp_box = new_button(10+(win["width"]/4),200,(win["width"]/4)-40,60,
                        "MP: {} / {}".format(character["mp"][0],character["mp"][1]),"mp box","beige","black","black",18)
    mp_box["button"].setWidth(4)
    char_sheet["mp_box"] = mp_box
    char_sheet["to_draw"].append(mp_box["button"])
    char_sheet["to_draw"].append(mp_box["text"])
    
    stat_points_box = new_button(25,280,(win["width"]/4)-40,50,
                                 "Stat Points: {}".format(character["stat_points"]),
                                 "stat points box","brown","white","black",18)
    stat_points_box["button"].setWidth(4)
    char_sheet["stat_points_box"] = stat_points_box
    char_sheet["to_draw"].append(stat_points_box["button"])
    char_sheet["to_draw"].append(stat_points_box["text"])
    
    box_text = "Str: {}".format(character["str"])
    str_total = calc_total_stat(character,"str")
    if str_total != character["str"]:
        box_text += " ({})".format(str_total)
    str_box = new_button(90,350,(win["width"]/4)-100,50,box_text,"str box","beige","black","black",18)
    str_box["button"].setWidth(4)
    char_sheet["str_box"] = str_box
    char_sheet["to_draw"].append(str_box["button"])
    char_sheet["to_draw"].append(str_box["text"])
    
    if character["stat_points"] > 0:
        str_up_box = new_button(25,350,50,50,"+","str up box","red4","beige","beige",20)
        str_up_box["button"].setWidth(4)
        char_sheet["str_up_box"] = str_up_box
        char_sheet["to_draw"].append(str_up_box["button"])
        char_sheet["to_draw"].append(str_up_box["text"])
        char_sheet["buttons"].append(str_up_box)
    
    
    box_text = "Stam: {}".format(character["stam"])
    stat_total = calc_total_stat(character,"stam")
    if stat_total != character["stam"]:
        box_text += " ({})".format(stat_total)
    stam_box = new_button(90,420,(win["width"]/4)-100,50,box_text,"stam box","beige","black","black",18)
    stam_box["button"].setWidth(4)
    char_sheet["stam_box"] = stam_box
    char_sheet["to_draw"].append(stam_box["button"])
    char_sheet["to_draw"].append(stam_box["text"])
    
    if character["stat_points"] > 0:
        stam_up_box = new_button(25,420,50,50,"+","stam up box","red4","beige","beige",20)
        stam_up_box["button"].setWidth(4)
        char_sheet["stam_up_box"] = stam_up_box
        char_sheet["to_draw"].append(stam_up_box["button"])
        char_sheet["to_draw"].append(stam_up_box["text"])
        char_sheet["buttons"].append(stam_up_box)
    
    box_text = "Dex: {}".format(character["dex"])
    stat_total = calc_total_stat(character,"dex")
    if stat_total != character["dex"]:
        box_text += " ({})".format(stat_total)
    dex_box = new_button(90,490,(win["width"]/4)-100,50,box_text,
                          "dex box","beige","black","black",18)
    dex_box["button"].setWidth(4)
    char_sheet["dex_box"] = dex_box
    char_sheet["to_draw"].append(dex_box["button"])
    char_sheet["to_draw"].append(dex_box["text"])
    
    if character["stat_points"] > 0:
        dex_up_box = new_button(25,490,50,50,"+","dex up box","red4","beige","beige",20)
        dex_up_box["button"].setWidth(4)
        char_sheet["dex_up_box"] = dex_up_box
        char_sheet["to_draw"].append(dex_up_box["button"])
        char_sheet["to_draw"].append(dex_up_box["text"])
        char_sheet["buttons"].append(dex_up_box)
    
    box_text = "Int: {}".format(character["int"])
    stat_total = calc_total_stat(character,"int")
    if stat_total != character["int"]:
        box_text += " ({})".format(stat_total)
    int_box = new_button(90,560,(win["width"]/4)-100,50,box_text,
                          "int box","beige","black","black",18)
    int_box["button"].setWidth(4)
    char_sheet["int_box"] = int_box
    char_sheet["to_draw"].append(int_box["button"])
    char_sheet["to_draw"].append(int_box["text"])
    
    if character["stat_points"] > 0:
        int_up_box = new_button(25,560,50,50,"+","int up box","red4","beige","beige",20)
        int_up_box["button"].setWidth(4)
        char_sheet["int_up_box"] = int_up_box
        char_sheet["to_draw"].append(int_up_box["button"])
        char_sheet["to_draw"].append(int_up_box["text"])
        char_sheet["buttons"].append(int_up_box)
        
        
    coin_box = new_button(540,280,300,40,"Coins: {}".format(character["coins"]),
                            "coin box", "beige","black","black",15)
    char_sheet["damage_box"] = coin_box
    char_sheet["to_draw"].append(coin_box["button"])
    char_sheet["to_draw"].append(coin_box["text"])
        
        
    damage = calculate_damage_range(character)
    damage_box = new_button(540,330,300,80,"Damage:\n{} - {}".format(damage[0],damage[1]),
                            "damage box", "beige","black","black",15)
    char_sheet["damage_box"] = damage_box
    char_sheet["to_draw"].append(damage_box["button"])
    char_sheet["to_draw"].append(damage_box["text"])
    
    
    armor,damage_reduction = calculate_armor(character)
    armor_box = new_button(540,420,300,80,"Armor: {}\nDamage Reduction: {}%".format(armor,int(damage_reduction*100)),
                            "armor box", "beige","black","black",15)
    char_sheet["armor_box"] = armor_box
    char_sheet["to_draw"].append(armor_box["button"])
    char_sheet["to_draw"].append(armor_box["text"])
    
    for item in char_sheet["to_draw"]:
        item.draw(win["win"])
    return(char_sheet)


#{"name": "Engineer", "map_x1": 380, "map_y1": 450, "radius": 100, "fill_color":"blue1", "outline_color":"lime",
#"type": "vendor", "shape": "circ","inventory": "tbd", "img": "img/Mob_Bug_Hulking.png", "dialog": {
#"None": "engi_1", "engi_intro": "engi_3"
#}},
#...
#"dialog": {
#"engi_intro_1": 
#{"img": "img/Portrait_Engineer.png", "name": "Engineer", "bg_color": "dark slate gray",
#"text": "What up robot dude!\nLet's get to work robot dude!\nFuckin robots lol",
#"responses": {
#"1": {"text": "Okay", "next": "engi_intro_2"},
#"2": {"text": "Hey fuck you lol", "next": "engi_intro_1a"}
#}},


## Based on the bools stored by the character, determine which dialog to display
## Bools are recorded after a dialog occurs the first time
## Some dialogs are only intended to be seen once
def choose_dialog_tree(vendor,char_bools):
    print(">>>>    def choose_dialog_tree received vendor dialog of {} and char_bools of {}".format(
        vendor["dialog"],char_bools))
    dialog_start = vendor["dialog"]["None"] # Default Dialog option, if no bools are present
    for item in vendor["dialog"].keys(): # Check through vendors possible dialog options
        print("def choose_dialog_tree comparing char_bool {} against vendor['dialog'].keys(): {}".format(
            item, vendor["dialog"].keys()))
        if item != "None" and item in char_bools.keys(): # If vendor has dialog options, and bool is present
            dialog_start = vendor["dialog"][item] # Set that to the dialog option
        # Repeats to the end of the list of vendor dialog options
        # The latest option will be returned
    return(dialog_start)


## Called to start a dialog tree where the player receives info and can choose how to respond
## Other effects may occur after the dialog concludes, thus the returned dialog_result
def start_dialog_tree(win,data,dialog_start):
    dialog = data["dialog"][dialog_start] # Get the dialog text from data
    
    # Display the dialog box for the player to respond to
    win,response = draw_dialog_box(
        win,dialog["img"],dialog["name"],dialog["bg_color"],dialog["text"],dialog["responses"])
    
    # If there are further dialog boxes to be displayed
    while response != "exit":
        # Get the next dialog text
        dialog = data["dialog"][response]
        # Display it for player to respond to
        win,response = draw_dialog_box(
            win,dialog["img"],dialog["name"],dialog["bg_color"],dialog["text"],dialog["responses"])
        # Repeat if the response is anything other than 'exit'
    
    # Return the start of the dialog tree as the bool
    # This is to record that this dialog_tree occured
    dialog_result = dialog_start
    #print(">>  def start_dialog_tree returning dialog_result: {}".format(dialog_result))
    return(win,dialog_result)



## Sometimes things needs to occur after a dialog concludes
## This is where those things occur, based on the received dialog_result
def process_dialog_result(win,data,map_objs,character,dialog_result): 
    if dialog_result == "None":  # Most of the time, no processing is needed
        return(win,map_objs,character)
    xy_from_center = character["xy_from_center"] # Gather some needed variables
    character["bools"][dialog_result] = True # Record that this occured
    
    print("def process_dialog_result gave character bools: {}".format(character["bools"]))
    
    ## ENGI INTRO ##
    ## Creates and drops some basic gear for the player to pick up ##
    if dialog_result == "engi_intro_1":
        
        ## Basic set of Kevlar Gear, with a lvl 1 basic Pistol and a lvl 3 basic Pistol
        win,map_objs = create_and_drop_item_from_name(win,data,map_objs,"Kevlar Vest",xy_from_center)
        win,map_objs = create_and_drop_item_from_name(win,data,map_objs,"Kevlar Helmet",xy_from_center)
        win,map_objs = create_and_drop_item_from_name(win,data,map_objs,"Energy Shield",xy_from_center)
        win,map_objs = create_and_drop_item_from_name(win,data,map_objs,"S1 9mm Pistol",xy_from_center)
        win,map_objs = create_and_drop_item_from_name(win,data,map_objs,"S3 9mm Pistol",xy_from_center)

        ## And 5 boxes of 9mm ammo to use with the Pistol
        for i in range(5):
            win,map_objs = create_and_drop_item_from_name(win,data,map_objs,"9mm Ammo",xy_from_center)
    
    ## FURTHER EFFECTS GO HERE
    elif dialog_result == "example":
        pass
    
    return(win,map_objs,character)


## When you need to create an item and immediately drop it to the floor for the player to pick up
## Saves a few lines of code when it is called
def create_and_drop_item_from_name(win,data,map_objs,item_name,xy_from_center):
    item = new_item_from_name(data,item_name)
    pickup_radius = 64
    item = drop_item(win,item,int(win["width"]/2),int(win["height"]/2)-100,pickup_radius,xy_from_center)
    map_objs.append(item)
    print("Created and dropped item {} at {}x{}".format(item["name"],item["map_x1"],item["map_y1"]))   
    return(win,map_objs)


## Draws a dialog box onto the screen, along with a portrait of the character who is speaking
## Also draws responses that the player can choose from, to continue the dialog tree
## Should be compatible with different sized monitors, as it uses fractions instead of whole numbers
def draw_dialog_box(win,portrait_img_path,name,bg_color,text,responses):
    dialog_box = {}
    dialog_box["box"] = Rectangle(Point(win["width"]*0.125,win["height"]*0.45),Point(win["width"]*0.875,win["height"]*0.8))
    dialog_box["box"].setFill(bg_color)
    dialog_box["box"].setOutline("beige")
    dialog_box["box"].setWidth(5)
    dialog_box["box"].draw(win["win"])
    
    dialog_box["portrait"] = Image(Point(win["width"]*0.2,win["height"]*0.625),portrait_img_path)
    dialog_box["portrait"].draw(win["win"])
    
    dialog_box["name"] = Text(Point(win["width"]*0.5,win["height"]*0.4825),name)
    dialog_box["name"].setSize(24)
    dialog_box["name"].setTextColor("bisque")
    dialog_box["name"].setStyle("bold")
    dialog_box["name"].setFace("helvetica")
    dialog_box["name"].draw(win["win"])
    
    dialog_box["text"] = Text(Point(win["width"]*0.5,win["height"]*0.65),text)
    dialog_box["text"].setSize(18)
    dialog_box["text"].setTextColor("white")
    dialog_box["text"].setFace("courier")
    dialog_box["text"].draw(win["win"])
    
    buttons = []
    button_y1 = win["height"]*0.475
    for item in responses:
        item = responses[item]
        #print(">> response: {}".format(responses[item]))
        response_box = new_button(win["width"]*0.75,button_y1,400,40,
                                  item["text"],item["next"],"beige","black","black",15)
        buttons.append(response_box)
        button_y1 += 45
        response_box["button"].draw(win["win"])
        response_box["text"].draw(win["win"])
    
    update()            ## Update the window to display the items
    play = True
    while play:
        click = win["win"].getMouse()
        
        if len(responses) > 0:  ## If there are possible responses, allow player to choose one
            clicked_on = interpret_click(win,buttons,click)
            if clicked_on != None:  ## For now, just check if they clicked a button or not
                response = clicked_on
                play = False        ## If they did, then we will close the box
        else:
            response = None
            play = False

            
    dialog_box["box"].undraw()
    dialog_box["portrait"].undraw()
    dialog_box["text"].undraw()
    dialog_box["name"].undraw()
    for item in buttons:
        item["text"].undraw()
        item["button"].undraw()
    
    update()            ## Update the window to undraw all items
    return(win,response)


## Based on received item rarity, change color of received box
def set_rarity_fill_color(item,box,default_color):
    if item == None:
        fill = default_color
    elif item["rarity"] == "common":
        fill = "old lace"
    elif item["rarity"] == "uncommon":
        fill = "dark sea green"
    elif item["rarity"] == "rare":
        fill = "light blue"
    elif item["rarity"] == "epic":
        fill = "pale violet red"
    elif item["rarity"] == "legendary":
        fill = "light salmon"
    box["button"].setFill(fill)
    return(box)


## Prepare vendor for transactions by giving them items for their inventory
def prepare_vendor(vendor_data):
    vendor = vendor_data.copy()
    
    ## Establish inventory grid ##
    for i in range(1,11):
        for j in range(1,11):
            vendor["inventory"]["{} {}".format(i,j)] = None
            
    ## Populate the grid with some items ##
    for i in range(random.randrange(6,11)):
        for j in range(random.randrange(3,5)):
            i_level = 1
            item_type = random.choice(["weapon","armor","helm","shield"])
            vendor["inventory"]["{} {}".format(i,j)] = new_random_item_from_level(data,i_level,item_type)
    
    return(vendor)
        
    
## Display the items a vendor has for sale
## Should allow player to purchase and sell items from and to the vendor
def draw_vendor_inventory(win,vendor_data):
    vendor = prepare_vendor(vendor_data)
    
    vend_sheet = {}
    vend_sheet["to_draw"],char_sheet["buttons"] = [],[]
    
    box = Rectangle(Point(0,0),Point(win["width"]/2,win["height"]))
    box.setFill("slate gray")
    box.setOutline("bisque")
    box.setWidth(4)
    vend_sheet["box"] = box
    vend_sheet["to_draw"].append(box)
    
    title = Text(Point(win["width"]/4,80),vendor["name"])
    title.setTextColor("white")
    title.setSize(24)
    title.setStyle("bold")
    vend_sheet["to_draw"].append(title)
    
    
    vend_screen_x,vend_screen_y = 65,200
    start_screen_x,start_screen_y = inv_screen_x,inv_screen_y
    size_x,size_y = 75,75
    ## Draw inventory grid ##
    for grid_x in range(1,11):
        for grid_y in range(1,11):
            
            inv_slot = new_button(inv_screen_x,inv_screen_y,size_x,size_y,"","inv slot {} {}".format(grid_x,grid_y),
                                  "silver","black","black",12)
            item = vendor["inventory"]["{} {}".format(grid_x,grid_y)] ## Get item data
            inv_slot["contents"] = item 
            
            inv_slot = set_rarity_fill_color(item,inv_slot,"silver")

            vend_sheet["to_draw"].append(inv_slot["button"])
            vend_sheet["to_draw"].append(inv_slot["text"])
            vend_sheet["buttons"].append(inv_slot)
            if inv_slot["contents"] != None:
                img = Image(Point(inv_screen_x + (size_x/2), inv_screen_y + (size_y/2)),inv_slot["contents"]["img"])
                inv["to_draw"].append(img)
                if "quantity" in item.keys():
                    quantity_text = Text(Point(inv_screen_x + (size_x*0.8), inv_screen_y + (size_y*0.8)),item["quantity"])
                    quantity_text.setStyle("bold")
                    quantity_text.setSize(18)
                    vend_sheet["to_draw"].append(quantity_text)
            inv_screen_x += size_x
        inv_screen_x = start_screen_x
        inv_screen_y += size_y
    
    
    for item in vend_sheet["to_draw"]:
        item.draw(win["win"])
    return(vend_sheet)


## Draw inventory box ##
## Should be on right side of screen ##
## Should show inventory grid and character item slots ##
def draw_inventory(win,character):
    inv = {}
    inv["to_draw"],inv["buttons"] = [],[]
    
    box = Rectangle(Point(win["width"]/2,0),Point(win["width"],win["height"]))
    box.setFill("slate gray")
    box.setOutline("bisque")
    box.setWidth(4)
    inv["box"] = box
    inv["to_draw"].append(box)
    
    
    helm_box = new_button((win["width"]*0.75)-75,30,150,150,"","helm box","tan","white","white",24)
    helm_box["button"].setWidth(3)
    inv["helm_box"] = helm_box
    inv["to_draw"].append(helm_box["button"])
    inv["to_draw"].append(helm_box["text"])
    inv["buttons"].append(helm_box)
    if character["helm"] != None:
        helm_img = Image(Point((win["width"]*0.75),105),character["helm"]["img"])
        helm_box = set_rarity_fill_color(character["helm"],helm_box,"tan")
        inv["to_draw"].append(helm_img)
    
    
    armor_box = new_button((win["width"]*0.75)-75,230,150,200,"","armor box","tan","white","white",24)
    armor_box["button"].setWidth(3)
    inv["armor_box"] = armor_box
    inv["to_draw"].append(armor_box["button"])
    inv["to_draw"].append(armor_box["text"])
    inv["buttons"].append(armor_box)
    if character["armor"] != None:
        armor_img = Image(Point((win["width"]*0.75),330),character["armor"]["img"])
        armor_box = set_rarity_fill_color(character["armor"],armor_box,"tan")
        inv["to_draw"].append(armor_img)
    
    
    weapon_box = new_button((win["width"]*0.75)-325,230,150,200,"","weapon box","tan","white","white",24)
    weapon_box["button"].setWidth(3)
    inv["weapon_box"] = weapon_box
    inv["to_draw"].append(weapon_box["button"])
    inv["to_draw"].append(weapon_box["text"])
    inv["buttons"].append(weapon_box)
    if character["weapon"] != None:
        weapon_img = Image(Point((win["width"]*0.75)-250,330),character["weapon"]["img"])
        weapon_box = set_rarity_fill_color(character["weapon"],weapon_box,"tan")
        inv["to_draw"].append(weapon_img)
    
    
    shield_box = new_button((win["width"]*0.75)+175,230,150,200,"","shield box","tan","white","white",24)
    shield_box["button"].setWidth(3)
    inv["shield_box"] = shield_box
    inv["to_draw"].append(shield_box["button"])
    inv["to_draw"].append(shield_box["text"])
    inv["buttons"].append(shield_box)
    if character["shield"] != None:
        shield_img = Image(Point((win["width"]*0.75)+250,330),character["shield"]["img"])
        shield_box = set_rarity_fill_color(character["shield"],shield_box,"tan")
        inv["to_draw"].append(shield_img)
    
    
    inv_screen_x,inv_screen_y = (win["width"]/2)+65,480
    start_screen_x,start_screen_y = inv_screen_x,inv_screen_y
    size_x,size_y = 75,75
    ## Draw inventory grid ##
    for grid_x in range(1,6):
        for grid_y in range(1,11):
            
            inv_slot = new_button(inv_screen_x,inv_screen_y,size_x,size_y,"","inv slot {} {}".format(grid_x,grid_y),
                                  "silver","black","black",12)
            item = character["inventory"]["{} {}".format(grid_x,grid_y)]
            inv_slot["contents"] = item #character["inventory"]["{} {}".format(x,y)]
            
            inv_slot = set_rarity_fill_color(item,inv_slot,"silver")

            inv["to_draw"].append(inv_slot["button"])
            inv["to_draw"].append(inv_slot["text"])
            inv["buttons"].append(inv_slot)
            if inv_slot["contents"] != None:
                img = Image(Point(inv_screen_x + (size_x/2), inv_screen_y + (size_y/2)),inv_slot["contents"]["img"])
                inv["to_draw"].append(img)
                if "quantity" in item.keys():
                    quantity_text = Text(Point(inv_screen_x + (size_x*0.8), inv_screen_y + (size_y*0.8)),item["quantity"])
                    quantity_text.setStyle("bold")
                    quantity_text.setSize(18)
                    inv["to_draw"].append(quantity_text)
            inv_screen_x += size_x
        inv_screen_x = start_screen_x
        inv_screen_y += size_y
    
    for item in inv["to_draw"]:
        item.draw(win["win"])
    return(inv)


## We need a way to add line breaks procedurally to the text ##
## Currently splits words if needed: would be better if it only inserted line breaks in spaces ##
def word_wrap(max_chars,text):
    ## Max chars on a line is based on how big the screen is ##
    try:
        insert = "\n"
        text = insert.join(text[i:i+max_chars] for i in range(0,len(text),max_chars))
    except:
        pass
    return(text)


## game_bar is a GUI that allows player to see how much health, mana, and xp they have
## Also includes a quickbar, to which items can be assigned (pending)
## Also shows if shift or ctrl modifiers are active
def draw_game_bar(win,character):
    game_bar = {}
    game_bar["to_draw"],game_bar["buttons"] = [],[]
    
    bg_box = new_button(0,win["height"]-300,win["width"],300,"","bg","slate gray","white","white",12)
    bg_box["button"].setWidth(4)
    game_bar["bg_box"] = bg_box
    game_bar["to_draw"].append(bg_box["button"])
    game_bar["to_draw"].append(bg_box["text"])
    
    
    hp_percent = character["hp"][0] / character["hp"][1]
    
    hp_outer = new_button(25,win["height"]-280,75,180,"","hp outer","black","white","white",12)
    hp_outer["button"].setWidth(5)
    game_bar["hp_outer"] = hp_outer
    game_bar["to_draw"].append(hp_outer["button"])
    game_bar["to_draw"].append(hp_outer["text"])
    
    hp_inner = new_button(25,win["height"]-280,75,180,"","hp inner","red4","white","white",12)
    hp_inner["top"] = win["height"]-180
    hp_inner["button"].setWidth(5)
    game_bar["hp_inner"] = hp_inner
    game_bar["to_draw"].append(hp_inner["button"])
    game_bar["to_draw"].append(hp_inner["text"])
    
    
    mp_percent = character["mp"][0] / character["mp"][1]
    
    mp_outer = new_button(win["width"]-100,win["height"]-280,75,180,"","mp outer","black","white","white",12)
    mp_outer["button"].setWidth(5)
    game_bar["mp_outer"] = mp_outer
    game_bar["to_draw"].append(mp_outer["button"])
    game_bar["to_draw"].append(mp_outer["text"])
    
    mp_inner = new_button(win["width"]-100,win["height"]-280,75,180,"","mp inner","blue3","white","white",12)
    mp_inner["top"] = win["height"]-180
    mp_inner["button"].setWidth(5)
    game_bar["mp_inner"] = mp_inner
    game_bar["to_draw"].append(mp_inner["button"])
    game_bar["to_draw"].append(mp_inner["text"])
    
    
    weapon = character["weapon"]
    weapon_text = ""
    if weapon != None:
        weapon_text = set_weapon_text(weapon)
    attack_box = new_button(150,win["height"]-270,200,150,weapon_text,"attack","black","white","white",12)
    attack_box["button"].setWidth(5)
    attack_box["text"].setFace("courier")
    game_bar["attack_box"] = attack_box
    attack_box["selectable"] = True
    attack_box["selected"] = False
    game_bar["to_draw"].append(attack_box["button"])
    game_bar["to_draw"].append(attack_box["text"])
    game_bar["buttons"].append(attack_box)
    
    skill_box = new_button(win["width"]-350,win["height"]-270,200,150,"","skill","black","white","white",12)
    skill_box["button"].setWidth(5)
    game_bar["skill_box"] = skill_box
    skill_box["selectable"] = True
    skill_box["selected"] = False
    game_bar["to_draw"].append(skill_box["button"])
    game_bar["to_draw"].append(skill_box["text"])
    game_bar["buttons"].append(skill_box)
    
    xp_outer = new_button(win["width"]/4,win["height"]-270,(win["width"]/2),20,"","xp outer","tan","black","black",12)
    xp_outer["button"].setWidth(2)
    game_bar["xp_outer"] = xp_outer
    game_bar["to_draw"].append(xp_outer["button"])
    
    ## xp_inner is offset so that it fits inside the xp box
    xp_inner = new_button((win["width"]/4)+4,win["height"]-266,5,12,"","xp inner","blue4","white","white",12)
    game_bar["xp_inner"] = xp_inner
    game_bar["to_draw"].append(xp_inner["button"])
    
    bottom_bar = Rectangle(Point(0,win["height"]-105),Point(win["width"],win["height"]))
    bottom_bar.setFill("slate gray")
    bottom_bar.setOutline("slate gray")
    game_bar["bottom_bar"] = bottom_bar
    game_bar["to_draw"].append(bottom_bar)
    
    shift_mod_text = Text(Point(450,win["height"]-150),"")
    shift_mod_text.setSize(28)
    game_bar["shift_mod_text"] = shift_mod_text
    game_bar["to_draw"].append(shift_mod_text)
    
    ctrl_mod_text = Text(Point(450,win["height"]-200),"")
    ctrl_mod_text.setSize(28)
    game_bar["ctrl_mod_text"] = ctrl_mod_text
    game_bar["to_draw"].append(ctrl_mod_text)
    
    screen_x = 550
    screen_y = win["height"] - 200
    width = 80
    for i in range(1,9):
        nb = new_button(screen_x,screen_y,width,width,str(i),"quick {}".format(i),"tan","black","black",10)
        screen_x += width
        nb["img_path"] = "img/blank.png"
        nb["img"] = Image(Point(screen_x + (width/2), screen_y + (width/2)), nb["img_path"])
        game_bar["quick {}".format(i)] = nb
        game_bar["to_draw"].append(nb["button"])
        game_bar["to_draw"].append(nb["text"])
        game_bar["buttons"].append(nb)
    
    for item in game_bar["to_draw"]:
        item.draw(win["win"])
    return(game_bar)



## Undraw, then draw the game_bar, which is most of the player GUI
def redraw_game_bar(win,game_bar):
    for item in game_bar["to_draw"]:
        item.undraw()
        item.draw(win["win"])
    return(win)


## Determine the corners of an info bar to reflect the value of the bar
## Used by health, mana, and xp bars
def adjust_bar(win,bar,current_value,max_value,direction,min_x,max_x,min_y,max_y):
    ## Determine what percent of full the value is
    if current_value != 0:
        percent = current_value/max_value
    else:
        percent = 0
        
    #print("{} / {} = {} percent".format(current_value,max_value,percent))
    #print("(before) {} x {}".format(bar["button"].getP1(),bar["button"].getP2()))
    
    ## Horiz: FUNCTIONAL! ##
    if direction == "horiz":
        new_screen_x1 = bar["button"].getP1().getX()
        new_screen_y1 = bar["button"].getP1().getY()
        
        max_width = max_x - min_x
        new_width = max_width * percent
        new_height = max_y - min_y
        
    ## Vert: FUNCTIONAL! ##
    else:
        screen_y2 = bar["button"].getP2().getY()
        
        new_width = max_x - min_x
        max_height = max_y - min_y
        new_height = max_height * percent
        
        new_screen_x1 = bar["button"].getP1().getX()
        new_screen_y1 = max_y - new_height
        
    ## Remove the old info bar
    bar["button"].undraw()
    
    ## Create a new info bar with the new corners
    new_bar = new_button(new_screen_x1, new_screen_y1, new_width, new_height, "", bar["function"],
                         bar["fill_color"],bar["text_color"],bar["outline_color"], 12)
          
    ## Draw the new bar
    new_bar["button"].draw(win["win"])
    return(new_bar)


## Receive xp
## Check if character leveled up
## If so, grant level up effects and reset xp to 0
def gain_xp(win,character,xp,game_bar):
    character["xp"][0] += xp  # Gain xp
    ## Check if character leveled up
    if character["xp"][0] >= character["xp"][1]:
        ## Grant character level up effects such as increased stats and stat points
        character["xp"][0] -= character["xp"][1]
        character["level"] += 1
        character["stat_points"] += 4
        character["skill_points"] += 1
        character["xp"][1] = ((character["level"]**1.5) * 150) + 100
        #character["hp"][1] += int((character["stam"] * 2) ** 1.2)
        character["hp"][1] += int((character["stam"] * 2) + (character["hp"][1]/5))
        character["hp"][0] = character["hp"][1]
        character["mp"][1] += int(character["int"] * 2)
        character["mp"][0] = character["mp"][1]
        
        print("Level Up!  Now level {} ({}/{} xp)".format(character["level"],character["xp"][0],character["xp"][1]))
        
    ## If xp ended up lower than 0, then set it back to 0
    elif character["xp"][0] < 0:
        character["xp"][0] = 0
       
    ## Adjust the on-screen xp bar to reflect any changes
    ## Get the corners of the outer bar
    ## Then place the inner bar within those edges
    screen_x1,screen_y1 = game_bar["xp_outer"]["button"].getP1().getX(),game_bar["xp_inner"]["button"].getP1().getY()
    screen_x2,screen_y2 = game_bar["xp_outer"]["button"].getP2().getX()-10,game_bar["xp_inner"]["button"].getP2().getY()
    game_bar["to_draw"].remove(game_bar["xp_inner"]["button"])
    game_bar["xp_inner"] = adjust_bar(
        win,game_bar["xp_inner"],character["xp"][0],character["xp"][1],"horiz",screen_x1,screen_x2,screen_y1,screen_y2)
    game_bar["to_draw"].append(game_bar["xp_inner"]["button"])
    
    return(character,game_bar)


## Given a list of objects on the map, determine which are close enough for player to see
## Render those objects, and unrender anything else that has passed out of view range
def draw_map_objs_in_range(win,map_objs,character):
    new_draw = False #  If anything new was drawn, pass that info along
    for item in map_objs:
        if item["type"] != "vfx": # First, check any vfx objects and modify if needed
            if "drawn" not in item.keys():
                item["drawn"] = False
            if "shape" not in item.keys():
                item["shape"] = "circ"
                #print("  Adding item shape to item {}".format(item["name"]))
            
            ## Determine where the corners of the object are relative to the screen
            if item["shape"] == "rect":
                screen_x1 = item["map_x1"] - character["map_x"]
                screen_y1 = item["map_y1"] - character["map_y"]
                screen_x2 = item["map_x2"] - character["map_x"]
                screen_y2 = item["map_y2"] - character["map_y"]
            elif item["shape"] == "circ":
                screen_x1 = item["map_x1"] - character["map_x"] - item["radius"]
                screen_y1 = item["map_y1"] - character["map_y"] - item["radius"]
                screen_x2 = item["map_x1"] - character["map_x"] + item["radius"]
                screen_y2 = item["map_y1"] - character["map_y"] + item["radius"]

            ## Determine if any of the edges are in view
            if (screen_x1 > -win["width"]) or (
                screen_x2 < win["width"]) or (
                screen_y1 > -win["height"]) or (
                screen_y2 < win["height"]):
                ## If any of the edges are in view, check if item is drawn
                if not item["drawn"]: # If the item is not drawn, draw it now and mark it as drawn
                    #print("+DRAWN {} at {},{} x {},{}!".format(item,int_x1,int_y1,int_x2,int_y2))
                    item["obj"].draw(win["win"])
                    item["drawn"] = True
                    new_draw = True
            ## If none of the edges are in view
            else:
                if item["drawn"]: # And if the object is drawn, then undraw it and mark it as not drawn
                    #print("-UNDRAWN {} at {},{} x {},{}!".format(item,int_x1,int_y1,int_x2,int_y2))
                    item["obj"].undraw()
                    item["drawn"] = False
    
    return(win,map_objs,new_draw)


## Take each drawn item on the map and move it by the received amount
## This includes projectiles
def move_map_objs(win,map_objs,projectiles,move):
    for item in map_objs:
        #print(item)
        #if item["drawn"]:
        item["obj"].move(move[0],move[1])
    for item in projectiles:
        #if item["drawn"]:
        item["obj"].move(move[0],move[1])
    return(map_objs,projectiles)


## Returns that minimum and maximum possible damage values for character
def calculate_damage_range(character):
    damage = []
    
    ## Each class has a different 'extra damage' stat
    if character["class"] == "heavy":
        stat = "str"
    elif character["class"] == "soldier":
        stat = "dex"
    elif character["class"] == "technomancer":
        stat = "int"
    
    ## Get min and max values for possible damage
    damage = [int(character[stat]/4),int(character[stat]/2)]
    
    # If character has a weapon equipped, add that damage to the total
    if character["weapon"] != None:
        damage[0] += character["weapon"]["damage"][0]
        damage[1] += character["weapon"]["damage"][1]
    
    return(damage)


## Calculate total armor of character, based on stats and equipped gear
def calculate_armor(character):
    armor = character["stam"]
    if character["armor"] != None:
        armor += character["armor"]["armor"]
    if character["helm"] != None:
        armor += character["helm"]["armor"]
    if character["shield"] != None:
        armor += character["shield"]["armor"]
    
    ## Per level, there is a maximum armor amount
    max_armor = character["level"] * 25
    ## Make sure character does not exceed maximum armor value
    if armor > max_armor:
        armor = max_armor
    ## Damage received is reduced by a flat % based on armor value
    damage_reduction = (armor / max_armor)/2
    
    return(armor,damage_reduction)


## Create a new item based on received parameters
## Item does not have to exist in data
## Can create unique items this way
def new_item(name,typ,rarity,img,effect,value,text,extra_keys):
    ## Create blank item
    item = {}
    ## Attach received basic parameters to the item
    item["name"] = name
    item["type"] = typ
    item["img"] = img
    item["value"] = value.split()[1]
    item["text"] = text
    item["effect"] = effect
    item["rarity"] = rarity
    
    ## If any advanced / extra parameters are included, attach those as well
    for key in extra_keys.keys():   
        item[key] = extra_keys[key] #Move all extra key_value pairs to the main item dict
    
    ## Determine what sort of usage to attach based on item type
    if typ == "potion" or typ == "scroll":
        item["usage"] = "single use"
    elif typ == "armor" or typ == "helm" or typ == "weapon" or typ == "shield":
        item["usage"] = "wearable"
        item["slot"] = typ
        ## Gear may have even further effects to attach to the new item
        for stat in effect:
            item[stat] = effect[stat]
    elif typ == "weapon":
        item["proj_radius"] = effect["radius"]
        if "passthru" not in extra_keys.keys():
            item["passthru"] = 0
    else:
        ## If it doesn't fit the established templates, call it a 'misc' usage item
        item["usage"] = "misc"
        
    #print("\n  def new_item returning item {}\n".format(item))
    return(item)


## Either receive or heal damage to player
## Returned dead = True if player was killed by damage received
## Adjust hp bar on the game bar to reflect new health level
def change_hp(win,character,hp_delta,game_bar):
    dead = False # Character has not died
    character["hp"][0] += int(hp_delta) # Add or remove the health
    if character["hp"][0] > character["hp"][1]: # If character has more health than maximum
        character["hp"][0] = character["hp"][1] # Set health to maximum
    elif character["hp"][0] <= 0: # If character health drops below 0
        print("Character died!") # Then character has died
        dead = True # And we return dead = True
        
    ## Now, we adjust the hp bar to reflect what just occurred
    x1,y1 = game_bar["hp_outer"]["button"].getP1().getX(),game_bar["hp_outer"]["button"].getP1().getY()
    x2,y2 = game_bar["hp_outer"]["button"].getP2().getX(),game_bar["hp_outer"]["button"].getP2().getY()
    ## Undraw the current bar
    game_bar["to_draw"].remove(game_bar["hp_inner"]["button"])
    ## Get the size of the new bar
    game_bar["hp_inner"] = adjust_bar(
        win,game_bar["hp_inner"],character["hp"][0],character["hp"][1],"vert",x1,x2,y1,y2)
    ## Prepare to draw the newly adjusted bar on the next tick
    game_bar["to_draw"].append(game_bar["hp_inner"]["button"])
    
    return(character,dead,game_bar)


## Attempt to use an item that was selected from inventory
## Returns the item if it could not be equipped or consumed
def use_item(win,character,item,game_bar):
    print("def use_item called")
    dead = False # Player might be killed, but hasn't yet
        
    if item["usage"] == "wearable": # If it is a wearable item, then try to equip it
        if check_item_reqs(character,item):
            character,item = equip_item(character,item["slot"],item)
            if item != None: # If an item is returned, then put that item in inventory
                character,item = pick_up_item(character,item) 
        else: # Otherwise, explain why player could not equip the item
            print("Could not equip {}, due to {}!".format(item["name"],item["req"]))
        
    elif item["usage"] == "consumable": # If item is used only once
        ## Check what type of effect is set to occur
        if "heal" in item["effect"].keys(): # If the item heals the character
            character,dead,game_bar = change_hp(win,character,item["effect"]["heal"],game_bar)
            item = None # Return no item, since it was consumed in usage
    
    return(character,item,game_bar)


## Based on item_slot, equip the item to the character
## If an item is already in that slot, remove and return it
def equip_item(character,item_slot,item):
    return_item = item # Store the info of the item to be placed into the slot first
    if character[item_slot] != None: # If there is an item there,
        return_item = character[item_slot] # Store the info of that item
    else: # If there is NO item in the slot
        return_item = None # Then record that no item will be returned
        
    if item != None: # If the item we are trying to equip is an item
        character[item_slot] = item.copy() # Place a copy of the item in that item slot
    else: # If the item we are trying to equip is not an item (it might happen idk)
        character[item_slot] = None # Then the item_slot becomes empty
        
    return(character,return_item)


## A box is drawn that displays the stats of the selected item
def show_item_stats(win,item,x1,y1):
    ## To make sure box appears entirely on screen
    y_raised = False
    ## If it might be off the side of the screen, move it back towards the center
    if x1 + 300 > win["width"]:
        x1 -= 300
    ## If it might be off the bottom of the screen, move it back up towards the center
    if y1 + 400 > win["height"]:
        y1 -= 400
        
    ## Initialize some variables that we will use
    item_box = []
    drop_y = 0
    
    ## Debug line
    #print("{} keys".format(len(item.keys())))
    
    ## Item name text
    item_name = Text(Point(x1 + 200, y1 + 30), item["name"])
    item_name.setSize(16)
    item_name.setStyle("bold")
    item_box.append(item_name)
    
    ## Rarity and item type text
    text = "{} {}".format(item["rarity"].capitalize(),item["type"].capitalize())
    if item["type"] == "weapon":
        text += " ({})".format(item["subtype"].capitalize())
    item_type = Text(Point(x1 + 200, y1 + 60), text)
    item_type.setSize(14)
    item_name.setStyle("bold")
    item_box.append(item_type)
    
    ## Cash value of item text
    item_value = Text(Point(x1 + 200, y1 + 90), "Value: {}".format(item["value"]))
    item_value.setSize(10)
    item_box.append(item_value)
    
    ## Item usage is generally either 'wearable' or 'consumable'
    item_usage = Text(Point(x1 + 200, y1 + 120), item["usage"].capitalize())
    item_usage.setSize(10)
    item_usage.setStyle("italic")
    item_box.append(item_usage)
    
    if "req" in item.keys():
        for i in item["req"].keys():
            print("Req: {}".format(item["req"]))
            item_req = Text(Point(x1+200,y1 + 160 + drop_y),"Requires: {} {}".format(i.capitalize(),item["req"][i]))
            #if character[i] < item["req"][i]:
            #    item_req.setTextColor("red")
            item_req.setSize(12)
            item_box.append(item_req)
            drop_y += 30
                
                
    if item["type"] == "potion":
        item_desc = Text(Point(x1 + 200, y1 + 170 + drop_y), "Heals {} damage".format(item["effect"]["heal"]))
        item_desc.setSize(16)
        item_desc.setTextColor("green4")
        item_desc.setStyle("bold")
        item_box.append(item_desc)
        
    elif item["type"] in ["armor","shield","helm"]:
        item_desc = Text(Point(x1 + 200, y1 + 170 + drop_y), "Armor: {}".format(item["armor"]))
        item_desc.setSize(14)
        item_desc.setTextColor("green4")
        item_desc.setStyle("bold")
        item_box.append(item_desc)
        
    elif item["type"] == "weapon":
        text = "\n"
        extra_drop_y = 0
        
        text += "Damage: {} - {}\n".format(item["damage"][0],item["damage"][1])
        
        for key in item.keys():
            if key == "ammo":
                key_formatted = key.capitalize().replace("_"," ")
                text += "{}: {} / {}\n".format(key_formatted, item[key][0], item[key][1])
                drop_y += 10
                extra_drop_y += 10
                
        for key in item["effect"].keys():
            key_formatted = key.capitalize().replace("_"," ")
            text += "{} +{}\n".format(key_formatted, item["effect"][key])
            drop_y += 10
            extra_drop_y += 10
        
        item_desc = Text(Point(x1 + 200, y1 + 170 + drop_y), text)
        item_desc.setSize(14)
        item_desc.setTextColor("green4")
        item_desc.setStyle("bold")
        item_box.append(item_desc)
        drop_y += extra_drop_y
        
        text = "\n"
        extra_drop_y = 0
        for key in item.keys():
            if key in ["fire_mode","fire_rate","reload_speed","ammo_type"]:
                key_formatted = key.capitalize().replace("_"," ")
                text += "{}: {}\n".format(key_formatted, item[key])
                drop_y += 10
                extra_drop_y += 10
                
        item_desc = Text(Point(x1 + 200, y1 + 230 + drop_y), text)
        item_desc.setSize(12)
        item_desc.setTextColor("black")
        item_box.append(item_desc)
        drop_y += extra_drop_y
        
    ## Descriptive / flavor text is displayed at the bottom of the box
    item_text = Text(Point(x1 + 200, y1 + 290 + drop_y), '"{}"'.format(item["text"]))
    item_text.setSize(10)
    item_text.setStyle("italic")
    item_box.append(item_text)
    
    ## Set the fill color based on the rarity of the item
    fill = "old lace"
    if item["rarity"] == "uncommon":
        fill = "dark sea green"
    elif item["rarity"] == "rare":
        fill = "light blue"
    elif item["rarity"] == "epic":
        fill = "pale violet red"
    elif item["rarity"] == "legendary":
        fill = "light salmon"
    
    ## Now that we know how big the box will be, we can draw the outline box behind it
    item_box_outer = Rectangle(Point(x1,y1),Point(x1 + 400, y1 + 320 + drop_y))
    item_box_outer.setFill(fill)
    item_box_outer.setOutline("slate gray")
    item_box_outer.setWidth(4)
    ## Insert it to front of list so it is drawn first, and text is drawn on top of it
    item_box.insert(0,item_box_outer)
    
    below_screen = item_box_outer.getP2().getY() - win["height"] + 100
    #print(">>>>  Calculated below_screen at {}".format(below_screen))
    if below_screen > 0:
        #print(">>>>  Shifting item box up by {}".format(below_screen))
        for item in item_box:
            item.move(0,-below_screen)
        
    print("Drawing item box at {}x{}".format(x1,y1))
    
    for i in item_box:
        i.draw(win["win"])
    update()
    
    return(item_box)


## If an item is tagged as 'vfx,' process its effects here
def process_vfx(win,vfx,map_objs):
    for item in vfx: # Iterate through the list of vfx items
        if item["ticks"] <= 0: ## If item has run out of ticks, undraw and remove it from the list
            vfx.remove(item)
            if item in map_objs:
                map_objs.remove(item)
            item["obj"].undraw()
        else:               ## If item has ticks remaining, remove 1 tick and process the instructions
            item["ticks"] -= 1
            if "scroll" in item.keys():
                item["obj"].move(item["scroll"][0],item["scroll"][1])
    return(win,vfx,map_objs)


## Creates a line of text, centered on the specified screen coordinates
## Text will move based on the received scroll_speed list  (ex: [0,10])
## Text will disappear after ticks have all passed
def new_scroll_text(win,screen_x,screen_y,text,text_color,text_size,scroll_speed,ticks):
    scroll_text = {}
    scroll_text["obj"] = Text(Point(screen_x,screen_y),text)
    scroll_text["obj"].setTextColor(text_color)
    scroll_text["obj"].setSize(text_size)
    scroll_text["obj"].setStyle("bold")
    scroll_text["scroll"] = scroll_speed
    scroll_text["ticks"] = ticks
    scroll_text["obj"].draw(win["win"])
    return(scroll_text)


## A small 'explosion' image, typically used to show projectile hits
def new_explosion(win,screen_x,screen_y):
    ## There are several different possible images
    chosen = random.randrange(1,9)  ## Choose one here
    explosion = {} # Create blank dict for info to be placed into
    # Based on the chosen image, create that image now
    explosion["obj"] = Image(Point(screen_x,screen_y),"img/Explosion_{}.png".format(chosen))
    explosion["obj"].draw(win["win"])
    explosion["type"] = "vfx" # Declare it to be 'vfx' so we know what to do with it
    explosion["ticks"] = 3 # Image disappears after 3 ticks
    return(explosion)


## Roll a random int between given rmin and rmax
def roll(rmin,rmax):
    return(random.randrange(rmin,rmax))


## Adds parameters to an item that allow it to be dropped to the ground
## Creates the coordinates, image, and other associated variables
## Item must then be added to map_objs in order for player to interact with it
def drop_item(win,item,screen_x,screen_y,interact_radius,center):
    new_item = item.copy()
    new_x = random.randrange(screen_x-20,screen_x+21,5)
    new_y = random.randrange(screen_y-20,screen_y+21,5)
    new_item["obj"] = Image(Point(new_x,new_y), item["img"])
    new_item["radius"] = interact_radius*2
    new_item["map_x1"], new_item["map_y1"] = new_x + center[0], new_y + center[1] + 100
    new_item["drawn"] = False
    
    return(new_item)


## Can be passed automatically by code
## Or called when player attempts to pick up item from the ground
def pick_up_item(character,item):
    #print("Attempting to pickup item {}".format(item["name"]))
    if item["type"] == "coins":
        character["coins"] += int(item["value"])
        #print(">> Picked up coins!")
        return(character,None)
    if "stackable" in item.keys():
        for slot in character["inventory"]:
            if character["inventory"][slot] != None:
                #print("Comparing items {} and {}".format(character["inventory"][slot], item))
                if character["inventory"][slot]["name"] == item["name"]:
                    character["inventory"][slot]["quantity"] += 1
                    print(">> Picked up item and stacked with similar items!")
                    return(character,None)
         
        for slot in character["inventory"]:
            if character["inventory"][slot] == None:
                character["inventory"][slot] = item.copy()
                #print(">> Picked up item and created new stack!")
                return(character,None)   
    else:
        for slot in character["inventory"]:
            if character["inventory"][slot] == None:
                character["inventory"][slot] = item.copy()
                #print(">> Picked up item!")
                return(character,None)
    print(">> FAILED to pickup item")
    return(character,item)


## Returns the nearest item that cn be interacted with
## Avoids returning certain types of map objects that cannot be picked up, like colliders
def get_nearest_interactable(win,map_objs,character):
    nearest_item = None
    distance_to = 10000
    item_distance = 10000
    offset = 0
    for item in map_objs:
        if "drawn" in item.keys():
            if item["drawn"] and item["type"] not in ["collider","destroyable"]:
                if item["type"] == "vendor":
                    offset = 100
                distance_to = calc_distance_between_points([character["map_x"],character["map_y"]-offset],
                                                           [item["map_x1"],item["map_y1"]])
                if distance_to < item_distance:
                    nearest_item = item
                    item_distance = distance_to
                    item_type = item["type"]
    #print("Nearest item is {}".format(nearest_item["name"]))
    return(nearest_item,item_type)


## Check distance from character to item and determines if it is within interact range
def check_interact_distance(character,item):
    offset = 0
    if "radius" in item.keys():
        if item["type"] == "vendor":
            offset = 100
        distance_to = calc_distance_between_points([character["map_x"],character["map_y"]-offset],
                                                   [item["map_x1"],item["map_y1"]])
        if distance_to <= item["radius"]:
            return(True)
    return(False)


## Attempt to interact with nearest item on the map
def interact_nearest_item(win,data,map_objs,character):
    interact_type = None
    item,item_type = get_nearest_interactable(win,map_objs,character)
    if check_interact_distance(character,item): # Check if nearest item is close enough to pick up
        if item_type not in ["collider","vendor","portal","mob","img"]:
            character,return_item = pick_up_item(character,item)
            if return_item == None: # If item was picked up successfully
                #print("\n Map objs:")
                #for i in map_objs:
                #    print(i)
                #print("Item: {}".format(item))
                map_objs.remove(item)
                item["obj"].undraw()
                interact_type = "pickup"
        elif item_type == "vendor":
            print("Interact with vendor {}".format(item))
            dialog_start = choose_dialog_tree(item,character["bools"])
            win,dialog_result = start_dialog_tree(win,data,dialog_start)
            win,map_objs,character = process_dialog_result(win,data,map_objs,character,dialog_result)
            interact_type = "vendor"
    return(win,map_objs,character,interact_type)


## On game_bar, weapon info is shown.  This updates that to keep info current
def set_weapon_text(weapon):
    weapon_name = word_wrap(15,weapon["name"])
    return("{}\n {}/{}".format(weapon_name,weapon["ammo"][0],weapon["ammo"][1]))


## Redraw character object, so it appears on top of all other drawn objects on screen
def redraw_character(win,character):
    character["obj"].undraw()
    character["obj"].draw(win["win"])
    return(win)


## If character dies, call this function
def on_death(win,character):
    character["xp"][0] = 0  # Remove all current level xp
    
    return(win,character)


## When moving to a new map, or spawning on first map, this moves all map objects
## This is so what is drawn colliders and objects match their position relative to player character
def move_to_spawn(win,map_objs,projectiles,character,spawn_point):
    to_spawn_x = character["map_x"] - spawn_point[0]
    to_spawn_y = character["map_y"] - spawn_point[1]
    
    character["map_x"] -= to_spawn_x
    character["map_y"] -= to_spawn_y
    
    move = [to_spawn_x,to_spawn_y]
    
    xy_from_center = [0,0]
    map_objs,projectiles = move_map_objs(win,map_objs,projectiles,move)
    xy_from_center[0] -= move[0]
    xy_from_center[1] -= move[1]
    
    return(win,map_objs,projectiles,character,xy_from_center)


## Check if player is close enough to a portal to interact with it
## Interaction is automically triggered if they are close enough
def check_portal_collision(win,character,map_objs):
    for item in map_objs:
        if item["type"] == "portal":
            distance_to = calc_distance_between_points(
                [character["map_x"],character["map_y"]-100],[item["map_x1"],item["map_y1"]])
            #print("Distance to portal: {}".format(distance_to))
            if distance_to < character["radius"]:
                return(item["teleport_to"])
    return(None)


## Given a map number, return map data from data file
def get_map_data(data,map_number):
    return(data["map"][map_number])


## When player enters a new map, this collects the map data and displays it on screen
def change_map(win,character,teleport_to,data):
    win = undraw_all(win)
    win,loading_screen = draw_loading_screen(win)
    map_objs,colliders = [],[]
    dmap = get_map_data(data,teleport_to.split()[1])
    win["win"].setBackground(dmap["bg"])
    character["map_x"],character["map_y"] = win["width"]/2,(win["height"]/2)
    if dmap != None:
        bg_img = Image(Point(win["width"]/2,win["height"]/2),dmap["bg_img"])
        for img in dmap["images"]:
            win,imgs = tile_image(win,img["img"],[img["map_x1"],img["map_y1"]],[img["map_x2"],img["map_y2"]])
            for item in imgs:
                map_objs.append(item)
                
        for obj in dmap["colliders"]:
            nc = new_collider(obj)
            map_objs.append(nc)
            colliders.append(nc)
            
        for obj in dmap["vendors"]:
            nc = new_collider(obj)
            map_objs.append(nc)
            colliders.append(nc)
            
        return(win,character,map_objs,dmap,colliders,bg_img)
    return(win,character,None,None,None,bg_img)


## When spawning into a map, we reset the destroyables to default
## So if they were destoryed, they are placed back as they were before they were destroyed
def deploy_destroyables(data,map_number,map_objs,destroyables):
    for destroyable in data["map"][map_number]["destroyables"]:
        nd = new_destroyable(destroyable)
        nd["loot"] = data["loot_tables"][nd["loot_table"]]
        map_objs.append(nd)
        destroyables.append(nd)
    return(map_objs,destroyables)


## Given an area of map and an image, calculate where to place images so they form a seamless image
def tile_image(win,image_path,point1,point2):
    temp_image = Image(Point(0,0),image_path)
    imgs = []
    img_width = temp_image.getWidth()
    img_height = temp_image.getHeight()
    del(temp_image)
    
    for i in range(point1[0]+int(img_width/2),point2[0],img_width):
        for j in range(point1[1]+int(img_height/2),point2[1],img_height):
            img = {"obj": Image(Point(i,j),image_path), "type":"img", "map_x1": i, "map_y1": j, "radius": 0}
            imgs.append(img)
    return(win,imgs)


## Main game function, called when player chooses to start new game or load a game ##
def game(win,character,data):
    win = undraw_all(win)
    to_draw,buttons,map_objs = [],[],[]
    projectiles,mobs,destroyables,colliders = [],[],[],[]
    vfx = []
    
    ## Set up game ##
    win,character,map_objs,dmap,colliders,bg_img = change_map(win,character,"town 0",data)
    win = undraw_all(win)
    bg_img.draw(win["win"])
    
    
    map_objs,destroyables = deploy_destroyables(data,"0",map_objs,destroyables)
    
    to_draw.append(character["obj"])
    
    for item in to_draw:
        item.draw(win["win"])
        
    ## Set up player status bar ##
    game_bar = draw_game_bar(win,character)
    for item in game_bar["buttons"]:
        buttons.append(item)
    
    ## Play loop ##
    ## Establish necessary variables ##
    menu_cooldown = [0,0]
    xy_from_center = [0,0]
    set_xset()
    item_box_open = False
    item_box = None
    item_selected = None
    slot_selected = None
    swap_with = None
    deselect_next_tick = False
    shift_modifier = False
    ctrl_modifier = False
    play = True
    paused = False
    inv_open = False
    char_sheet_open = False
    teleport_to = None
    shoot = True
    shoot_ticks = 0
    reloaded = False
    
    win,map_objs,projectiles,character,xy_from_center = move_to_spawn(
        win,map_objs,projectiles,character,data["map"]["0"]["spawn_point"])
    
    print("Character starts at {}x{}".format(character["map_x"],character["map_y"]))
    
    
    while play:
        ## Check if a teleport should occur        
        character["xy_from_center"] = xy_from_center
        teleport_to = check_portal_collision(win,character,map_objs)
        if teleport_to != None:
            print("Possible teleport incoming to {}...".format(teleport_to))
            dmap = get_map_data(data,teleport_to.split()[1])
            print("def get_map_data returned level {}".format(dmap["level"]))
            if dmap != None:
                win,character,map_objs,dmap,colliders,bg_img = change_map(win,character,teleport_to,data)
                win = undraw_all(win)
                bg_img.draw(win["win"])
                
                destroyables = []
                map_objs,destroyables = deploy_destroyables(data,teleport_to.split()[1],map_objs,destroyables)
                print("def change_map returned {} map_objs".format(len(map_objs)))
                if map_objs != None:
                    if dmap["level"] == 0:
                        spawn_point = dmap["return_point"]
                    else:
                        spawn_point = dmap["spawn_point"]
                    win,map_objs,projectiles,character,xy_from_center = move_to_spawn(
                        win,map_objs,projectiles,character,spawn_point)
                    new_draw = True
                    teleport_to = None
                    print("Teleport succeeded!")
                else:
                    print("Teleport failed!")
            
        win,vfx,map_objs = process_vfx(win,vfx,map_objs)
        
        win,map_objs,new_draw = draw_map_objs_in_range(win,map_objs,character)
        
        if shift_modifier:
            game_bar["shift_mod_text"].setText("SHIFT")
        else:
            game_bar["shift_mod_text"].setText("")
            
        if ctrl_modifier:
            game_bar["ctrl_mod_text"].setText("CTRL")
        else:
            game_bar["ctrl_mod_text"].setText("")
        
        if new_draw:
            win = redraw_game_bar(win,game_bar)
            win = redraw_character(win,character)
        
        key = win["win"].checkKey()
        click = win["win"].checkMouse()
        
        
        ## Check reload and shoot tick timers ##
        if shoot == False:
            shoot_ticks += 1
            game_bar["attack_box"]["button"].setFill("gray")
        else:
            game_bar["attack_box"]["button"].setFill("black")
            if reloaded:
                reloaded = False
        
        weapon_text = "Unarmed"
        if character["weapon"] != None:   ## If character is wielding a weapon
            weapon = character["weapon"]
            if weapon != None:  ## Display weapon info in attack box
                weapon_text = set_weapon_text(weapon)
            if shoot_ticks >= character["weapon"]["fire_rate"]:
                shoot = True
                shoot_ticks = 0
                
        if shoot == False:
            if reloaded:
                weapon_text = "RELOADING"
        
        game_bar["attack_box"]["text"].setText(weapon_text)
                
                
        ## Then interpret any commands sent by player
        
        if click != None:  # If a click occurred
            print("\n A CLICK occurred")
            
            ## FIRE WEAPON ##
            if not inv_open and not char_sheet_open and shoot and character["weapon"] != None: #and shift_modifier:
                new_projectiles = []
                character["direction"] = coords_to_direction(click.getX()-character["obj"].getAnchor().getX(),
                                                        character["obj"].getAnchor().getY()-click.getY())+90
                new_projectiles,reloaded=shoot_button(win,character,projectiles)
                shoot_ticks=0
                if reloaded:
                    scroll_text = new_scroll_text(
                        win,win["width"]/2,(win["height"]/2)-50,
                        "RELOADING...","white",14,[0,-1],
                        character["weapon"]["reload_speed"]+character["weapon"]["fire_rate"])
                    vfx.append(scroll_text)
                    shoot_ticks -= character["weapon"]["reload_speed"]
                shoot = False
                #print("Preparing to merge new_projectiles into projectiles")
                for p in new_projectiles:
                    if p not in projectiles:
                        projectiles.append(p)
                #for p in new_projectiles:
                #    projectiles.append(p)
            
            ## SELECT AN ITEM ##
            if item_selected != None:
                print("An item ({}) is currently selected".format(item_selected["name"]))
                if deselect_next_tick and swap_with == None:
                    print("No swap chosen: de-selecting item")
                    deselect_next_tick = False
                    item_selected = None
                    slot_selected = None
                else:
                    deselect_next_tick = True
                    print("Will de-select next tick if no swap chosen")
            else:
                print("No item is currently selected")
                
            ## CLOSE ITEM BOX ##
            if item_box != None: # If an item box is open
                print(" The ITEM BOX is OPEN, CLOSING IT NOW")
                for item in item_box: #Undraw the item box
                    item.undraw()
                item_box_open = False # Reset the related bools
                item_box = None # Set item box to None
            else:
                print(" The item box is NOT OPEN")
            
            ## DETERMINE WHAT WAS CLICKED ON ##
            clicked_on = interpret_click(win,buttons,click)
            
            if clicked_on == "dex up box":
                character["stat_points"] -= 1
                character["dex"] += 1
            elif clicked_on == "str up box":
                character["stat_points"] -= 1
                character["str"] += 1
            elif clicked_on == "stam up box":
                character["stat_points"] -= 1
                character["stam"] += 1
                character["hp"][1] += int((2 + character["level"]) ** 1.5)
                character["hp"][0] += int((2 + character["level"]) ** 1.5)
            elif clicked_on == "int up box":
                character["stat_points"] -= 1
                character["int"] += 1
                character["mp"][1] += int((2 + character["level"]))
                character["mp"][0] += int((2 + character["level"]))
                
            ## For items, modifiers are used to determine what to do with them ##
            if not shift_modifier and not ctrl_modifier and clicked_on != None:
                print("Clicked with NO modifier: {}".format(clicked_on.split()[:2]))
                if clicked_on.split()[:2] == ["inv", "slot"]: # If button clicked on is an inventory slot
                    print("clicked an inventory slot")
                    slot = "{} {}".format(clicked_on.split()[2],clicked_on.split()[3])
                    if character["inventory"][slot] != None: # If slot is not empty
                        item = character["inventory"][slot]
                        print("Using item {}".format(item["name"]))
                        character,item,game_bar = use_item(win,character,item,game_bar)
                        character["inventory"][slot] = item
                if clicked_on == "armor box" and character["armor"] != None:
                    character,item = equip_item(character,"armor",None)
                    character,item = pick_up_item(character,item)
                elif clicked_on == "helm box" and character["helm"] != None:
                    character,item = equip_item(character,"helm",None)
                    character,item = pick_up_item(character,item)
                elif clicked_on == "shield box" and character["shield"] != None:
                    character,item = equip_item(character,"shield",None)
                    character,item = pick_up_item(character,item)
                elif clicked_on == "weapon box" and character["weapon"] != None:
                    character,item = equip_item(character,"weapon",None)
                    character,item = pick_up_item(character,item)
                    
            elif shift_modifier and not ctrl_modifier and clicked_on != None:
                print("Clicked while shift modifier active")
                print("  item_selected: {}".format(item_selected))
                item = None
                if clicked_on.split()[:2] == ["inv", "slot"]: # If button clicked on is an inventory slot
                    print("SHIFT clicked an inventory slot")
                    slot = "{} {}".format(clicked_on.split()[2],clicked_on.split()[3])
                    if character["inventory"][slot] != None and menu_cooldown[0] > menu_cooldown[1]: # If slot is not empty
                        item = character["inventory"][slot]
                        #print(" Got item {}".format(item))
                        if item_selected == None: # If no item has been selected yet
                            print("* Selecting item {}, OPENING ITEM BOX WINDOW".format(item["name"]))
                            item_selected = item
                            slot_selected = slot
                            item_box = show_item_stats(win,item,click.getX(),click.getY())
                            item_box_open = True
                            menu_cooldown = [0,10]
                            
                        elif item_selected != None and swap_with == None:
                            swap_with = slot
                            character["inventory"][slot_selected], character["inventory"][slot] = character["inventory"][slot], character["inventory"][slot_selected] # Swap selected and just clicked items
                            print("Swapping item slots, de-selecting items and slots")
                            item_selected, slot_selected, swap_with = None,None,None
                            if item_box != None:
                                print("UNDRAWING ITEM BOX")
                                for i in item_box:
                                    i.undraw()
                            item_box_open = False
                            item_box = None
                        else: 
                            item_selected = None
                            slot_selected = None
                            print("De-selecting item, but NOT UNDRAWING ITEM BOX\n")
                            
                    elif character["inventory"][slot] == None and (item_selected != None):  # If an item is selected, and clicking an empty inv slot
                            print("Swapping item to empty slot")
                            swap_with = slot
                            character["inventory"][slot_selected],character["inventory"][slot] = (
                                character["inventory"][slot],character["inventory"][slot_selected]) 
                            # Swap selected and just clicked items
                            print("> Swapping item slots, de-selecting items and slots") 
                            item_selected, item, slot_selected, swap_with = None, None, None, None
                            menu_cooldown = [0,5]
                            if item_box != None:
                                print("UNDRAWING ITEM BOX")
                                for i in item_box:
                                    i.undraw()
                            item_box_open = False
                            item_box = None
                            
                elif clicked_on == "armor box" and character["armor"] != None:
                    item_box = show_item_stats(win,character["armor"],click.getX(),click.getY())
                elif clicked_on == "helm box" and character["helm"] != None:
                    item_box = show_item_stats(win,character["helm"],click.getX(),click.getY())
                elif clicked_on == "shield box" and character["shield"] != None:
                    item_box = show_item_stats(win,character["shield"],click.getX(),click.getY())
                elif clicked_on == "weapon box" and character["weapon"] != None:
                    item_box = show_item_stats(win,character["weapon"],click.getX(),click.getY())
                    
            ## If ctrl modifier is active, shift modifier is inactive, and something was clicked on
            elif ctrl_modifier and not shift_modifier and clicked_on != None:
                for hotkey in character["hotkey"]:
                    if hotkey == None:
                        win,character,game_bar = assign_hotkey(win,character,hotkey,item,game_bar)
                
                
        ## Move projectiles and stuff like that
        if len(projectiles) > 0:
            projectiles = move_projectiles(win,projectiles)
                
            
        ## Refresh open tabs ##
        if char_sheet_open:
            win,char_sheet,buttons = refresh_char_sheet(win,character,char_sheet,buttons)
        if inv_open:
            win,inv,buttons = refresh_inv(win,character,inv,buttons)
        if item_box != None: # Refresh item box so it appears above open tabs
            for item in item_box:
                item.undraw()
                item.draw(win["win"])
        
        if key != "":
            if item_box != None:
                print(" Key pressed while ITEM BOX OPEN -- CLOSING ITEM BOX and De-Selecting Item and Slot")
                for item in item_box:
                    item.undraw()
                item_box_open = False
                item_box = None
                item_selected = None
                slot_selected = None
                
            #print(key)
        
        character["move"] = [0,0]
        
        if key == "Escape" and menu_cooldown[0] >= menu_cooldown[1]:
            menu_cooldown = [0,10]
            win,result = pause_menu(win)
            if result == "exit":
                play = False
            
        
        elif key == "w" or key == "Up":
            move = [0,character["move_speed"]]
            if check_move_colliders(character,map_objs,move):
                character["map_y"] -= character["move_speed"]
                map_objs,projectiles = move_map_objs(win,map_objs,projectiles,move)
                xy_from_center[1] -= character["move_speed"]
                character["move"] = [0,-character["move_speed"]]
                #print("Character at {}x{}".format(character["map_x"],character["map_y"]))
            
        elif key == "s" or key == "Down":
            move = [0,-character["move_speed"]]
            if check_move_colliders(character,map_objs,move):
                character["map_y"] += character["move_speed"]
                map_objs,projectiles = move_map_objs(win,map_objs,projectiles,move)
                xy_from_center[1] += character["move_speed"]
                character["move"] = [0,character["move_speed"]]
                #print("Character at {}x{}".format(character["map_x"],character["map_y"]))
        
        elif key == "a" or key == "Left":
            move = [character["move_speed"],0]
            if check_move_colliders(character,map_objs,move):
                character["map_x"] -= character["move_speed"]
                map_objs,projectiles = move_map_objs(win,map_objs,projectiles,move)
                xy_from_center[0] -= character["move_speed"]
                character["move"] = [-character["move_speed"],0]
                #print("Character at {}x{}".format(character["map_x"],character["map_y"]))
            
        elif key == "d" or key == "Right":
            move = [-character["move_speed"],0]
            if check_move_colliders(character,map_objs,move):
                character["map_x"] += character["move_speed"]
                map_objs,projectiles = move_map_objs(win,map_objs,projectiles,move)
                xy_from_center[0] += character["move_speed"]
                character["move"] = [character["move_speed"],0]
                #print("Character at {}x{}".format(character["map_x"],character["map_y"]))
                
        ##
        ## MANUAL RELOAD
        ##
        elif key == "r":
            if shoot:
                if character["weapon"] != None:
                    character,reloaded = reload_manually(character)
                    if reloaded:
                        scroll_text = new_scroll_text(
                            win,win["width"]/2,(win["height"]/2)-50,
                            "RELOADING...","white",14,[0,-1],
                            character["weapon"]["reload_speed"]+character["weapon"]["fire_rate"])
                        vfx.append(scroll_text)
                        shoot_ticks = -character["weapon"]["reload_speed"]
                        shoot = False
                
        ##
        ## SHIFT MODIFIER
        ##
        elif key == "Shift_L":
            if shift_modifier:
                shift_modifier = False
            else:
                shift_modifier = True
            menu_cooldown = [0,10]
        
        ##
        ## CTRL MODIFIER
        ##
        elif key == "Control_L":
            if ctrl_modifier:
                ctrl_modifier = False
            else:
                ctrl_modifier = True
            menu_cooldown = [0,10]
          
        ##
        ## INTERACT KEY
        ##
        elif key == "Return" and menu_cooldown[0] >= menu_cooldown[1]:
            win,map_objs,character,interact_type = interact_nearest_item(win,data,map_objs,character)
            if interact_type == "vendor":
                menu_cooldown = [0,8]
                
                
        
        elif key in character["hotkey"].keys() and not ctrl_modifier:
            win,character,game_bar = use_hotkey(win,character,key,game_bar)

            
            
        
        
        ##
        ## DEBUG TESTING KEYS ##
        ##
        elif key == "bracketright":
            xp = 10*character["level"]
            character,game_bar = gain_xp(win,character,xp,game_bar)
            
        elif key == "bracketleft":
            xp = -10
            character,game_bar = gain_xp(win,character,xp,game_bar)
            
        elif key == "minus":
            dmg = 10
            character,dead,game_bar = change_hp(win,character,dmg,game_bar)
            if dead:
                play = False
                
        elif key == "equal":
            dmg = -10
            character,dead,game_bar = change_hp(win,character,dmg,game_bar)
            if dead:
                play = False
                
                
        ##
        ## END DEBUG TESTING KEYS ##
        ##
        
        
        ## Check for projectiles hits ##
        if len(projectiles) > 0:
            projectiles,mobs,destroyables,colliders,map_objs,character,game_bar,vfx = check_for_projectile_hits(
                win,data,character,game_bar,projectiles,mobs,destroyables,colliders,map_objs,xy_from_center,vfx)
        
        
        if menu_cooldown[0] >= menu_cooldown[1]:
            if key.lower() == "c":
                menu_cooldown = [0,10]
                if char_sheet_open:
                    char_sheet_open = False
                    for item in char_sheet["to_draw"]:
                        item.undraw()
                    for item in char_sheet["buttons"]:
                        buttons.remove(item)
                else:
                    char_sheet_open = True
                    char_sheet = draw_char_sheet(win,character)
                    for item in char_sheet["buttons"]:
                        buttons.insert(0,item)


            elif key.lower() == "i":
                menu_cooldown = [0,10]
                if inv_open:
                    inv_open = False
                    for item in inv["to_draw"]:
                        item.undraw()
                    for item in inv["buttons"]:
                        buttons.remove(item)
                else:
                    inv_open = True
                    inv = draw_inventory(win,character)
                    for item in inv["buttons"]:
                        buttons.insert(0,item)

        if menu_cooldown[1] > 0:
            menu_cooldown[0] += 1
        update(30)
    
    return


## Undraw and redraw all items of the character sheet
## Usually called when any of the items are updated with new text
def refresh_char_sheet(win,character,char_sheet,buttons):
    for item in char_sheet["to_draw"]:
        item.undraw()
    for item in char_sheet["buttons"]:
        buttons.remove(item)
        
    char_sheet = draw_char_sheet(win,character)
    for item in char_sheet["buttons"]:
        buttons.insert(0,item)
    
    return(win,char_sheet,buttons)


## Undraw and redraw all items in teh character inventory sheet
## Usually called when inventory changes while the sheet is open
def refresh_inv(win,character,inv,buttons):
    for item in inv["to_draw"]:
        item.undraw()
    for item in inv["buttons"]:
        buttons.remove(item)
        
    inv = draw_inventory(win,character)
    for item in inv["buttons"]:
        buttons.insert(0,item)
    
    return(win,inv,buttons)



## First function called
## Gathers screen size data and opens window
## Calls titles, then main menu
def main():
    width,height = get_screen_size()
    win = open_window("Diablo Clone",width,height)
    
    titles(win)
    main_menu(win)
    
    print("Farewell!")
    return
    
## Starts the whole thing!
main()
    