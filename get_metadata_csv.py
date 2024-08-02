# -*- coding: utf-8 -*-
"""
Created on Mon Dec 18 10:47:47 2023

@author: dnelson
"""

from datetime import date
import requests
import csv


def query_revcity(offset):
    url = 'https://therevolutionarycity.org/admin/data-dump'
    if offset != 0:
        url = url + '?page=' + str(offset)
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    return data


def get_data_dump():
    n = 0
    end_cond = 100
    output = []
    while end_cond == 100:
        r = query_revcity(n)
        output = output + r
        end_cond = len(r)
        n = n + 1
    return output


def write_to_csv(data, today):
    header = data[0].keys()
    path = f'U:/htr_revcity/scripts/data/metadata-dump-{today}.csv'
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for i in data:
            writer.writerow(i.values())


def cli():
    data = get_data_dump()
    today = date.today().strftime('%Y-%m-%d')
    write_to_csv(data, today)


if __name__ =='__main__':
    cli()
