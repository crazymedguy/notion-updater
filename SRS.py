from cachetools import cached
from notion.client import NotionClient
from notion.block import *
from notion.collection import NotionDate
import math
from datetime import datetime
import copy
import numpy as np
import os
from os import environ 

########## VALUES #############
desired_success_rate = 0.75
default_ease_rate = 2.50
easecap = 0.20
learning_steps = [15,1440]
# "No idea", "Unsure", "Half Right", "Almost Perfect", "Nailed It"
grade_allocations = [0.01, 0.25, 0.50, 0.75, 0.99]
###############################

token_v2 = environ['NOTION_TOKEN']
collection_url = environ['COLLECTION_URL']

client = NotionClient(
    token_v2=token_v2,
    monitor=True,
    start_monitoring=True)

collection = client.get_collection_view(collection_url)

def get_block(id):
    return client.get_block(id)

def row_callback(record, changes):
    start = record.update
    record.update = False
    if start:
        print("Updating \n", record.topics)
        main(record)
        print("Done!\n")
    time.sleep(3)

def add_row_callback(row):
    return row.add_callback(row_callback, callback_id="row_callback")

def register_row_callbacks(collection):
    print("Registering Row Callbacks...\n")
    rows = collection.collection.get_rows()
    for row in rows:
        add_row_callback(row)
    return

def collection_callback(record, difference, changes):
    register_row_callbacks(record)

def fetch_topic(record):
    return get_block(record.id)

def get_ease(qs):
    print("Getting ease list...")
    ease_list=[]
    for q in qs:
        if q.ease is None:
            ease = default_ease_rate
        else:
            ease = q.ease
        ease_list.append(ease)
    return ease_list

def get_grade(qs):
    print("Getting grade list...")
    grade_list = []
    for q in qs:
        if q.Rank is None:
            grade = grade_allocations[0]
        elif q.Rank == "No idea":
            grade = grade_allocations[0]
        elif q.Rank == "Unsure":
            grade = grade_allocations[1]
        elif q.Rank == "Half Right":
            grade = grade_allocations[2]
        elif q.Rank == "Almost Perfect":
            grade = grade_allocations[3]
        elif q.Rank == "Nailed It":
            grade = grade_allocations[4]
        grade_list.append(grade)
    return grade_list

def get_rtime(top, qs):
    print("Getting revised time list...")
    rtime_list = []
    for q in qs:
        time = NotionDate(start=datetime.now())
        rtime_list.append(time)
    return rtime_list

def get_interval(qs):
    print("Getting interval list...")
    interval_list=[]
    for q in qs:
        pint = q.p_interval
        if pint is None:
            pint = learning_steps[0]
        interval_list.append(pint)
    return interval_list

def create_matrix(e,g,r,i):
    print("Creating EGRI matrix...")
    egri_matrix = np.column_stack((e,g,r,i))
    return egri_matrix

def calculate_ease(m):
    print("Calculating qns ease...")
    for q in m:
        e = q[0]
        g = q[1]
        ne = e * math.log(desired_success_rate) / math.log(g)
        q[0] = ne
    return m

def calculate_interval(m):
    print("Calculating qns intervals...")
    for q in m:
        e = q[0]
        g = q[1]
        r = q[2]
        i = q[3]
        if i < learning_steps[-1]:
            mini = min(learning_steps, key=lambda x:abs(x-i))
            n = learning_steps.index(mini)
            ni = learning_steps[n+1]
        else:
            ni = i * e
        q[3] = ni
    return m

def update_qns_values(qs, m):
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

def update_topic_date(topic):
    print("Updating topic date...")
    topic.Revised = NotionDate(start=datetime.now())
    return

def update_topic_count(topic):
    print("Updating topic count...")
    counts = topic.counts
    topic.counts = counts + 1
    return

"""def update_topic_values():
    return"""

def main(record):
    topic = fetch_topic(record)
    print("Copying questions...")
    questions_copy = copy.copy(topic.questions)
    ease_list = get_ease(questions_copy)
    grade_list = get_grade(questions_copy)
    rtime_list = get_rtime(topic, questions_copy)
    interval_list = get_interval(questions_copy)
    egri_matrix = create_matrix(ease_list, grade_list, rtime_list, interval_list)
    calc_e_matrix = calculate_ease(egri_matrix)
    calc_ei_matrix = calculate_interval(calc_e_matrix)
    update_qns_values(topic.questions, calc_ei_matrix)
    update_topic_date(topic)
    update_topic_count(topic)
    #update_topic_values()
    return


collection.add_callback(collection_callback)
register_row_callbacks(collection)
print("\nMonitoring now...\n")
client.start_monitoring()
input()