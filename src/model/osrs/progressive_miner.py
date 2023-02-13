import time
import random as r
import utilities.api.item_ids as ids
import utilities.color as clr
import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from model.runelite_bot import BotStatus
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket
from utilities.geometry import RuneLiteObject
import utilities.api.stat_names as stat_names

class OSRSProgressiveMiner(OSRSBot):
    def __init__(self):
        bot_title = "Miner"
        description = "This bot banks iron. Position character in f2p mining guild. Tag ore, ladder and bank."
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 1
        self.take_breaks = False
    
    def create_options(self):
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 200, 500)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])

    def save_options(self, options: dict):
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            else:
                self.log_msg(f"Unknown option: {option}")
                print("Developer: ensure that the option keys are correct, and that options are being unpacked correctly.")
                self.options_set = False
                return
        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{' ' if self.take_breaks else ' not '}take breaks.")
        self.log_msg("Options set successfully.")
        self.options_set = True

    def main_loop(self):
        # Setup API
        api_m = MorgHTTPSocket()
        api_s = StatusSocket()
        
        seeds = rd.random_seeds(0,8,100)
        self.log_msg("Selecting inventory...")
        self.mouse.move_to(self.win.cp_tabs[3].random_point(custom_seeds=seeds))
        self.mouse.click()
        self.ores = 0
        tin_ore = ids.TIN_ORE
        copper_ore = ids.COPPER_ORE
        iron_ore = ids.IRON_ORE
        mining = stat_names.MINING
        copper_tin_color = clr.PINK
        iron_color = clr.BLACK
        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60
        probability = 0.05
        while (time.time() - start_time < end_time) and api_m.get_skill_level(mining) < 15:             
            # 5% chance to take a break between tree searches
            if rd.random_chance(probability):
                self.take_break(max_seconds=30, fancy=True)
                probability /= rd.random.uniform(0.95,2)
                if probability > 0.08: probability = rd.random.uniform(0.01,0.04)

            if api_s.get_is_inv_full():
                self.__drop_ores(api_s,[tin_ore,copper_ore])
            
            if rd.random_chance(probability=0.02): #chance to drop ores early
                self.__drop_ores(api_s,[tin_ore,copper_ore])

            self.mine_ore(api_m,seeds,copper_tin_color) # find, move mouse and click ore to mine

            #probability,moved = self.move_to_next_ore(api_m,probability) # chance to move mouse to the next nearest ore

            self.update_progress((time.time() - start_time) / end_time)

        while (time.time() - start_time < end_time) and api_m.get_skill_level(mining) > 14:             
            # 5% chance to take a break between tree searches
#            if rd.random_chance(probability=0.05) and self.take_breaks:
#                self.take_break(max_seconds=30, fancy=True)

            if api_s.get_is_inv_full():
                if api_m.get_skill_level(mining) <15:
                    self.__drop_ores(api_s,[tin_ore,copper_ore])
                else:
                    self.__drop_ores(api_s,[iron_ore])
            
            if rd.random_chance(probability=0.02): #chance to drop ores early
                if api_m.get_skill_level(mining) <15:
                    self.__drop_ores(api_s,[tin_ore,copper_ore])
                elif api_m.get_skill_level(mining) >14:
                    self.__drop_ores(api_s,[iron_ore])

            if api_m.get_skill_level(mining) <15: #mine copper and tin if level below 15
                    self.mine_ore(api_m,seeds,copper_tin_color)
            if api_m.get_skill_level(mining) >14: #if over 14 mine iron
                    self.mine_ore(api_m,seeds,iron_color)

            
            self.mine_ore(api_m,seeds)# find, move mouse and click ore
            #probability,moved = self.move_to_next_ore(api_m,probability) # chance to move mouse to the next nearest ore

            self.update_progress((time.time() - start_time) / end_time)        

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.set_status(BotStatus.STOPPED)

    def __move_mouse_to_nearest_ore(self,seeds, next_nearest=False):

        ores = self.get_all_tagged_in_rect(self.win.game_view, clr.PINK)
        ore = None
        if not ores:
            return False
        # If we are looking for the next nearest tree, we need to make sure trees has at least 2 elements
        if next_nearest and len(ores) < 2:
            return False
        ores = sorted(ores, key=RuneLiteObject.distance_from_rect_center)
        ore = ores[1] if next_nearest else ores[0]
        if next_nearest:
            self.mouse.move_to(ore.random_point(custom_seeds=seeds), mouseSpeed="slow", knotsCount=2)
        else:
            self.mouse.move_to(ore.random_point(custom_seeds=seeds))
        return True

    def __drop_ores(self, api_s: StatusSocket, ores: list):
        """
        Private function for dropping logs. This code is used in multiple places, so it's been abstracted.
        Since we made the `api` and `logs` variables assigned to `self`, we can access them from this function.
        """
        num_type_ores = len(ores)
        slots = []
        for ore in range(num_type_ores):
            slots_ore = api_s.get_inv_item_indices(ores[ore])
            slots = slots + slots_ore
        
        slots = slots.sort()
        self.drop(slots)
        self.ores += len(slots)
        self.log_msg(f"ores mined: ~{self.ores}")
        time.sleep(1)
    
    def mine_ore(self,api_m: MorgHTTPSocket,seeds,ore_color):
            if api_m.get_is_player_idle():
                if ore := self.get_nearest_tag(ore_color):
                    self.mouse.move_to(ore.random_point(custom_seeds=seeds))
                    if self.mouseover_text(contains="Mine", color=clr.OFF_WHITE):
                        self.mouse.click()
                    time.sleep(r.uniform(0.1,0.2))

    
    def move_to_next_ore(self,api_m,probability):
            while not api_m.get_is_player_idle():
                # Every second there is a chance to move the mouse to the next tree, lessen the chance as time goes on
                if rd.random_chance(probability):
                    self.__move_mouse_to_nearest_ore(next_nearest=True)
                    probability /= rd.random.randrange(0, 2)
                    if probability > 1: probability = rd.random.uniform(0.05, 0.2)                   
                time.sleep(1)
            return probability


