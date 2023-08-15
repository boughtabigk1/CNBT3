import random

TOTAL_BUDGET = 80
MAX_TIER = 20
GROUP_SIZE = 8
OUTPUT_PATH = 'output/teams.txt'
PLAYER_INPUT = 'params/players.txt'
TIER_INPUT = 'params/tierlist.txt'
TEAM_COMP_INPUT = 'params/brackets1.txt'
# TEAM_COMP_INPUT = 'params/brackets2.txt'


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
        
class Bracket():
    def __init__(self, min: int, max: int, qty: int):
        self.min = min
        self.max = max
        self.qty = qty
    
class Draft():
    def __init__(self, players):
        self.__init_tiers__()
        self.__init_brackets__()
        self.__init_players__(players)
        
    def __init_tiers__(self):
        self.tierlist = [[] for _ in range(MAX_TIER)]
        pricelist = open(TIER_INPUT, 'r')
        prices = pricelist.read().splitlines()
        for price in prices:
            pair = price.split("\t")
            self.tierlist[int(pair[1])-1].append(pair[0])

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
        while actual_value < 1 or actual_value > MAX_TIER or len(self.tierlist[target_value-1+(offset*direction)]) == 0:
            direction *= -1
            offset += 1 if direction > 0 else 0
            actual_value = target_value+(offset*direction)
        len_tier = len(self.tierlist[actual_value-1])
        pick_index = random.randint(0, len_tier-1)
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
        self.players[player_index].replace(mon_index, pick)
        
    def __downgrade1__(self, player_index):
        mon_index = random.randint(0, self.num_mons-1)
        while self.players[player_index].mons[mon_index].val == 1:
            mon_index = (mon_index + 1)%self.num_mons
        pick_value = self.players[player_index].mons[mon_index].val - 1
        pick = self.__get_mon__(pick_value)
        self.players[player_index].replace(mon_index, pick)
        
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
        
    def sort_teams(self):
        for player in self.players:
            player.mons = sorted(player.mons, key=lambda mon: mon.val, reverse=True)
        
    def print_results(self):
        for player in self.players:
            sum = 0
            print("~" + player.name + "~")
            for mon in player.mons:
                sum += mon.val
                print(str(mon.val) + "   " + mon.name)
            print("")
        print("_________________________________")    
    
    def write_results(self, path: str):
        with open(path, 'w') as file:
            file.truncate(0)
        output = ""
        for player in self.players:
            output += "~" + player.name + "~\n"
            for mon in player.mons:
                output += str(mon.val) + "   " + mon.name + '\n'
            output += "\n"
        output += "_________________________________\n"
        file_path = path  # Replace with your desired file path
        with open(file_path, 'a') as file:
            file.write(output) 
        
def main(): 
    groups = parse_groups(GROUP_SIZE)
    for group in groups:
        new_draft = Draft(group)
        new_draft.draft()
        new_draft.fix_draft()
        new_draft.sort_teams()
        new_draft.print_results()
        new_draft.write_results(OUTPUT_PATH)
        
if __name__ == "__main__":
    main()