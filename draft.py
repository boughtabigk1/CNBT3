import random
import sys

TOTAL_BUDGET = 80
MIN_TIER, MAX_TIER = 1, 19
GROUP_SIZE = 16
READABLE_OUTPUT_PATH = 'output/teams.txt'
DOC_OUTPUT_PATH = 'output/teams-data.txt'
PLAYER_INPUT = 'params/players.txt'
TIER_INPUT = 'params/tierlist.txt'
TYPE_INPUT = 'params/types.txt'
TEAM_COMP_INPUT = 'params/brackets1.txt'
# TEAM_COMP_INPUT = 'params/brackets2.txt'
USAGE_ERR = "Arguments: \n'draft' to generate teams \n'replace <value>' to get replacement mon ±1 point"
                
def clear_results(path: str):
    with open(path, 'w') as file:
        file.truncate(0)

def parse_groups(group_size: int):
    groups = []
    curr_group = []
    player_list = open(PLAYER_INPUT, 'r')
    signups = player_list.read().splitlines()
    random.shuffle(signups)
    for player_index, signup in enumerate(signups):
        parts = signup.split("\t")
        player = Player(parts[0], parts[1])
        if player_index % group_size == 0 and player_index > 0:
            groups.append(curr_group)
            curr_group = []
        curr_group.append(player)
    if len(curr_group) > 0:
        groups.append(curr_group)
    return groups

class Mon:
    def __init__(self, name: str, val: int):
        self.name = name
        self.val = val
        self.tera_type = ""

class Player:
    def __init__(self, name: str, team_name: str):
        self.name = name
        self.team_name = team_name
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
            if int(pair[1]) > MAX_TIER:
                continue
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
            
    def __init_players__(self, players):
        self.players = players
        
    def __get_mon__(self, target_value: int):
        offset= 0
        direction = -1
        actual_value = target_value+(offset*direction)
        under_min, over_max = False, False
        while actual_value < MIN_TIER or actual_value > MAX_TIER or (len(self.tierlist[actual_value-1])) == 0:
            direction *= -1
            offset += 1 if direction > 0 else 0
            actual_value = target_value+(offset*direction)
            if actual_value < MIN_TIER:
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
        while self.players[player_index].mons[mon_index].val == MIN_TIER:
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
                if player.pts < TOTAL_BUDGET:
                    self.__upgrade1__(player_index)
                elif player.pts > TOTAL_BUDGET:
                    self.__downgrade1__(player_index)
        
    def assign_teras(self):
        for player_index in range(len(self.players)):
            for mon_index in range(self.num_mons):
                type = self.types[random.randint(0, len(self.types)-1)]
                self.players[player_index].mons[mon_index].tera_type = type
            
    def replace_mon(self, val: int):
        upper = min(MAX_TIER, val+1)
        lower = max(MIN_TIER, val-1)
        new_val = random.randint(lower, upper)
        new_mon = self.__get_mon__(new_val)
        new_mon.tera_type = self.types[random.randint(0, len(self.types)-1)]
        return new_mon

    def sort_teams(self):
        for player in self.players:
            player.mons = sorted(player.mons, key=lambda mon: mon.val, reverse=True)
        
    def print_results(self):
        for player in self.players:
            sum = 0
            print(player.name + " / " + player.team_name)
            for mon in player.mons:
                sum += mon.val
                # print(str(mon.val) + "   " + mon.name + "   " + mon.tera_type)
                print(f"{str(mon.val):6} {mon.tera_type:<8} {mon.name:<19} ")

            print("")
    
    def write_results_readable(self, path: str):
        output = ""
        for player in self.players:
            output += player.name + " / " + player.team_name + "\n"
            for mon in player.mons:
                output += str(mon.val) + "\t" + mon.name + "\t" + mon.tera_type + "\n"
            output += "\n"
        # output += "_________________________________\n"
        file_path = path  # Replace with your desired file path
        with open(file_path, 'a') as file:
            file.write(output)     
            
    def write_results_formatted(self, path: str):
        output = ""
        for player in self.players:
            output += player.team_name + "\t"
            output += player.name + "\t"
            for mon in player.mons:
                output += mon.name + "\t"            
            for mon in player.mons:
                output += mon.tera_type + "\t"
            output += "\n"
        file_path = path  # Replace with your desired file path
        with open(file_path, 'a') as file:
            file.write(output) 

        
def draft():
    clear_results(READABLE_OUTPUT_PATH)
    clear_results(DOC_OUTPUT_PATH)
    groups = parse_groups(GROUP_SIZE)
    for group in groups:
        new_draft = Draft(group)
        new_draft.draft()
        new_draft.fix_draft()
        new_draft.sort_teams()
        new_draft.assign_teras()
        new_draft.print_results()
        new_draft.write_results_readable(READABLE_OUTPUT_PATH)
        new_draft.write_results_formatted(DOC_OUTPUT_PATH)
        
    
def replace(val: int):        
    if val > MAX_TIER or val < 1:
        exit("INVALID PRICE")
    new_draft = Draft([])
    new_mon = new_draft.replace_mon(val)
    print(str(new_mon.val) + "   " + new_mon.name + "   " + new_mon.tera_type)
    
    
def main(): 
    if len(sys.argv) <= 1:
        sys.exit(USAGE_ERR)
    elif sys.argv[1] == "draft":
        draft()
    elif len(sys.argv) >= 3 and sys.argv[1] == "replace" and sys.argv[2].isnumeric:
        replace(int(sys.argv[2]))
    else:
        sys.exit(USAGE_ERR)
        
if __name__ == "__main__":
    main()