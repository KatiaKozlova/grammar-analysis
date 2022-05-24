#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# !pip install pdfplumber
# !pip install gdown


# In[135]:


import pdfplumber
import enchant
import re 
import csv
import os
import json
import string
import shutil 
import requests
import gdown
import pandas as pd
from zipfile import ZipFile
from flask import Flask, send_file
from flask import render_template, request, redirect, url_for
from werkzeug.utils import secure_filename


# In[136]:


d_en = enchant.Dict('en')


# In[137]:


def extract_tables(pg, nmng, pth, p_num):  # function for table extraction
    table_settings = {  # settings for explicit borders 
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
    }
    flag = 0
    table = pg.extract_table(table_settings)  # extraction of the biggest table on a page 
    if table:
        flag = 0
        my_df = pd.DataFrame(table[1:], columns=table[0])  # extracted table to DataFrame
        with open(pth + '/' + str(p_num + 1) + '_' + nmng[0][2].replace(':', '.') + '._' + nmng[0][3].replace('/', '').replace('*', '').replace('<', '').replace(':', '.').strip() + '.csv', 'w+', encoding='utf-8') as csv_table:
            my_df.to_csv(csv_table, index=False)  # saving DataFrame in CSV
        if len(re.findall(r',-[^-,]|[^-,]-,|[^-,]-\s|\s-[^-,]|,=|=,|[^\s]=\s|\s=[^\s]',  my_df.to_csv(index=False))) < 3:  # cheking for morphemes in a cell
            os.remove(pth + '/' + str(p_num + 1) + '_' + nmng[0][2].replace(':', '.') + '._' + nmng[0][3].replace('/', '').replace('*', '').replace('<', '').replace(':', '.').strip() + '.csv')  # delete if no morphemes
        else:
            flag = 1
        if flag == 1:  # if morphological table is found
            tab = pg.debug_tablefinder(table_settings)
            for req_table in tab.tables:
                if req_table.extract()[0] == table[0]:
                    cropped = pg.within_bbox(req_table.bbox)  # crop page
                    img = cropped.to_image(resolution=200)
                    # save cropped page as image
                    img.save(pth + '/' + str(p_num + 1) + '_' + nmng[0][2].replace(':', '.') + '._' + nmng[0][3].replace('/', '').replace('*', '').replace('<', '').replace(':', '.').strip() + '.jpeg')
                    break


# In[161]:


def extract_examples_tables(name): 
    path = name.split('.')[0]
    if not os.path.exists(path):  # folder creation
        os.mkdir(path)
    with pdfplumber.open(name) as pdf:
        examples_dic = {}
        for p in range(len(pdf.pages)):
            page = pdf.pages[p]
            text = page.extract_text()  # text extraction
            # IMG-finder
            examples = re.findall(r"\n((\s*?((\(?(\d+([\.\-:]\d+){0,2}|\d*[a-z])\)|\d+:|\[\d+\]|\d+([a-z]|\-\d+)?\.)(\s+?[a-z]\.|\s+?\([a-z]\))?)|(\s*?[a-z]\.))((.*?)\n){2,5}\s*?((‘.*’)|(“.*”)|(„.*‟)|('.*')|(\".*\")|(`.*')|(«.*»)))", text)
            # find all the tables' names
            naming = re.findall(r'(^|\n)\s*(Table|TABLE|Tableau|TABLEAU|Cuadro|CUADRO)\s+(\d+)(.*?)\n', text)
            nmbr = len(naming)
            if nmbr != 0:  # there is a table name on a page
                extract_tables(page, naming, path, p)  # table extraction (see above)
            for example in examples:  # for each example
                number = None
                if example:
                    letter = ''
                    t = example[0].strip()
                    t = re.sub('\t', ' ', t)
                    clear = t.split('\n')
                    for i in range(len(clear)):
                        line = clear[i]
                        if '-' not in line and '=' not in line and '–' not in line:  # omittimg first lines without glossing
                            continue
                        else:
                            break
                    t = '\n'.join(clear[i:])
                    # trying to find example's number
                    if t.startswith('('):  # '(12)'-like
                        number = t.split(')')[0].strip('(')
                        txt = re.sub(r'\(?(\d+([\.\-:]\d+){0,2}|\d*[a-z])\)|\d+:|\[\d+\]|\d+([a-z]|\-\d+)?\.', '', t).strip()
                         # trying to find example's sub-number
                        if '.' in txt.split('\n')[0].strip().strip('.'):  # '(12) a.'-like
                            letter = txt.split('\n')[0].strip().strip('.').split('.')[0]
                            letter = letter.strip()
                        elif ')' in txt.split('\n')[0].strip().split('(')[0]: # '(12) (a)'-like
                            letter = txt.split('\n')[0].strip().split('(')[0].split(')')[0]
                            letter = letter.strip()
                    elif t.startswith('['):  # '[12]'-like
                        number = t.split(']')[0].strip('[')
                    elif ')' in t.split('\n')[0].strip().split('(')[0]:  #'12)'-like
                        temp = t.split('\n')[0].strip().split('(')[0].split(')')[0].strip()
                        if temp[0] in '1234567890':
                            number = re.sub(r'[a-z]', '', temp)
                            if re.findall(r'[a-z]', temp) != 0:
                                letter = re.sub(r'\d', '', temp)
                        else: #'a)'-like
                            letter = temp
                    elif t.split('\n')[0].strip().split(':')[0].strip().isdigit(): #'12:'-like
                        number = t.split('\n')[0].strip().split(':')[0].strip()
                    elif t.strip()[1] == '.': #'b.'-like
                        letter = t.split('\n')[0].strip().strip('.').split('.')[0]
                        letter = letter.strip()
                    elif t.split('\n')[0].strip().split('.')[0].strip()[0].isdigit(): #'12.'-like
                        number = t.split('\n')[0].strip().split('.')[0].strip()
                    if number and (str(number) + '_' + str(p + 1)) not in examples_dic:
                        examples_dic[str(number) + '_' + str(p + 1)] = []
                    # cleaning from number-letters
                    txt = re.sub(r'((\(?(\d+([\.\-:]\d+){0,2}|\d*[a-z])\)|\d+:|\[\d+\]|\d+([a-z]|\-\d+)?\.)(\s+?[a-z]\.|\s+?\([a-z]\))?)|(\s*?[a-z]\.)', '', t)
                    clear = txt.split('\n')
                    for i in range(len(clear)):
                        line = clear[i]
                        if '-' not in line and '=' not in line and '–' not in line and '+' not in line:
                            continue
                        else:
                            break
                    txt = '\n'.join(clear[i:])
                    txt = txt.strip().split('\n')
                    if len(txt) == 5:  # two first rows are four
                        txt[0] = re.sub(r'^[a-z]\.', '', txt[0].strip())
                        txt[0] = re.sub(r'^[a-z]\)', '', txt[0].strip())
                        original = ''
                        gloss = ''
                        trans = txt[-1].strip()
                        for i in txt[:-1:2]:
                            original += i.strip() + ' '
                        for i in txt[1:-1:2]:
                            gloss += i.strip() + ' '
                    elif len(txt) == 4:  # first row to omit
                        txt[1] = re.sub(r'^[a-z]\.', '', txt[1].strip())
                        txt[1] = re.sub(r'^[a-z]\)', '', txt[1].strip())
                        original = txt[1].strip()
                        gloss = txt[2].strip()
                        trans = txt[-1].strip()
                    elif len(txt) == 3:  # three rows, everything OK
                        txt[0] = re.sub(r'^[a-z]\.', '', txt[0].strip())
                        txt[0] = re.sub(r'^[a-z]\)', '', txt[0].strip())
                        original = txt[0].strip()
                        gloss = txt[1].strip()
                        trans = txt[-1].strip()
                    # write to dictionary
                    if letter and number and {letter: [original, gloss, trans]} not in examples_dic[str(number) + '_' + str(p + 1)]:
                        examples_dic[str(number) + '_' + str(p + 1)].append({letter: [original, gloss, trans]})
                    elif number and original and gloss and trans and [original, gloss, trans] not in examples_dic[str(number) + '_' + str(p + 1)]:
                        examples_dic[str(number) + '_' + str(p + 1)].append([original, gloss, trans])
    with open(path + '/' + name.split('.')[0] + '.json', 'w', encoding='utf-8') as fp:  # dictionary to JSON
        json.dump(examples_dic, fp, ensure_ascii=False)


# In[139]:


def prettify(text):  # function to clear lines from punctuation
    w = text.strip('. ?!')
    w = re.sub('\\t', ' ', w)
    w = re.sub('\t', ' ', w)
    w = re.sub(r'–', '-', w)
    w = re.sub(r'--', '-', w)
    w = re.sub(r'\s+-', '-', w)
    w = re.sub(r'\s+=', '=', w)
    w = re.sub(r'=\s+', '=', w)
    w = re.sub(r'-\s+', '-', w)
    w = re.sub(r'--', '-', w)
    w = re.sub(r'\(.\)', '', w)
    w_new = re.sub(r'\[|\]', '', w)
    w_new = re.sub(r'\s{2,}', ' ', w_new)
    w_new = w_new.split()
    return w, w_new


# In[140]:


def glossing(name):  # cutting into morphemes
    l = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ.n/123():\\sgplmfn>'  # allowed signs  for a gloss
    list_of_glosses = {}
    path = name.split('.')[0]
    with open(path + '/' + name.split('.')[0] + '.json', encoding='utf-8') as file:  # examples' loading
        dic = json.load(file)
    for it in dic:
        items = dic[it]
        for item in items:
            if type(item) != list:
                item = list(item.values())[0]
            words, words_new = prettify(item[0])
            glossed_words, glossed_words_new = prettify(item[1])
            if len(words_new) != len(glossed_words_new):  # not equal number of words
                # try to delete everything inside square brackets 
                words = re.sub(r'\[.*?\]', '', words)  
                words = re.sub(r'\s{2,}', ' ', words)
                words = words.split()
                glossed_words = re.sub(r'\[.*?\]', '', glossed_words)
                glossed_words = re.sub(r'\s{2,}', ' ', glossed_words)
                glossed_words = glossed_words.split()
            else:
                glossed_words = glossed_words_new
                words = words_new
            if len(words) == len(glossed_words):  # equal number of words
                for index in range(len(words)):
                    # split by dividers
                    word = re.split(r'-|=|~', words[index].strip())  
                    glossed_word = re.split(r'-|=|~', glossed_words[index].strip())
                    if len(word) == len(glossed_word):  # equal number of parts
                        for i in range(len(glossed_word)):
                            gloss = glossed_word[i]
                            flag = 0
                            for letter in gloss:
                                if letter not in l:
                                    flag = 1
                            if flag == 0:  # check if all the signs are allowed
                                # clear from punctuation
                                if ')' in gloss and '(' not in gloss:
                                    gloss = gloss.strip(')')
                                affix = word[i].lower().strip('#[]*)(….?”!/,!1234567890<>|/')
                                affix = affix.split('(')[0]
                                affix = affix.split('/')[0]
                                affix = affix.strip('#[]*)(….?”!/,!1234567890<>|/')
                                gloss = re.sub(r'\(|\)', '', gloss).upper().strip('.')
                                # write to dictionary
                                if gloss and gloss not in list_of_glosses and affix:  
                                    list_of_glosses[gloss] = [{affix: [it]}]
                                elif gloss and affix:
                                    flag = 0
                                    for affixes in list_of_glosses[gloss]:
                                        if affix in affixes.keys():
                                            flag = 1
                                    if flag == 0:
                                        list_of_glosses[gloss].append({affix: [it]})
                                    else:
                                        for affixes in list_of_glosses[gloss]: 
                                            if affix in affixes.keys() and it not in affixes[affix]:
                                                affixes[affix].append(it)
    with open(path + '/' + name.split('.')[0] + '_glosses.json', 'w', encoding='utf-8') as f:  # dictionary to JSON
        json.dump(list_of_glosses, f, ensure_ascii=False)


# In[141]:


def web_glosses():  # function to upload glosses with keywords from Wiki
    html = requests.get('https://en.wiktionary.org/wiki/Appendix:List_of_glossing_abbreviations')
    content =  html.text
    # searchin in HTML
    glosses = re.findall('<td><small>(.+?)<\/small><\/td>\n<td>(((.*?)<a.*>(.+?)<\/a>(.*))|(.*?))\n', content)
    web_dic_glosses = {}
    for item in glosses:
        name = ''
        if item[4] != '':
            if item[5] != '':
                name = re.findall('<small>(.*?)</small>', item[5])
            if not item[4].startswith('('):
                text = item[4].split('(')[0].strip().strip(string.punctuation)
            else:
                text = item[4].split(')')[1].strip()
        elif item[1] != '':
            text = item[1].split('(')[0].strip().strip(string.punctuation)
        n = item[0].split(',')
        if len(n) > 1:
            for i in n:
                i = i.strip()
                if '(' in i and i not in web_dic_glosses:
                    web_dic_glosses[i.split('(')[0]] = text
                    name = i.replace('(', '')
                    name = name.replace(')', '')
                if i not in web_dic_glosses:
                    web_dic_glosses[i] = text
        elif text and '(' in item[0] and item[0] not in web_dic_glosses:
            web_dic_glosses[item[0].split('(')[0]] = text
            name = item[0].replace('(', '')
            name = name.replace(')', '')
        elif text and item[0] not in web_dic_glosses:
            web_dic_glosses[item[0]] = text
        if text and name and name[0] not in web_dic_glosses:
            web_dic_glosses[name[0]] = text
    # deleting excessive ones (may be added as well)
    del web_dic_glosses['V']
    del web_dic_glosses['SG']
    del web_dic_glosses['PL']
    del web_dic_glosses['DU']
    del web_dic_glosses['IN']
    del web_dic_glosses['AGR']
    del web_dic_glosses['FORM']
    del web_dic_glosses['A']
    del web_dic_glosses['HIST']
    del web_dic_glosses['B']
    del web_dic_glosses['AND']
    del web_dic_glosses['PP']
    del web_dic_glosses['PPFV']
    return web_dic_glosses


# In[165]:


def table_glossing(name):  # searching morphemes in tables
    dic_glosses = web_glosses()
    path = name.split('.')[0]
    list_of_items = os.listdir(path)  # every file in folder
    with open(path + '/' + name.split('.')[0] + '_glosses.json', encoding='utf-8') as file:  # dictionary with examples' glosses
        dic = json.load(file)
    dic_of_glosses = {}
    for gloss in dic:
        for it in dic[gloss]:
            if list(it.keys())[0] not in dic_of_glosses:
                dic_of_glosses[list(it.keys())[0]] = [gloss]
            elif gloss not in dic_of_glosses[list(it.keys())[0]]:
                dic_of_glosses[list(it.keys())[0]].append(gloss)
    keyss = list(web_glosses().keys())  # list of glosses from Wiki
    valuess = [w.split(' ')[0] for w in web_glosses().values()] # list of keywords for glosses from Wiki
    for item in list_of_items:
        if item.endswith('.csv') and item[0].isdigit():  # each .csv file
            num = item.split('._')[0]  # number + page
            with open(path + '/' + item) as csv_file:
                tablereader = csv.reader(csv_file)
                try:
                    names = list(tablereader)[0]  # first row (columns' names)
                    for i in range(len(names)):
                        if re.findall(r'\w+[\-–]\s?\n\w+', names[i]):  # check if line wrapping
                            new_word = re.sub(r'[\-–]\s?\n', '', re.findall(r'\w+[\-–]\s?\n\w+', names[i])[0])
                            if d_en.check(new_word):  # if word exists in English
                                names[i] = re.sub(r'[\-–]\s?\n', '', names[i])  # line wrapping
                except UnicodeDecodeError:
                    continue
            with open(path + '/' + item) as csv_file:
                tablereader = csv.reader(csv_file)
                for row in list(tablereader):
                    for i in range(len(row)):
                        words = row[i].strip()
                        if re.findall(r'\w+[\-–]\s?\n\w+', words):  # check if line wrapping
                            new_word = re.sub(r'[\-–]\s?\n', '', re.findall(r'\w+[\-–]\s?\n\w+', words)[0])
                            if d_en.check(new_word):  # if word exists in English
                                row[i] = re.sub(r'[\-–]\s?\n', '', words)  # line wrapping
                        words = re.split(r'\s|\/', row[i])
                        for word in range(len(words)):
                            w = words[word]
                            # cleaning from punctuation
                            w = w.strip(',:;')
                            w = w.replace('(', '')
                            w = w.replace(')', '').strip()
                            # check if dividers in the end/beginning
                            if w.startswith('-') or w.startswith('–') or w.startswith('=') or w.endswith('-') or w.endswith('–') or w.endswith('='):
                                w = w.strip(string.punctuation)
                                w = w.strip('–')
                                if '-' not in w and '–' not in w and '=' not in w and w.islower():  # not a fully glossed example 
                                    f = 0
                                    if w in dic_of_glosses.keys() and len(dic_of_glosses[w]) != 1:  # if already exists in dictionary
                                        if names[i].strip() == '' and i != 0:
                                            names[i] = names[i - 1]
                                        if i == 0:
                                            # first item: definitions in column and cell
                                            defs = names[i] + ' ' + ' '.join(words[:word]) + ' ' + ' '.join(words[word + 1:]) + ' ' + ' '.join(row[i + 1:])
                                        else:
                                            # not first: definitions in row, column and cell
                                            defs = names[i] + ' ' + row[0] + ' ' + ' '.join(words[:word]) + ' ' + ' '.join(words[word + 1:]) + ' ' + ' '.join(row[i + 1:])
                                        # try to find person marking
                                        person = re.findall(r'(\d)[^\s]*?\s?([^\s]*?)\s?((s(in)?g|pl|du)(.*)|(s|p|d)(\s|$))', defs.lower())
                                        if person:
                                            if person[0][2].startswith('s'):
                                                number = 'SG'
                                            elif person[0][2].startswith('d'):
                                                number = 'DU'
                                            else:
                                                number = 'PL'
                                            key = person[0][0].strip() + number
                                            if key in dic_of_glosses[w]:
                                                for it in dic[key]:
                                                    if list(it.keys())[0] == w and 'TAB. ' + num not in it[w]:
                                                        it[w].append('TAB. ' + num)
                                                        break
                                            else:
                                                if key in dic.keys():
                                                    for it in dic[key]:
                                                        if w in it.keys() and 'TAB. ' + num not in it[w]:
                                                            it[w].append('TAB. ' + num)
                                                            f = 1
                                                            break
                                                    if f == 0:
                                                        dic[key].append({w: ['TAB. ' + num]})
                                                else:
                                                    dic[key] = [{w: ['TAB. ' + num]}]
                                            continue
                                        # try to find noun class marking
                                        gender = re.findall(r'\b\d|\b[IV]+\b', defs)
                                        if gender and len(gender) == 1:
                                            gender = gender[0]
                                            person = re.findall(r'\b((s(in)?g|pl|du)(.*)|(s|p|d)(\s|$))', defs.lower())
                                            if person:
                                                if person[0][1].startswith('s'):
                                                    number = 'SG'
                                                elif person[0][1].startswith('d'):
                                                    number = 'DU'
                                                else:
                                                    number = 'PL'
                                                key = gender + number
                                                if key in dic_of_glosses[w]:
                                                    for it in dic[key]:
                                                        if list(it.keys())[0] == w and 'TAB. ' + num not in it[w]:
                                                            it[w].append('TAB. ' + num)
                                                            break
                                                else:
                                                    if key in dic.keys():
                                                        for it in dic[key]:
                                                            if w in it.keys() and 'TAB. ' + num not in it[w]:
                                                                it[w].append('TAB. ' + num)
                                                                f = 1
                                                                break
                                                        if f == 0:
                                                            dic[key].append({w: ['TAB. ' + num]})
                                                    else:
                                                        dic[key] = [{w: ['TAB. ' + num]}]
                                                continue
                                        defs = defs.split()
                                        flag = 0
                                        for d in defs:  # try to find in Wiki-glosses
                                            d = d.strip(';:,.()')
                                            if d.lower() in valuess:  # keyword
                                                flag = 1
                                                index = valuess.index(d.lower())
                                                key = keyss[index]
                                                if key in dic_of_glosses[w]:
                                                    for it in dic[key]:
                                                        if list(it.keys())[0] == w and 'TAB. ' + num not in it[w]:
                                                            it[w].append('TAB. ' + num)
                                                else:
                                                    if key in dic.keys():
                                                        for it in dic[key]:
                                                            if w in it.keys() and 'TAB. ' + num not in it[w]:
                                                                it[w].append('TAB. ' + num)
                                                                f = 1
                                                        if f == 0:
                                                            dic[key].append({w: ['TAB. ' + num]})
                                                    else:
                                                        dic[key] = [{w: ['TAB. ' + num]}]
                                            elif d.upper() in keyss:  # gloss
                                                flag = 1
                                                key = d.upper()
                                                if key in dic_of_glosses[w]:
                                                    for it in dic[key]:
                                                        if list(it.keys())[0] == w and 'TAB. ' + num not in it[w]:
                                                            it[w].append('TAB. ' + num)
                                                else:
                                                    if key in dic.keys():
                                                        for it in dic[key]:
                                                            if w in it.keys() and 'TAB. ' + num not in it[w]:
                                                                it[w].append('TAB. ' + num)
                                                                f = 1
                                                        if f == 0:
                                                            dic[key].append({w: ['TAB. ' + num]})
                                                    else:
                                                        dic[key] = [{w: ['TAB. ' + num]}]
                                            if flag == 1:
                                                break
                                        if flag == 0:  # not found -> append to each gloss
                                            for key in dic_of_glosses[w]:
                                                for it in dic[key]:
                                                    if list(it.keys())[0] == w and 'TAB. ' + num not in it[w]:
                                                        it[w].append('TAB. ' + num)
                                    elif w in dic_of_glosses.keys() and len(dic_of_glosses[w]) == 1:  # only one gloss -> append
                                        for it in dic[dic_of_glosses[w][0]]:
                                            if list(it.keys())[0] == w and 'TAB. ' + num not in it[w]:
                                                it[w].append('TAB. ' + num)
                                    else:  # not in dictionary
                                        if i == 0:
                                            # first item: definitions in column and cell
                                            defs = names[i] + ' ' + ' '.join(words[:word]) + ' ' + ' '.join(words[word + 1:]) + ' ' + ' '.join(row[i + 1:])
                                        else:
                                            # not first: definitions in row, column and cell
                                            defs = names[i] + ' ' + row[0] + ' ' + ' '.join(words[:word]) + ' ' + ' '.join(words[word + 1:]) + ' ' + ' '.join(row[i + 1:])
                                        # try to find person marking
                                        person = re.findall(r'(\d)[^\s]*?\s?([^\s]*?)\s?((s(in)?g|pl|du)(.*)|(s|p|d)(\s|$))', defs.lower())
                                        if person:
                                            if person[0][2].startswith('s'):
                                                number = 'SG'
                                            elif person[0][2].startswith('d'):
                                                number = 'DU'
                                            else:
                                                number = 'PL'
                                            key = person[0][0].strip() + number
                                            if key in dic.keys():
                                                for it in dic[key]:
                                                    if w in it.keys() and 'TAB. ' + num not in it[w]:
                                                        it[w].append('TAB. ' + num)
                                                        f = 1
                                                        break
                                                if f == 0:
                                                    dic[key].append({w: ['TAB. ' + num]})
                                            else:
                                                dic[key] = [{w: ['TAB. ' + num]}]
                                            continue
                                        # try to find noun class marking
                                        gender = re.findall(r'\b\d|\b[IV]+\b', defs)
                                        if gender and len(gender) == 1:
                                            gender = gender[0]
                                            person = re.findall(r'\b((s(in)?g|pl|du)(.*)|(s|p|d)(\s|$))', defs.lower())
                                            if person:
                                                if person[0][1].startswith('s'):
                                                    number = 'SG'
                                                elif person[0][1].startswith('d'):
                                                    number = 'DU'
                                                else:
                                                    number = 'PL'
                                                key = gender + number
                                                if key in dic.keys():
                                                    for it in dic[key]:
                                                        if w in it.keys() and 'TAB. ' + num not in it[w]:
                                                            it[w].append('TAB. ' + num)
                                                            f = 1
                                                            break
                                                    if f == 0:
                                                        dic[key].append({w: ['TAB. ' + num]})
                                                else:
                                                    dic[key] = [{w: ['TAB. ' + num]}]
                                                continue
                                        defs = defs.split()
                                        for d in defs:  # try to find in Wiki-glosses
                                            d = d.strip(';:,.()')
                                            if d.lower() in valuess:  # keyword
                                                index = valuess.index(d.lower())
                                                key = keyss[index]
                                                if key in dic.keys():
                                                    for it in dic[key]:
                                                        if w in it.keys() and 'TAB. ' + num not in it[w]:
                                                            it[w].append('TAB. ' + num)
                                                            f = 1
                                                            break
                                                    if f == 0:
                                                        dic[key].append({w: ['TAB. ' + num]})
                                                else:
                                                    dic[key] = [{w: ['TAB. ' + num]}]
                                            elif d.upper() in keyss:  # gloss
                                                flag = 1
                                                key = d.upper()
                                                if key in dic.keys():
                                                    for it in dic[key]:
                                                        if w in it.keys() and 'TAB. ' + num not in it[w]:
                                                            it[w].append('TAB. ' + num)
                                                            f = 1
                                                            break
                                                    if f == 0:
                                                        dic[key].append({w: ['TAB. ' + num]})
                                                else:
                                                    dic[key] = [{w: ['TAB. ' + num]}]
    with open(path + '/' + name.split('.')[0] + '_all_glosses.json', 'w', encoding='utf-8') as f:  # dictionary to JSON
        json.dump(dic, f, ensure_ascii=False)


# In[143]:


def beautify_glosses(name):  # glosses to table
    path = name.split('.')[0]
    with open(path + '/' + name.split('.')[0] + '_all_glosses.json', encoding='utf-8') as file:  # open JSON
        dic = json.load(file)
        dic = dict(sorted(dic.items()))
    df = pd.DataFrame(columns=['Gloss', 'Affix', 'Examples'])  # create table
    for gloss in dic:
        for pair in dic[gloss]:
            for key in list(pair.keys()):
                affix = '-' + key + '-'
                examples = ''
                for i in range(len(pair[key])):
                    tab = 0
                    if pair[key][i].startswith('TAB.'):  # if it's table entry
                        page, example = pair[key][i].split()[1].split('_')
                        tab = 1
                    else:  # if it's example entry
                        example, page = pair[key][i].split('_')
                    if i == 0 and i == len(pair[key]) - 1:
                        # beautifying list of examples and tables
                        if tab == 1:
                            examples += 'p. ' + page + ' tab. (' + example + ')'
                        else:
                            examples += 'p. ' + page + ' (' + example + ')'
                    elif i == 0:
                        if tab == 1:
                            examples += 'p. ' + page + ' tab. (' + example + ')'
                        else:
                            examples += 'p. ' + page + ' (' + example + ')'
                    elif i == len(pair[key]) - 1:
                        if tab == 1:
                            examples += ', p. ' + page + ' tab. (' + example + ')'
                        else:
                            examples += ', p. ' + page + ' (' + example + ')'
                    else:
                        if tab == 1:
                            examples += ', p. ' + page + ' tab. (' + example + ')'
                        else:
                            examples += ', p. ' + page + ' (' + example + ')'
                # add to table
                df = pd.concat([df, pd.DataFrame([[gloss, affix, examples], ], columns=['Gloss', 'Affix', 'Examples'])], ignore_index=True)
    # drop duplicates
    df = df.drop_duplicates().reset_index().drop(columns=['index'])
    df.to_csv(path + '/' + name.split('.')[0] + '_glosses.csv')  # to CSV
    return df


# In[144]:


def beautify_examples(name):  # examples to table
    path = name.split('.')[0]
    with open(path + '/' + name.split('.')[0] + '.json', encoding='utf-8') as file:  # open JSON
        dic = json.load(file)
        dic = dict(sorted(dic.items()))
    df = pd.DataFrame(columns=['Number_Example', 'Page', 'Example', 'Glossing', 'Translation'])  # create table
    for number in dic:
        example, page = number.split('_')  # number and page
        for pair in dic[number]:
            if type(pair) == list and len(pair) == 3:  # 3 lines
                words, words_new = prettify(pair[0])
                glossed_words, glossed_words_new = prettify(pair[1])
                if len(words_new) != len(glossed_words_new):  # not equal number of words
                    # try to delete everything inside square brackets 
                    words = re.sub(r'\[.*?\]', '', words)
                    words = re.sub(r'\s{2,}', ' ', words)
                    words = words.split()
                    glossed_words = re.sub(r'\[.*?\]', '', glossed_words)
                    glossed_words = re.sub(r'\s{2,}', ' ', glossed_words)
                    glossed_words = glossed_words.split()
                else:
                    glossed_words = glossed_words_new
                    words = words_new
                if len(words) == len(glossed_words):  # equal number of words
                    words = ' '.join(words)
                    glossed_words = ' '.join(glossed_words)
                    # split by dividers
                    word = re.split(r'\s|-|=|~|<|>', words)
                    glossed_word = re.split(r'\s|-|=|~|<|>', glossed_words)
                    if words.strip() and len(word) == len(glossed_word):  # write to table
                        df = pd.concat([df, pd.DataFrame([[example, page, words, glossed_words, pair[2]], ], columns=['Number_Example', 'Page', 'Example', 'Glossing', 'Translation'])], ignore_index=True)
            elif type(pair) == dict:
                for key in list(pair.keys()):
                    if len(pair[key]) == 3:  # 3 lines
                        words, words_new = prettify(pair[key][0])
                        glossed_words, glossed_words_new = prettify(pair[key][1])
                        if len(words_new) != len(glossed_words_new):  # not equal number of words
                            # try to delete everything inside square brackets 
                            words = re.sub(r'\[.*?\]', '', words)
                            words = re.sub(r'\s{2,}', ' ', words)
                            words = words.split()
                            glossed_words = re.sub(r'\[.*?\]', '', glossed_words)
                            glossed_words = re.sub(r'\s{2,}', ' ', glossed_words)
                            glossed_words = glossed_words.split()
                        else:
                            glossed_words = glossed_words_new
                            words = words_new
                        if len(words) == len(glossed_words):  # equal number of words
                            words = ' '.join(words)
                            glossed_words = ' '.join(glossed_words)
                            # split by dividers
                            word = re.split(r'\s|-|=|~|<|>', words)
                            glossed_word = re.split(r'\s|-|=|~|<|>', glossed_words)
                            if words.strip() and len(word) == len(glossed_word):  # write to table
                                df = pd.concat([df, pd.DataFrame([[example, str(page) + ' (' + key + ')', words, glossed_words, pair[key][2]], ], columns=['Number_Example', 'Page', 'Example', 'Glossing', 'Translation'])], ignore_index=True)
    df = df.drop_duplicates().reset_index().drop(columns=['index'])
    # drop duplicates
    df.to_csv(path + '/' + name.split('.')[0] + '_examples.csv')  # to CSV
    return df


# In[156]:


sheet_id = '1Hjfru6VSZWIyt2Gg6ZRRtvAeQrgmOM2GAi8LMT6whs0'  # Goofle Sheets with 1000 checked grammars
sheet_name ='Sheet1'
url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
grammars = pd.read_csv(url)  # upload table
grams = grammars[(grammars['да/нет'] == 'да')].sort_values(by='про какой язык')  # searchable ones


# In[166]:


UPLOAD_FOLDER = os.getcwd()  # folder to upload
app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# In[167]:


@app.route('/')  # starting page
def index():
    options = ''
    for index, row in grams.iterrows():
        # options from Google Sheets
        options += '<option value="{}">{}</option>\n'.format(row['id'], row['полный путь'].split('/')[-1].split('.')[0])
    return render_template('index.html', options = options, ID = row['id'])

@app.route('/results', methods=['POST', 'GET'])  # resulting page
def upload_route_summary():
    if request.method == 'POST':  # submit file
        file = request.files['fileupload']
        filename = secure_filename(file.filename)
        if not os.path.exists(filename.split('.')[0]):  # not in foler
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            extract_examples_tables(filename)
            glossing(filename)
            table_glossing(filename)
            table1 = beautify_glosses(filename).to_html(justify='center', escape=False)
            # change examples' numbers to links
            table1 = re.sub(r"p\. (\d+?) \((.+?)\)", r"p. \g<1> (<a href='/example?page=\g<1>&example=\g<2>&filename={}'>\g<2></a>)".format(filename.split('.')[0]), table1)
            # change tables' numbers to links
            table1 = re.sub(r"p\. (\d+?) tab\. \((.+?)\)", r"p. \g<1> tab. (<a href='/table?page=\g<1>&table=\g<2>&filename={}'>\g<2></a>)".format(filename.split('.')[0]), table1)
            table2 = beautify_examples(filename).to_html(justify='center', escape=False)
            name = filename.split('.')[0] + '/' + filename.split('.')[0]
        else:  # already in folder
            table1 = beautify_glosses(filename).to_html(justify='center', escape=False)
            table1 = re.sub(r"p\. (\d+?) \((.+?)\)", r"p. \g<1> (<a href='/example?page=\g<1>&example=\g<2>&filename={}'>\g<2></a>)".format(filename.split('.')[0]), table1)
            table1 = re.sub(r"p\. (\d+?) tab\. \((.+?)\)", r"p. \g<1> tab. (<a href='/table?page=\g<1>&table=\g<2>&filename={}'>\g<2></a>)".format(filename.split('.')[0]), table1)
            table2 = beautify_examples(filename).to_html(justify='center', escape=False)
            name = filename.split('.')[0] + '/' + filename.split('.')[0]
    elif request.method == 'GET':  # submit one from Google Sheets or return
        if request.args.get('filename'):  # returned one
            filename = request.args.get('filename') + '.pdf'
            table1 = beautify_glosses(filename).to_html(justify='center', escape=False)
            table1 = re.sub(r"p\. (\d+?) \((.+?)\)", r"p. \g<1> (<a href='/example?page=\g<1>&example=\g<2>&filename={}'>\g<2></a>)".format(filename.split('.')[0]), table1)
            table1 = re.sub(r"p\. (\d+?) tab\. \((.+?)\)", r"p. \g<1> tab. (<a href='/table?page=\g<1>&table=\g<2>&filename={}'>\g<2></a>)".format(filename.split('.')[0]), table1)
            table2 = beautify_examples(filename).to_html(justify='center', escape=False)
            name = filename.split('.')[0] + '/' + filename.split('.')[0]
        elif request.args.get('vars'):  # submitted from Google Sheets
            ID = request.args.get('vars')
            url = 'https://drive.google.com/uc?id=' + ID  # ID in Google Drive
            filename = 'file.pdf'
            gdown.download(url, os.path.join(app.config['UPLOAD_FOLDER'], filename))  # download by ID from Google Drive
            extract_examples_tables(filename)
            glossing(filename)
            table_glossing(filename)
            table1 = beautify_glosses(filename).to_html(justify='center', escape=False)
            table1 = re.sub(r"p\. (\d+?) \((.+?)\)", r"p. \g<1> (<a href='/example?page=\g<1>&example=\g<2>&filename={}'>\g<2></a>)".format(filename.split('.')[0]), table1)
            table1 = re.sub(r"p\. (\d+?) tab\. \((.+?)\)", r"p. \g<1> tab. (<a href='/table?page=\g<1>&table=\g<2>&filename={}'>\g<2></a>)".format(filename.split('.')[0]), table1)
            table2 = beautify_examples(filename).to_html(justify='center', escape=False)
            name = filename.split('.')[0] + '/' + filename.split('.')[0]
    return render_template('data.html', table1 = table1, table2 = table2, name = name)


@app.route('/download', methods=['GET'])  # download data
def downloadFile():
    if not request.args:
        return redirect(url_for('/results'))
    table = request.args.get('vars')
    if table.endswith('.csv'):  # CSV-table
        return send_file(table, as_attachment=True)
    elif table.endswith('.jpeg'):  # ZIP of tables in .jpeg and .csv
        t = table.split('/')[0]
        with ZipFile(table + '_tables.zip', 'w') as zipObj:
            for file in os.listdir(path=t + '/'):
                if file.endswith('.jpeg') or (file.endswith('.csv') and file[0].isdigit()):
                    zipObj.write(t + '/' + file)
        return send_file(table + '_tables.zip', as_attachment=True)
    else:  # the whole ZIP
        t = table.split('/')[0]
        with ZipFile(table + '.zip', 'w') as zipObj:
            zipObj.write(table + '_glosses.csv')
            zipObj.write(table + '_examples.csv')
            for file in os.listdir(path=t + '/'):
                if file.endswith('.jpeg') or (file.endswith('.csv') and file[0].isdigit()):
                    zipObj.write(t + '/' + file)
        return send_file(table + '.zip', as_attachment=True)

@app.route('/example', methods=['GET'])  # link to example
def showExample():
    if not request.args:
        return redirect(url_for('/results'))
    page = request.args.get('page')
    example = request.args.get('example')
    filename = request.args.get('filename')
    table2 = beautify_examples(filename + '.pdf')
    # find example by page and number and convert to HTML
    table2 = table2.loc[(table2['Page'] == page) & (table2['Number_Example'] == example)].to_html(justify='center', escape=False)
    table1 = beautify_glosses(filename + '.pdf')
    # find pairs with this example and convert to HTML
    table1 =  table1[table1['Examples'].str.contains('p. {} ({})'.format(page, example), regex=False)].to_html(justify='center', escape=False)
    return render_template('examples.html', table2 = table2, table1 = table1, filename = filename)

@app.route('/table', methods=['GET'])  # link to table
def showTable():
    if not request.args:
        return redirect(url_for('/results'))
    page = request.args.get('page')
    tab = request.args.get('table')
    filename = request.args.get('filename')
    for file in os.listdir(path=filename + '/'):
        if file.startswith(page + '_' + tab):
            if file.endswith('.jpeg'):
                src_dir = filename + '/' + file
                dst_dir = 'static'
                shutil.copy(src_dir, dst_dir)  # copy image to static
                image = file.replace(' ', '%20')
    table1 = beautify_glosses(filename + '.pdf')
    # find pairs with this table and convert to HTML
    table1 =  table1[table1['Examples'].str.contains('p. {} tab. ({})'.format(page, tab), regex=False)].to_html(justify='center', escape=False)
    return render_template('table.html', image = image, table1 = table1, filename = filename, page = page, tab = tab)


# In[ ]:


if __name__ == '__main__':
    app.run(debug=False)

