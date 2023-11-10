from flask import Flask, request, render_template
import requests, sqlite3, datetime

app = Flask(__name__)

host = 'https://pub.orcid.org/v3.0/'
conn = sqlite3.connect("orcid1.db", check_same_thread=False)
cursor = conn.cursor()

count = 0
global temp
resp = []#I really don't remember if we're need in it...

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        orcid_id = request.form.get('orcid_id')
        row = ''
        if orcid_id != None:
            cursor.execute("SELECT * FROM orcid11 WHERE orcid_id=?", (orcid_id,))
            row = cursor.fetchall()
            for i in row:
                if i[0] == orcid_id:
                    return render_template("9.html", table=row)
            return render_template("8.html", text = "We can't find this record")
    else:
        return render_template("8.html")

@app.route('/table', methods=['GET', 'POST'])
def table():
    cursor.execute("SELECT * FROM orcid11")
    resp.append(cursor.fetchall())
    return render_template("7.html", table=resp)

@app.route('/page<int:page_number>', methods=['GET', 'POST'])#общее для страниц списка
def page(page_number):
    resp = []
    cursor.execute("SELECT * FROM orcid11")
    for i in range(page_number-1):
        cursor.fetchmany(size=25)
    for i in range(1):
        resp.append(cursor.fetchmany(size=25))
    return render_template("6.html", table=resp)

if __name__ == "__main__":
    app.run(debug=True)


    now = datetime.datetime.now()#time
    time = now.strftime("%H:%M:%S")
    current_hour = datetime.datetime.now().strftime("%H")
    current_min = datetime.datetime.now().strftime("%M")
    current_sec = datetime.datetime.now().strftime("%S")
    if current_hour=='03' and current_min=='0' and current_sec=='0':
        print("DATABASE WILL BE UPDATED")#вот в этой штуке должно быть всё что обновляет ДБ (наверное)

    cursor.execute("""CREATE TABLE IF NOT EXISTS orcid11
                (orcid_id UNIQUE, name, surname, other_names, country, external_ids, kwords_str, works_counter, works)
                """)
    conn.commit()

    mining_search_res = requests.get(host + 'search/?q=affiliation-org-name:"Saint+Petersburg+Mining+University"', headers = {'Accept': 'application/vnd.orcid+json'}).json()
    #noun = mining_search_res['num-found']
    g = 0
    mining_search_res = mining_search_res['result']
    for i in mining_search_res:#Внос данных в таблицу БД
        g += 1
        orcid_id = i['orcid-identifier']['path']
        person_req = requests.get(host + orcid_id + '/person', headers = {'Accept': 'application/vnd.orcid+json'}).json()
        works_req = requests.get(host + orcid_id + '/works', headers = {'Accept': 'application/vnd.orcid+json'}).json()['group']

        if person_req['name'] is None or person_req['name']['given-names'] is None or person_req['name']['family-name'] is None:# person_req.json():
            name = 'None'
            surname = 'None'
        else:
            name = person_req['name']['given-names']['value']
            surname = person_req['name']['family-name']['value']

        kwords_str = ''
        keywords_req = person_req['keywords']['keyword']
        for i in keywords_req:
            kwords_str = kwords_str + i['content'] + '; '

        #last_m_d_pers = person_req['value']#?
        other_names = ''
        for i in person_req['other-names']['other-name']:
            other_names += i['content']#???

        #biography = person_req['biography']#?
        #person_req['researcher-urls']
        country = ''
        for i in person_req['addresses']['address']:
            country += i['country']['value'] + "; "

        external_ids = ''
        for i in person_req['external-identifiers']['external-identifier']:
            external_ids += i['external-id-type'] + ': ' + i['external-id-value'] + '; '

        works_counter = 0
        works = ''
        #этим кодом заносятся вытаскивается всё про работы
        for i in works_req:
            last_m_d = i['last-modified-date']['value']#?
            works_counter += 1

            ids = i['external-ids']['external-id']
            doi = None
            wos = None
            eid = None
            for j in ids:
                if j['external-id-type'] == 'doi':
                    doi = j['external-id-value']
                if j['external-id-type'] == 'wosuid':
                    wos = j['external-id-value']
                if j['external-id-type'] == 'eid':
                    eid = j['external-id-value']

            w_summary = i['work-summary']


            for j in w_summary:
                if j['external-ids'] != None and j['external-ids']['external-id'] != None:
                    for k in j['external-ids']['external-id']:
                        if k['external-id-type'] == 'doi':
                            if doi == None:
                                doi = k['external-id-value']
                        if k['external-id-type'] == 'wosuid':
                            if wos == None:
                                wos = k['external-id-value']
                        if k['external-id-type'] == 'eid':
                            if eid == None:
                                eid = k['external-id-value']

                work_title = j['title']['title']['value']

                if j['publication-date'] != None:
                    if j['publication-date']['year'] != None:
                        work_publication_year = j['publication-date']['year']['value']

                if doi != None:
                    works += 'doi: ' + doi + ', '
                if wos != None:
                    works += 'wos: ' + wos + ', '
                if eid != None:
                    works += 'eid: ' + eid + ', '
                works += work_title + ', ' + work_publication_year + ';\n'
        print(g, orcid_id, name, surname)

        if cursor.fetchone() is None:
            cursor.execute("INSERT OR REPLACE INTO orcid11(orcid_id, name, surname, other_names, country, external_ids, kwords_str, works_counter, works) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (orcid_id, name, surname, other_names, country, external_ids, kwords_str, works_counter, works))
            conn.commit()
#Всё ниже для маленькой таблицы
    # cursor.execute("""CREATE TABLE IF NOT EXISTS orcid7
    #             (name text, surname text, orcid_id text UNIQUE, k_words text, works text)
    #             """)
    # conn.commit()

    # for i in mining_search_res:#Внос данных в little таблицу БД
    #     orcid_id = i['orcid-identifier']['path']
    #     person_req = requests.get(host + orcid_id + '/person', headers = {'Accept': 'application/vnd.orcid+json'})
    #     works_req = requests.get(host + orcid_id + '/works', headers = {'Accept': 'application/vnd.orcid+json'}).json()['group']
    #     if person_req.json()['name'] is None or person_req.json()['name']['given-names'] is None or person_req.json()['name']['family-name'] is None:# person_req.json():
    #         name = 'None'
    #         surname = 'None'
    #         print(count, orcid_id, "None")
    #     else:
    #         count = count + 1
    #         name = person_req.json()['name']['given-names']['value']
    #         surname = person_req.json()['name']['family-name']['value']
    #
    #     kwords_str = ''
    #     keywords_req = person_req.json()['keywords']['keyword']
    #     for i in keywords_req:
    #         kwords_str = kwords_str + i['content'] + '; '
    #
    #     #этим кодом заносятся doi работ человека в строку
    #     works_str = ''
    #     for i in works_req:
    #         a = i['external-ids']['external-id']
    #         for j in a:
    #             if j['external-id-type'] == "doi":
    #                 works_str = works_str + j['external-id-value'] + '; '
    #
    #     #а этим
    #
    #     print(name, surname, orcid_id, kwords_str, works_str)
    #     if cursor.fetchone() is None:
    #         cursor.execute("INSERT OR REPLACE INTO orcid7(name, surname, orcid_id, k_words, works) VALUES (?, ?, ?, ?, ?)", (name, surname, orcid_id, kwords_str, works_str))
    #         conn.commit()