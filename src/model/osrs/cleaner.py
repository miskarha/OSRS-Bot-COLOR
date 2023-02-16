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
import utilities.imagesearch as imsearch
import utilities.ocr as ocr

import pyautogui as pag

class OSRSHerbCleaner(OSRSBot):
    def __init__(self):
        bot_title = "Cleaner"
        description = "Cleans herbs"
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 500
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
        self.herbs = 0
        bank_color = clr.PINK
        start_time = time.time()
        end_time = self.running_time * 60
        raw_shrimp_img = imsearch.BOT_IMAGES.joinpath("items","Raw_shrimps_bank.png")
        shrimp_img = imsearch.BOT_IMAGES.joinpath("Shrimps.png")

        while (time.time() - start_time < end_time):             

            if api_s.get_is_inv_empty():
                self.withdraw_item(raw_shrimp_img,bank_color,seeds)
            
            if not api_s.get_is_inv_empty():
               self.bank_item(raw_shrimp_img,bank_color,seeds)

            self.update_progress((time.time() - start_time) / end_time)
            
        self.update_progress(1)
        self.__logout("Finished.")
   

    def bank_item(self,item_img,bank_color,seeds):
        bank = self.get_nearest_tag(bank_color)
        self.mouse.move_to(bank.random_point(seeds))
        if self.mouseover_text(contains="Bank", color=clr.OFF_WHITE):
                self.mouse.click()             
        time.sleep(rd.random.uniform(0.5,1))
        if item := imsearch.search_img_in_rect(item_img,self.win.control_panel):
                self.mouse.move_to(item.random_point(seeds))
                time.sleep(0.5)
                if self.mouseover_text(contains="Deposit", color=clr.OFF_WHITE):
                    self.mouse.click()
                    time.sleep(2) 

    def withdraw_item(self,item_img,bank_color,seeds):
        bank = self.get_nearest_tag(bank_color)
        if bank == None:
            if item := imsearch.search_img_in_rect(item_img,self.win.game_view):
                self.mouse.move_to(item.random_point(seeds))
                if self.mouseover_text(contains="Withdraw", color=clr.OFF_WHITE):
                    self.mouse.click()
                    pag.press("escape")
                    time.sleep(2)
                    return            
        self.mouse.move_to(bank.random_point(seeds))
        self.mouse.click()                
        time.sleep(rd.random.uniform(1,1.5))
        if item := imsearch.search_img_in_rect(item_img,self.win.game_view):
            self.mouse.move_to(item.random_point(seeds))
            if self.mouseover_text(contains="Withdraw", color=clr.OFF_WHITE):
                self.mouse.click()
                pag.press("escape")
                time.sleep(1)
                


                