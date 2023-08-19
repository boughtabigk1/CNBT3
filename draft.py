import random
import sys

TOTAL_BUDGET = 80
MAX_TIER = 18
GROUP_SIZE = 16
OUTPUT_PATH = 'output/teams.txt'
PLAYER_INPUT = 'params/players.txt'
TIER_INPUT = 'params/tierlist.txt'
TYPE_INPUT = 'params/types.txt'
TEAM_COMP_INPUT = 'params/brackets1.txt'
# TEAM_COMP_INPUT = 'params/brackets2.txt'
                
def clear_results(path: str):
    with open(path, 'w') as file:
        file.truncate(0)

def parse_groups(group_size: int):
    groups = []
    curr_group = []
    player_list = open(PLAYER_INPUT, 'r')
    player_names = player_list.read().splitlines()
    random.shuffle(player_names)
    for player_index, player_name in enumerate(player_names):
        if player_index % group_size == 0 and player_index > 0:
            groups.append(curr_group)
            curr_group = []
        curr_group.append(player_name)
    if len(curr_group) > 0:
        groups.append(curr_group)
    return groups

class Mon:
    def __init__(self, name: str, val: int):
        self.name = name
        self.val = val
        self.tera_type = ""

class Player:
    def __init__(self, name: str):
        self.name = name
        self.pts = 0
        self.mons = []
        
    def add(self, mon: Mon):
        self.pts += mon.val
        self.mons.append(mon)     
    
    def replace(self, mon_index: int, new_mon: Mon):
        old_mon = self.mons.pop(mon_index)
        self.pts -= old_mon.val
        self.add(new_mon)
        return old_mon
      
    def get_rand(self):
        index = random.randint(0, len(self.mons))
        return (index, self[index].val)      
    
    def __print_team__(self):
        print(self.name + " team~ ")
        for mon in self.mons:
            print(str(mon.val) + "   " +  mon.name)
  
class Bracket():
    def __init__(self, min: int, max: int, qty: int):
        self.min = min
        self.max = max
        self.qty = qty
    
class Draft():
    def __init__(self, players):
        self.__init_tiers__()
        self.__init_brackets__()
        self.__init_types__()
        self.__init_players__(players)
        
    def __init_tiers__(self):
        self.tierlist = [[] for _ in range(MAX_TIER)]
        price_list = open(TIER_INPUT, 'r')
        prices = price_list.read().splitlines()
        for price in prices:
            pair = price.split("\t")
            self.tierlist[int(pair[1])-1].append(pair[0])
            
    def __init_types__(self):
        type_list = open(TYPE_INPUT, 'r')
        self.types = type_list.read().splitlines()

    def __init_brackets__(self):
        self.num_mons = 0
        self.brackets = []
        team_comp = open(TEAM_COMP_INPUT, 'r')
        bounds_list = team_comp.read().splitlines()
        for bounds in bounds_list:
            vals = bounds.split(" ")
            self.brackets.append(Bracket(int(vals[0]), int(vals[1]), int(vals[2])))
            self.num_mons += int(vals[2])
            
    def __init_players__(self, group):
        self.players = []
        for player_name in group:
            self.players.append(Player(player_name))
        
    def __get_mon__(self, target_value: int):
        offset= 0
        direction = -1
        actual_value = target_value+(offset*direction)
        under_min, over_max = False, False
        while actual_value < 1 or actual_value > MAX_TIER or (len(self.tierlist[actual_value-1])) == 0:
            direction *= -1
            offset += 1 if direction > 0 else 0
            actual_value = target_value+(offset*direction)
            if actual_value < 1:
                under_min = True
            if actual_value > MAX_TIER:
                over_max = True
            if under_min and over_max:
                sys.exit("OUT OF MONS ERROR")
        len_tier = len(self.tierlist[actual_value-1])
        pick_index = 0 if len_tier == 1 else random.randint(0, len_tier-1)
        pick_name = self.tierlist[actual_value-1].pop(pick_index)
        return Mon(pick_name, actual_value)
        
    def __pick__(self, player_index: int, bracket: Bracket):
        pick_value = random.randint(bracket.min, bracket.max)
        pick = self.__get_mon__(pick_value)
        self.players[player_index].add(pick)
        
    def __unpick__(self, mon: Mon):
        self.tierlist[mon.val-1].append(mon.name)
        
    def __upgrade1__(self, player_index: int):
        mon_index = random.randint(0, self.num_mons-1)
        while self.players[player_index].mons[mon_index].val == MAX_TIER:
            mon_index = (mon_index - 1)%self.num_mons
        pick_value = self.players[player_index].mons[mon_index].val + 1
        pick = self.__get_mon__(pick_value)
        old_mon = self.players[player_index].replace(mon_index, pick)
        self.__unpick__(old_mon)
        
    def __downgrade1__(self, player_index):
        mon_index = random.randint(0, self.num_mons-1)
        while self.players[player_index].mons[mon_index].val == 1:
            mon_index = (mon_index + 1)%self.num_mons
        pick_value = self.players[player_index].mons[mon_index].val - 1
        pick = self.__get_mon__(pick_value)
        old_mon = self.players[player_index].replace(mon_index, pick)
        self.__unpick__(old_mon)
        
    def __get_bracket_for_round__(self):
        for bracket in self.brackets:
            if bracket.qty > 0:
                bracket.qty -= 1
                return bracket
        return None
    
    def draft(self):
        for round in range(self.num_mons):
            bracket = self.__get_bracket_for_round__()
            for player_index, player in enumerate(self.players):
                self.__pick__(player_index, bracket)
        
    def fix_draft(self):
        for player_index, player in enumerate(self.players):
            while player.pts != TOTAL_BUDGET:
                player.__print_team__()
                if player.pts < TOTAL_BUDGET:
                    self.__upgrade1__(player_index)
                elif player.pts > TOTAL_BUDGET:
                    self.__downgrade1__(player_index)
        
    def assign_teras(self):
        for player_index in range(len(self.players)):
            for mon_index in range(self.num_mons):
                type = self.types[random.randint(0, len(self.types)-1)]
                self.players[player_index].mons[mon_index].tera_type = type
    def sort_teams(self):
        for player in self.players:
            player.mons = sorted(player.mons, key=lambda mon: mon.val, reverse=True)
        
    def print_results(self):
        for player in self.players:
            sum = 0
            print("~" + player.name + "~")
            for mon in player.mons:
                sum += mon.val
                print(str(mon.val) + "   " + mon.name + "   " + mon.tera_type)
            print("")
        print("_________________________________")    
    
    
    def write_results(self, path: str):
        output = ""
        for player in self.players:
            output += "~" + player.name + "~\n"
            for mon in player.mons:
                output += str(mon.val) + "   " + mon.name + "   " + mon.tera_type + "\n"
            output += "\n"
        output += "_________________________________\n"
        file_path = path  # Replace with your desired file path
        with open(file_path, 'a') as file:
            file.write(output) 
        
def main(): 
    clear_results(OUTPUT_PATH)
    groups = parse_groups(GROUP_SIZE)
    for group in groups:
        new_draft = Draft(group)
        new_draft.draft()
        new_draft.fix_draft()
        new_draft.sort_teams()
        new_draft.assign_teras()
        # new_draft.print_results()
        new_draft.write_results(OUTPUT_PATH)
        
if __name__ == "__main__":
    main()