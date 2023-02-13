import shutil
import time
from pathlib import Path
import random
import utilities.api.item_ids as item_ids
import utilities.color as clr
import utilities.game_launcher as launcher
from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket
import utilities.random_util as rd
import utilities.ocr as ocr

class OSRSSandcrabs(OSRSBot, launcher.Launchable):
    def __init__(self):
        bot_title = "Combat"
        description = (
            "This bot kills NPCs. Position your character near some NPCs and highlight them. After setting this bot's options, please launch RuneLite with the"
            " button on the right."
        )
        super().__init__(bot_title=bot_title, description=description)
        self.running_time: int = 500
        self.loot_items: str = ""
        self.hp_threshold: int = 5

    def create_options(self):
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 500)
        self.options_builder.add_text_edit_option("loot_items", "Loot items (requires re-launch):", "E.g., Coins, Dragon bones")
        self.options_builder.add_slider_option("hp_threshold", "Low HP threshold (0-100)?", 0, 100)

    def save_options(self, options: dict):
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "loot_items":
                self.loot_items = options[option]
            elif option == "hp_threshold":
                self.hp_threshold = options[option]
            else:
                self.log_msg(f"Unknown option: {option}")
                print("Developer: ensure that the option keys are correct, and that options are being unpacked correctly.")
                self.options_set = False
                return

        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f'Loot items: {self.loot_items or "None"}.')
        self.log_msg(f"Bot will eat when HP is below: {self.hp_threshold}.")
        self.log_msg("Options set successfully. Please launch RuneLite with the button on the right to apply settings.")

        self.options_set = True

    def launch_game(self):
        if launcher.is_program_running("RuneLite"):
            self.log_msg("RuneLite is already running. Please close it and try again.")
            return
        # Make a copy of the default settings and save locally
        src = launcher.runelite_settings_folder.joinpath("osrs_settings.properties")
        dst = Path(__file__).parent.joinpath("custom_settings.properties")
        shutil.copy(str(src), str(dst))
        # Modify the highlight list
        loot_items = self.capitalize_loot_list(self.loot_items, to_list=False)
        with dst.open() as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith("grounditems.highlightedItems="):
                lines[i] = f"grounditems.highlightedItems={loot_items}\n"
        with dst.open("w") as f:
            f.writelines(lines)
        # Launch the game
        launcher.launch_runelite_with_settings(self, dst)

    def main_loop(self):
        self.log_msg("WARNING: This script is for testing and may not be safe for personal use. Please modify it to suit your needs.")
        seeds = rd.random_seeds(0,8,100)
        # Setup API
        api_morg = MorgHTTPSocket()
        api_status = StatusSocket()

        self.toggle_auto_retaliate(True)

        self.log_msg("Selecting inventory...")
        self.mouse.move_to(self.win.cp_tabs[3].random_point(custom_seeds=seeds))
        self.mouse.click()
        failed_searches = 0

        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60
        while time.time() - start_time < end_time:
            run_energy = random.randint(85,100)
            # toggle run if it is not on
            if self.get_run_energy() > run_energy:
                self.toggle_run(True)



            # If inventory is full...
            if api_status.get_is_inv_full():
                self.log_msg("Inventory is full. Idk what to do.")
                self.set_status(BotStatus.STOPPED)
                return

            # While not in combat
            while not api_morg.get_is_in_combat():
                # Find a target
                target = self.get_nearest_tagged_NPC(clr.CYAN)               
                if target is None:
                    failed_searches += 1
                    if failed_searches % 10 == 0:
                        self.log_msg("Searching for targets...")
                    if failed_searches > 60:
                        # If we've been searching for a whole minute...
                        self.__logout("No tagged targets found. Logging out.")
                        return
                    time.sleep(1)
                    continue
                failed_searches = 0

                # Click target if mouse is actually hovering over it, else recalculate
                self.mouse.move_to(target.random_point())
                if not self.mouseover_text(contains="Attack", color=clr.OFF_WHITE):
                    continue
                self.mouse.click()
                time.sleep(1.5)
                if not api_morg.get_is_player_idle():
                    continue
            # While in combat
            while api_morg.get_is_in_combat():
                # Check to eat food
                if self.get_hp() < self.hp_threshold:
                    self.__eat(api_status)
                time.sleep(1)

            # Loot all highlighted items on the ground
#            if self.loot_items:
#                self.__loot(api_status)
#                self.__bury(api_status)
            

            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def __eat(self, api: StatusSocket):
        self.log_msg("HP is low.")
        food_slots = api.get_inv_item_indices(item_ids.all_food)
        if len(food_slots) == 0:
            self.log_msg("No food found. Pls tell me what to do...")
            self.set_status(BotStatus.STOPPED)
            return
        self.log_msg("Eating food...")
        self.mouse.move_to(self.win.inventory_slots[food_slots[0]].random_point())
        self.mouse.click()

    def __bury(self, api: StatusSocket):
        bone_slots = api.get_inv_item_indices(item_ids.BONES)
        num_bones = len(bone_slots)
        if num_bones <1:
            return
#        n= random.randint(10,num_bones)
        if api.get_is_inv_full():
            self.log_msg("Burying bones")
            for i in range(num_bones):
                self.mouse.move_to(self.win.inventory_slots[bone_slots[i]].random_point())
                self.mouse.click()
                time.sleep(0.3)        
#        if num_bones >= n:
#            for i in range(num_bones):
#                self.mouse.move_to(self.win.inventory_slots[bone_slots[i]].random_point())
#                self.mouse.click()
#                time.sleep(0.3)
        self.log_msg("Buried., {} bones".format(num_bones))

    def __loot(self, api: StatusSocket):
        """Picks up loot while there is loot on the ground"""
        while self.pick_up_loot(self.loot_items):
            if api.get_is_inv_full():
                self.__logout("Inventory full. Cannot loot.")
                return
            curr_inv = len(api.get_inv())
            self.log_msg("Picking up loot...")
            for _ in range(5):  # give the bot 5 seconds to pick up the loot
                if len(api.get_inv()) != curr_inv:
                    self.log_msg("Loot picked up.")
                    time.sleep(1)
                    break
                time.sleep(1)

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.set_status(BotStatus.STOPPED)
    
    def attack_random_mob(self,seeds):
        if ocr.find_text("Someone else is fighting that",self.win.chat,ocr.PLAIN_12,clr.BLACK):
            print("attack random mob")
            targets = self.get_all_tagged_in_rect(self.win.game_view, clr.CYAN)
            randindex = random.randint(1,len(targets)-1)
            random_mob = targets[randindex]
            self.mouse.move_to(random_mob.random_point(seeds))
            if  self.mouseover_text(contains="Attack", color=clr.OFF_WHITE):
                self.mouse.click()
                time.sleep(1.5)

    def handle_door(self,seeds):
        if door := self.get_nearest_tag(clr.BLACK) and ocr.find_text("reach that!",self.win.chat,ocr.PLAIN_12,clr.BLACK):
            print("found door")
            door = self.get_nearest_tag(clr.BLACK)
            self.mouse.move_to(door.random_point(seeds))
            if self.mouseover_text(contains="Open", color=clr.OFF_WHITE):
                self.mouse.click()
                tm = random.randint(3,5)
                time.sleep(tm)
    
    
