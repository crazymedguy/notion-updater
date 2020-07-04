from src.Config import Config
from notion.collection import *
from datetime import date

class TaskManager:
    def __init__(self, config=Config()):
        self.config = config

    def updateNotion(self):
        return

    def daily_collection(self):
        return self.config.client().get_collection_view(self.config.daily_collection_url())

    def check_existing_daily(self):
        print("Checking for existing daily tasks...")
        status = True
        today = self.config.todayGMT8()
        for row in self.daily_collection().collection.get_rows():
            if row.Date != today:
                status = False
        return status

    def add_new_daily(self):
        row = self.daily_collection().collection.add_row()
        today = self.config.todayGMT8()
        row.Events = today.strftime("%a - %d/%m/%Y")
        row.Date = NotionDate(start=today,end=None,timezone=Config.localTZ)
        print("Today's daily added.")
        return

    def update_recurring_tasks(self):
        print("Updating recurring tasks...")
        # If recurring, check for how many instances
        # If 10 instances, abort task.
        # If <10, create until 10.
        # If selected to be "deleted", remove all instances.

        return

    def start_loop(self):
        if not self.check_existing_daily():
            print("No existing daily found, adding...")
            self.add_new_daily()
        else:
            print("Existing daily found.")
        self.update_recurring_tasks()
        return

TM = TaskManager()
TM.start_loop()