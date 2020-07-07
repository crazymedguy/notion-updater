from src.Config import Config
from notion.collection import *
from datetime import date
import uuid

class TaskManager:
    def __init__(self, config=Config()):
        self.config = config

    def updateNotion(self):
        return

    def daily_collection(self):
        return self.config.client().get_collection_view(self.config.daily_collection_url())

    def guild_collection(self):
        return self.config.client().get_collection_view(self.config.guild_collection_url())

    def check_existing_daily(self):
        print("Checking for existing daily tasks...")
        need_add = True
        today = self.config.todayGMT8()
        for row in self.daily_collection().collection.get_rows():
            if row.Events == today.strftime("%a - %d/%m/%Y"):
                need_add = False
        if need_add:
            print("Adding daily for {}".format(today))
            self.add_new_daily()
        else:
            print("Daily already existing for {}".format(today))
        return

    def add_new_daily(self):
        row = self.daily_collection().collection.add_row()
        today = self.config.todayGMT8()
        row.Events = today.strftime("%a - %d/%m/%Y")
        row.Date = NotionDate(start=today,end=None,timezone=Config.localTZ)
        print("Today's daily added.")
        return

    def check_daily_pomodoros(self):
        print("Checking for daily pomodoros...")
        today = self.config.todayGMT8()
        need_update = True
        for parent in self.guild_collection().collection.get_rows():
            if parent.Status == "Working On It":
                if parent.Frequency is not None:
                    for child in parent.children:
                        if child.Name == "{} Pomodoro for {}".format(today, parent.Name):
                            need_update = False
                    if need_update:
                        print("No daily pomodoro for {}, now adding...".format(parent.Name))
                        self.update_daily_pomodoros(parent)
                    else:
                        print("Daily pomodoro already existing for {}".format(parent.Name))
        return

    def update_daily_pomodoros(self, parent):
        today = self.config.todayGMT8()
        new_pomodoro = self.guild_collection().collection.add_row()
        new_pomodoro.Name = "{} Pomodoro for {}".format(today, parent.Name)
        new_pomodoro.Parents = parent.id
        new_pomodoro.Types = "d28dedbe654c47f1b7084432a935cc21"
        new_pomodoro.Status = "Working On It"
        new_pomodoro.Do_By_Date = NotionDate(start=today, end=None, timezone=Config.localTZ)
        new_pomodoro.Deadline = NotionDate(start=today, end=None, timezone=Config.localTZ)
        print("Pomodoro added for {}".format(parent.Name))
        return


    def update_recurring_tasks(self):
        print("Updating recurring tasks...")
        # If recurring, check for how many instances
        # If 10 instances, abort task.
        # If <10, create until 10.
        # If selected to be "deleted", remove all instances.

        return

    def start_loop(self):
        self.check_existing_daily()
        self.check_daily_pomodoros()
        self.update_recurring_tasks()
        return

TM = TaskManager()
TM.start_loop()