from src.Config import Config
from notion.collection import *

class TaskManager:
    def updateNotion(self):
        return

    def daily_collection(self):
        return Config.client().get_collection_view(Config.daily_collection_url)

    def add_new_daily(self):
        row = self.daily_collection().collection.add_row()
        today = Config.nowGMT8()
        row.name = today.strftime("%a - %d/%m/%Y")
        row.Date = NotionDate(start=today,end=None,timezone=Config.localTZ)
        return

    def update_recurring_tasks(self):
        # If recurring, check for how many instances
        # If 10 instances, abort task.
        # If <10, create until 10.
        # If selected to be "deleted", remove all instances.

        return

    def start_loop(self):
        self.update_recurring_tasks()
        return

TM = TaskManager()
TM.start_loop()