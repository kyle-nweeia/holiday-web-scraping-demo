from calendar import month_abbr
from datetime import datetime
from itertools import chain
from json import dumps

from flask import Flask, request
from lxml import html
import requests

app = Flask(__name__)

def fetch():
    with open('holidays.csv', 'w') as output:
        def url(i):
            next_year = str(int(datetime.today().strftime('%Y')) + 1)
            return (
                'https://www.timeanddate.com/holidays/us/',
                f'https://www.timeanddate.com/holidays/us/{next_year}',
                )[i]

        for i in range(2):
            page = requests.get(url(i))
            tree = html.fromstring(page.content)
            table = tree.xpath('//table[@id="holidays-table"]/tbody/tr')
            for row in table:
                if not len(row): continue # Skip month headers
                [anchor] = row.xpath('td/a')
                if anchor.get('href')[10:12] != 'us': continue # Skip non-U.S.
                line = ','.join([value.text_content() for value in row])
                output.write(f'{line}\n')

@app.route('/holidays')
def holidays(holidayType=None):
    def date(line): return line.split(',')[0].split() # Get month and day
    def day(date): return int(date[1]) # Get day from date
    def mapper(line): return dict(
        name = line.split(',')[2],
        date = line.split(',')[0],
        type = line.split(',')[3],
        detail = line.split(',')[4][:-1].replace('\xa0', ''),
        )
    def match(line):
        if holidayType is None: return line
        return holidayType.lower() in mapper(line)['type'].lower()
    def matches(lines, results = []):
        if len(results) == 10: return results
        try: line = next(lines)
        except StopIteration: return results
        return matches(lines, results+list(filter(match, [line])))
    def month(date): return list(month_abbr).index(date[0]) # Get month number
    holidayType = request.args.get('holidayType')
    today = datetime.today().strftime('%b %d').split()

    with open('holidays.csv', 'r') as csv:
        for line in csv:
            if month(date(line)) < month(today): continue
            if month(date(line))>month(today) or day(date(line))>day(today):
                return dumps([mapper(x) for x in matches(chain([line], csv))])

def main():
    fetch()
    app.run(debug=True)

if __name__ == '__main__':
    main()
