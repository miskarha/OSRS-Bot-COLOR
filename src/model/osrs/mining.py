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


class OSRSMiner(OSRSBot):
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
        failed_searches = 0
        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60
        while time.time() - start_time < end_time:
            #pink tile = (3040, 3236, 0), (3041, 3237, 0), (3039, 3237, 0), (3039, 3236, 0)
            #yellow = (3027, 3236, 0), (3028, 3236, 0), (3028, 3235, 0), (3027, 3235, 0))         
            #red = player pos: (3015, 3232, 0)
            #black = player pos: (3001, 3225, 0)
            #white  =player pos: (2982, 3223, 0)
            #deposit box location = (3045, 3235, 0)
            #gray color = 125 125 125
            #print("region data:", api_m.get_player_region_data())
            #print("player pos:", api_m.get_player_position())
            #time.sleep(5)
            if api_s.get_is_inv_empty():
                self.go_bank(api_s,api_m,seeds)
                    
            # 5% chance to take a break between tree searches
#            if rd.random_chance(probability=0.05) and self.take_breaks:
#                self.take_break(max_seconds=30, fancy=True)

 #           if api_s.get_is_inv_full():
 #               self.__drop_ores(api_s)

#            if api_m.get_is_player_idle():
#                if ore := self.get_nearest_tag(clr.PINK):
#                    self.mouse.move_to(ore.random_point(custom_seeds=seeds))
#                    self.mouse.click()
                    #time.sleep(r.uniform(0.05,0.08))
            #self.__move_mouse_to_nearest_ore(seeds, next_nearest=False)
#            time.sleep(0.6)

#            # Click if the mouseover text assures us we're clicking a tree
#            if not self.mouseover_text(contains="Mine", color=clr.OFF_WHITE):
#                continue
#            self.mouse.click()
#            time.sleep(0.5)

            # While the player is chopping (or moving), wait
#            probability = 0.10
#            while not api_m.get_is_player_idle():
#                # Every second there is a chance to move the mouse to the next tree, lessen the chance as time goes on
#                if rd.random_chance(probability):
#                    self.__move_mouse_to_nearest_ore(next_nearest=True)
#                    probability /= 2
#                time.sleep(1)

            #self.update_progress((time.time() - start_time) / end_time)
        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.set_status(BotStatus.STOPPED)

    def __move_mouse_to_nearest_ore(self,seeds, next_nearest=False):
        """
        Locates the nearest tree and moves the mouse to it. This code is used multiple times in this script,
        so it's been abstracted into a function.
        Args:
            next_nearest: If True, will move the mouse to the second nearest tree. If False, will move the mouse to the
                          nearest tree.
            mouseSpeed: The speed at which the mouse will move to the tree. See mouse.py for options.
        Returns:
            True if success, False otherwise.
        """
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

    def __drop_ores(self, api_s: StatusSocket):
        """
        Private function for dropping logs. This code is used in multiple places, so it's been abstracted.
        Since we made the `api` and `logs` variables assigned to `self`, we can access them from this function.
        """
        slots = api_s.get_inv_item_indices(ids.IRON_ORE)
        self.drop(slots)
        self.ores += len(slots)
        self.log_msg(f"ores mined: ~{self.ores}")
        time.sleep(1)
    def __go_ladder(self, api_s: StatusSocket):               
                ladder = self.get_nearest_tag(clr.BLACK)
                self.mouse.move_to(ladder.random_point())
                self.mouse.click()
    def __go_helper(self, api_s: StatusSocket,seeds):
                helper = self.get_nearest_tag(clr.GREEN)
                self.mouse.move_to(helper.random_point(custom_seeds=seeds))
                self.mouse.click()
    def go_bank(self,api_s: StatusSocket,api_m: MorgHTTPSocket, seeds):
            clicked_tiles = []
            while True:                
                if tile := self.get_nearest_tag(clr.Color([255,20,255])) and clicked_tiles.count("PINK") == 0:
                    tile = self.get_nearest_tag(clr.Color([255,20,255]))
                    self.mouse.move_to(tile.random_point(custom_seeds=seeds))
                    self.mouse.click()
                    clicked_tiles.append("PINK")
                    time.sleep(3)
                if tile := self.get_nearest_tag(clr.YELLOW) and clicked_tiles.count("YELLOW") == 0 :
                    tile = self.get_nearest_tag(clr.YELLOW)
                    self.mouse.move_to(tile.random_point(custom_seeds=seeds))
                    self.mouse.click()
                    clicked_tiles.append("YELLOW")
                    time.sleep(3)
                if tile := self.get_nearest_tag(clr.RED) and clicked_tiles.count("RED") == 0:
                    tile = self.get_nearest_tag(clr.RED)
                    self.mouse.move_to(tile.random_point(custom_seeds=seeds))
                    self.mouse.click()
                    clicked_tiles.append("RED")
                    time.sleep(3)   
                if tile := self.get_nearest_tag(clr.Color([100,100,0])) and clicked_tiles.count("KUSI") == 0:
                    if tile := self.get_nearest_tag(clr.WHITE):
                        clicked_tiles.append("WHITE")
                    tile = self.get_nearest_tag(clr.Color([100,100,0]))
                    self.mouse.move_to(tile.random_point(custom_seeds=seeds))
                    self.mouse.click()
                    clicked_tiles.append("KUSI")
                    time.sleep(3)
                if tile := self.get_nearest_tag(clr.WHITE) and clicked_tiles.count("WHITE") == 0:
                    tile = self.get_nearest_tag(clr.WHITE)
                    self.mouse.move_to(tile.random_point(custom_seeds=seeds))
                    self.mouse.click()
                    clicked_tiles.append("WHITE")
                    time.sleep(3)
                if  tile := self.get_nearest_tag(clr.Color([0,255,255])) and clicked_tiles.count("BOX") == 0:
                    while api_m.get_is_player_idle() == False:
                        time.sleep(1)
                    tile = self.get_nearest_tag(clr.Color([0,255,255]))
                    self.mouse.move_to(tile.random_point(custom_seeds=seeds))
                    self.mouse.click()
                    time.sleep(2)
#                    while api_m.get_player_position() != (3045, 3235, 0):
#                        self.mouse.move_to(self.get_nearest_tag(clr.Color([0,255,255])).random_point())
#                        if self.mouseover_text(contains="Deposit", color=clr.OFF_WHITE):                        
#                            self.mouse.click()
#                        time.sleep(2)         
                    time.sleep(0.7)
                    bank = self.get_nearest_tag(clr.Color(lower=[125,125,125]))
                    self.mouse.move_to(bank.random_point(custom_seeds=seeds))
                    self.mouse.click()
                    clicked_tiles.append("BOX")
                    return