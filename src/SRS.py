from notion.collection import NotionDate
import math
from datetime import datetime
import time
import copy
import numpy as np
from src.Config import Config
import sys

class SRS:
    def __init__(self, config=Config()):
        self.desired_success_rate = 0.75
        self.default_ease_rate = 2.50
        self.easecap = 0.20
        self.learning_steps = [15,1440]
        self.grade_allocations = [0.01, 0.25, 0.50, 0.75, 0.99] #"No idea", "Unsure", "Half Right", "Almost Perfect", "Nailed It"
        self.config = config
        self.client = self.config.client()
        self.collection = self.client.get_collection_view(self.config.topics_collection_url())

    def get_block(self, id):
        return self.client.get_block(id)

    def row_callback(self, record, changes):
        start = record.update
        record.update = False
        if start:
            print("Updating \n", record.topics)
            self.main(record)
            print("Done!\n")
        reset = record.reset
        creset = record.confirm_reset
        record.reset = False
        record.confirm_reset = False
        if reset:
            time.sleep(2)
            if creset:
                self.reset_loop(record)
        time.sleep(3)

    def add_row_callback(self, row):
        return row.add_callback(self.row_callback, callback_id="row_callback")

    def register_row_callbacks(self, collection):
        print("Registering Row Callbacks...\n")
        rows = collection.collection.get_rows()
        for row in rows:
            self.add_row_callback(row)
        return

    def collection_callback(self, record, difference, changes):
        self.register_row_callbacks(record)

    def fetch_topic(self, record):
        return self.get_block(record.id)

    def get_ease(self, qs):
        print("Getting ease list...")
        ease_list=[]
        for q in qs:
            if q.ease is None:
                ease = self.default_ease_rate
            else:
                ease = q.ease
            ease_list.append(ease)
        return ease_list

    def get_grade(self, qs):
        print("Getting grade list...")
        grade_list = []
        for q in qs:
            if q.Rank is None:
                grade = self.grade_allocations[0]
            elif q.Rank == "No idea":
                grade = self.grade_allocations[0]
            elif q.Rank == "Unsure":
                grade = self.grade_allocations[1]
            elif q.Rank == "Half Right":
                grade = self.grade_allocations[2]
            elif q.Rank == "Almost Perfect":
                grade = self.grade_allocations[3]
            elif q.Rank == "Nailed It":
                grade = self.grade_allocations[4]
            grade_list.append(grade)
        return grade_list

    def get_rtime(self, top, qs):
        print("Getting revised time list...")
        rtime_list = []
        for q in qs:
            timeNow = self.config.nowGMT8()
            time = NotionDate(start=timeNow,end=None,timezone=self.config.localTZ())
            rtime_list.append(time)
        return rtime_list

    def get_interval(self, qs):
        print("Getting interval list...")
        interval_list=[]
        for q in qs:
            pint = q.p_interval
            interval_list.append(pint)
        return interval_list

    def create_matrix(self, e,g,r,i):
        print("Creating EGRI matrix...")
        egri_matrix = np.column_stack((e,g,r,i))
        return egri_matrix

    def calculate_ease(self, m):
        print("Calculating qns ease...")
        for q in m:
            e = q[0]
            g = q[1]
            print(e)
            print(g)
            print(self.desired_success_rate)
            sys.stdout.flush()
            ne = e * math.log(self.desired_success_rate) / math.log(g)
            q[0] = ne
        return m

    def calculate_interval(self, m):
        print("Calculating qns intervals...")
        for q in m:
            e = q[0]
            g = q[1]
            r = q[2]
            i = q[3]
            if i is None:
                ni = self.learning_steps[0]
            elif i < self.learning_steps[-1]:          # If interval is within Learning Range
                if g >= self.grade_allocations[2]:     # If grade is equal or above 50%, go to next step.
                    mini = min(self.learning_steps, key=lambda x:abs(x-i))
                    n = self.learning_steps.index(mini)
                    ni = self.learning_steps[n+1]
                else:                             # If grade is below 50%, restart at first step.
                    ni = self.learning_steps[0]
            else:
                ni = i * e
            q[3] = ni
        return m

    def update_qns_values(self, qs, m):
        print("Updating qns values...")
        n = 0
        for q in m:
            e = q[0]
            g = q[1]
            r = q[2]
            i = q[3]
            question = qs[n]
            question.ease = e
            if g == 0.01:
                question.Rank = "No idea"
            question.qnsRevised = r
            question.p_interval = i
            n = n + 1
        return

    def update_topic_date(self, topic):
        print("Updating topic date...")
        timeNow = self.config.nowGMT8()
        topic.Revised = NotionDate(start=timeNow,end=None,timezone=self.config.localTZ())
        return

    def update_topic_count(self, topic):
        print("Updating topic count...")
        counts = topic.counts
        topic.counts = counts + 1
        return

    def main(self, record):
        topic = self.fetch_topic(record)
        print("Copying questions...")
        questions_copy = copy.copy(topic.questions)
        ease_list = self.get_ease(questions_copy)
        grade_list = self.get_grade(questions_copy)
        rtime_list = self.get_rtime(topic, questions_copy)
        interval_list = self.get_interval(questions_copy)
        egri_matrix = self.create_matrix(ease_list, grade_list, rtime_list, interval_list)
        calc_e_matrix = self.calculate_ease(egri_matrix)
        calc_ei_matrix = self.calculate_interval(calc_e_matrix)
        self.update_qns_values(topic.questions, calc_ei_matrix)
        self.update_topic_date(topic)
        self.update_topic_count(topic)
        #update_topic_values()
        return

    def start_loop(self):
        while True:
            start_time = time.time()
            self.collection.add_callback(self.collection_callback)
            self.register_row_callbacks(self.collection)
            print("\nMonitoring now...\n")
            timelimit = 3600
            n = True
            while n:
                self.client.start_monitoring()
                time.sleep(0.01)
                elapsed = time.time() - start_time
                if elapsed == timelimit:
                    n = False

    def reset_loop(self, record):
        # clean up questions
        # backup statistics
        topic = self.fetch_topic(record)
        qs = copy.copy(topic.questions)
        print("Resetting questions...")
        for q in qs:
            q.Rank = "No idea"
            q.qnsRevised = None
            q.ease = None
            q.p_interval = None
        print("Updating topics...")
        topic.revised = None
        topic.counts = None
        print("Topic reset.")
        return


p = SRS()
p.start_loop()
