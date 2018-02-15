from resources.lib.modules import client,webutils,control,convert
import re,sys,xbmcgui,os,requests,liveresolver
import inspect

from resources.lib.modules.log_utils import log

AddonPath = control.addonPath
IconPath = AddonPath + "/resources/media/"

_channels = {}

def icon_path(filename):
    return os.path.join(IconPath, filename)

class info():
    def __init__(self):
        self.mode = 'arenavision'
        self.name = 'Arenavision.in'
        self.icon = icon_path('av.jpg')
        self.categorized = False
        self.paginated = False
        self.multilink = True

class main():
    def __init__(self):
        self.base = 'http://arenavision.in'
        self.headers = { "Cookie" : "beget=begetok; has_js=1;" }
        self._channels = {}
        self._schedule = None


    def _find_links(self):
        result = client.request('http://arenavision.in', headers=self.headers)
        links, hrefs = client.parseDOM(result,'a'), client.parseDOM(result,'a', ret='href')
        for i,link in enumerate(links):
            if link.startswith('ArenaVision'):
                self._channels[int(link[-2:])] = hrefs[i]
                continue
            if link.startswith('EVENTS'):
                log('batman : ' + hrefs[i])
                self._schedule = hrefs[i]


    def links(self,url):
        self._find_links()
        links = re.findall('(\d+.+?)\[(.+?)\]',url)
        links=self.__prepare_links(links)
        return links

    def channels(self):
        if self._schedule is None:
            self._find_links()
        result = client.request('http://arenavision.in' + self._schedule, headers=self.headers)
        tables = client.parseDOM(result,'table',attrs={'style':'width: 100%; float: left'})
        if tables:
            table = tables[0]
        rows = client.parseDOM(table,'tr')
        events = self.__prepare_events(rows)
        return events


    @staticmethod
    def convert_time(time,date):
        li = time.split(':')
        li2 = date.split('/')
        hour,minute=li[0],li[1]
        day,month,year = li2[0],li2[1],li2[2]
        import datetime
        from resources.lib.modules import pytzimp
        d = pytzimp.timezone(str(pytzimp.timezone('Europe/Ljubljana'))).localize(datetime.datetime(int(year), int(month), int(day), hour=int(hour), minute=int(minute)))
        timezona= control.setting('timezone_new')
        my_location=pytzimp.timezone(pytzimp.all_timezones[int(timezona)])
        convertido=d.astimezone(my_location)
        fmt = "%A, %B %d, %Y"
        fm2 = "%H:%M"
        time=convertido.strftime(fmt)
        tm = convertido.strftime(fm2)
        return tm,time



    def __prepare_events(self,events):
        new = []
        events.pop(0)
        date_old = ''
        for event in events:
            items = client.parseDOM(event,'td')
            i = 0

            for item in items:

                if i==0:
                    date = item
                elif i==1:
                    time = item.replace('CET','').strip()
                elif i==2:
                    sport = item
                elif i==3:
                    competition = item
                elif i==4:
                    event = webutils.remove_tags(item)
                elif i==5:
                    url = item

                i += 1
            try:
                time, date = self.convert_time(time,date)
                if date != date_old:
                    date_old = date
                    new.append(('x','[COLOR yellow]%s[/COLOR]'%date, info().icon))
                sport = '%s - %s'%(sport,competition)
                event = re.sub('\s+',' ',event)
                title = '[COLOR orange](%s)[/COLOR] (%s) [B]%s[/B]'%(time,sport,convert.unescape(event))
                title = title.encode('utf-8')
                new.append((url,title, info().icon))
            except Exception as e:
                log(e)


        return new

    def __prepare_links(self,links):
        new=[]
        if self._schedule is None:
            self._find_links()

        for link in links:
            lang = link[1]
            urls = link[0].split('-')
            for u in urls:
                title = '[B]AV%s[/B] [%s]'%(u,lang)
                url = self._channels[int(u)]
                new.append((url,title))
        return new

    def resolve(self,url):
        headers = {
                "Cookie" : "beget=begetok; has_js=1;"
        }
        try:
            log('batman : ' + url)
            source = requests.get(url,headers=headers).text
        except:
            source = None
        if source:
            match = re.compile('sop://(.+?)"').findall(source)
            if match:
                log("sop://" + match[0])
                return "sop://" + match[0]
            else:
                match = re.compile('this.loadPlayer\("(.+?)"').findall(source)
                if match:
                    return liveresolver.resolve("acestream://" + match[0])
                else:
                    pass
