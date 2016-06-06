
import sys
import os
import os.path
import requests
from bs4 import BeautifulSoup
from time import localtime, strftime

DEBUG = True

htmlhead = '<html>\n<body>\n<meta http-equiv="content-type" content="text/html; charset=utf-8" />\n'
htmltail = '</body>\n</html>'

if not DEBUG:
    index_source = r'D:\Google Drive\Crystal_DB\index.source'
    index_html = r'D:\Google Drive\Crystal_DB\index.html'
else:
    index_source = r'index.source'
    index_html = r'index.html'

Test_List = [
    'http://www.104.com.tw/jobbank/custjob/index.php?r=cust&jobsource=n104bank1&j=3c4a446b5646406748423a1d1d1d1d5f2443a363189j99' #Starbucks
]

Compony_List = [
    'https://www.104.com.tw/jobbank/custjob/index.php?r=cust&j=4339416a33353d662f313962373d3518628282825406b416795j51',  #唯晶數位娛樂股份有限公司
    'https://www.104.com.tw/jobbank/custjob/index.php?r=cust&j=4460422940363f6952583a1d1d1d1d5f2443a363189j52',  #Tata Consultancy Services Limited Taiwan Branch(印度商塔塔顧問服務有限公司台灣分公司)
    'https://www.104.com.tw/jobbank/custjob/index.php?r=cust&j=5e70432448363f675a583a1d1d1d1d5f2443a363189j01',  #物聯智慧股份有限公司
    'https://www.104.com.tw/jobbank/custjob/index.php?r=cust&j=444a43295a5c3e6844583a1d1d1d1d5f2443a363189j52',  #瑞嘉軟體科技股份有限公司
    'https://www.104.com.tw/jobbank/custjob/index.php?r=cust&j=4f4149723b3d456e3739416a3f453d2083030302e494d457119j02',  #智寶科技服務有限公司
]

def is_hot_job(job, page):
    jobscope = job.parent.parent
    try:
        if jobscope.find_all('img')[0].get('src') == "http://www.104.com.tw/jobbank/custjob/image/icon_urgency.gif":
            return True
        else:
            return False
    except IndexError:
        return False


def totalpages(web):
    response = requests.get(str(web))
    soup = BeautifulSoup(response.text.encode('utf-8'), 'html.parser')

    tags = soup.find_all('input', attrs={"name": "totalpage"})[0]
    return int(tags.get('value'))


def parse_source_to_html():
    with open(index_source, 'r', encoding = 'ISO8859-1') as f:
        job_database = f.readlines()
        f.close()

    html = []
    html.append(htmlhead)
    html.append('Last update: ' + strftime('%Y-%m-%d %H:%M:%S\n', localtime()))

    for string in job_database:
        if '_COM_' in string:
            html.append('<h2>')
            for lines in job_database[job_database.index(string):]:
                webfound = False
                if '_WEB_' in lines:
                    webfound = True
                    html.append('<a href="' + lines[5:] + '">')
                    break
            html.append(string[5:].rstrip('\n'))
            if webfound:
                html.append('</a>')
            html.append('</h2>\n')
            html.append('<pre>\n')
        if '_JOB_' in string:
            jobdsc = '{:<70} {:<20} {}'.format(string[5:].rstrip('\n').ljust(70), job_database[job_database.index(string)+1].rstrip('\n'), job_database[job_database.index(string)+2])
            html.append(jobdsc)
        if '_END_' in string:
            html.append('</pre>\n')
            html.append('<hr>\n')

    html.append(htmltail)
    with open(index_html, 'w', encoding = 'ISO8859-1') as f:
        f.writelines(html)
        f.close()


def parse_html_content(webaddr):
    for page in range(1, totalpages(webaddr) + 1):
        #print('page'+str(page))
        webpage = webaddr + '&page=' + str(page) + '#info06s'
        response = requests.get(webpage)
        soup = BeautifulSoup(response.text.encode('utf-8'), 'html.parser')

        # get the compony name
        if page == 1:
            compony = list('_COM_' + ''.join(list(soup.h1.stripped_strings)) + '\n')
            compony.append('_WEB_' + str(webaddr) + '\n')

        # append the job name and reserve the start/end timestamp
        for job in soup.find_all('div', class_ = 'jobname'):
            if isinstance(job.a, type(soup.a)):
                if job.a.get_text() in compony:
                    print('already have')
                    continue

                # to avoid the duplication of hot job as a record
                if page > 1 and is_hot_job(job, page):
                    continue

                compony.append('_JOB_' + job.a.get_text() + '\n')
                compony.append(strftime('%Y-%m-%d\n', localtime()))
                compony.append('_STOP_\n')

    # append the _END_ tag
    compony += list('_END_' + ''.join(list(soup.h1.stripped_strings)) + '\n')

    # check index.source. If the file is not exist, write the data into index.source directly
    filepath = index_source
    if not os.path.isfile(index_source):
        filepath = index_source
    else:
        filepath = 'tmp.source'
    with open(filepath, 'w', encoding = response.encoding) as f:
        f.writelines(compony)
        f.close()

    # merge the index.source and tmp.source, 因為處理unicode,
    # 所以我們選擇先寫入檔案後重新讀出來
    with open(index_source, 'r', encoding = response.encoding) as f:
        all_compony = f.readlines()
        f.close()

    try:
        with open('tmp.source', 'r', encoding = response.encoding) as f:
            current_compony = f.readlines()
            f.close()
    except FileNotFoundError:
        return

    # It is a new company, copy all contents to the index.source
    if '_COM_' in current_compony[0] and current_compony[0] not in all_compony:
        newlist = all_compony + current_compony
        with open(index_source, 'r+', encoding = response.encoding) as f:
            f.writelines(newlist)
            f.close()

    # 有找到既有資料, 先複製一份出來, 整理完之後在 append 回去, 避免不同公司會有相同名稱職缺
    if '_COM_' in current_compony[0] and current_compony[0] in all_compony:
        ComponyEnd = current_compony[0].replace('_COM_', '_END_')
        compony_data = all_compony[all_compony.index(current_compony[0]):all_compony.index(ComponyEnd) + 1]
        all_compony[all_compony.index(current_compony[0]):all_compony.index(ComponyEnd) + 1] = ()

        # compare job between tmp.source with index.source
        #
        # _JOB_    : xxxxx      << index(job)
        # _START_  : start time << index(job) + 1
        # _STOP_   : end time   << index(job) + 2
        #
        appendlist = []

        for job in current_compony:
            if '_JOB_' in job and job not in compony_data:
                # here is the new job which is not in the database.
                appendlist += current_compony[current_compony.index(job):current_compony.index(job) + 3]
                #print(appendlist)

        for jobrecord in compony_data:
            if '_JOB_' in jobrecord and jobrecord not in current_compony:
                # job is closed
                if compony_data[compony_data.index(jobrecord) + 2].lstrip('\n') is '_STOP_':
                    compony_data[compony_data.index(jobrecord) + 2] = strftime("%Y-%m-%d\n", localtime())

        webfound = False
        for string in compony_data:
            if '_WEB_' in string:
                webfound = True
        if not webfound:
            appendlist.append('_WEB_' + str(webaddr) + '\n')

        if appendlist:
            compony_data = compony_data[:-1] + appendlist + compony_data[-1:]

        all_compony += compony_data
        with open(index_source, 'r+', encoding = response.encoding) as f:
            f.writelines(all_compony)
            f.close()

        # TODO: remove the record which is over 180 days
    os.remove('tmp.source')


def main():
    if DEBUG:
        parse_html_content(Test_List[0])
    else:
        for ComponyWeb in Compony_List:
            parse_html_content(ComponyWeb)

    parse_source_to_html()

if __name__ == '__main__':
    main()
