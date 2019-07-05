# -*- coding: utf-8 -*-
import scrapy
import re


class GooglescholarSpider(scrapy.Spider):
    LABLE = 'machine_learning'
    MAX_AUTHORS = 10000
    MAX_PAPERS = 100
    BY_YEAR = False
    
    name = 'googlescholar'
    allowed_domains = ['scholar.google.com']
    start_urls = ['https://scholar.google.com/citations?hl=en&view_op=search_authors&mauthors=label:{}'.format(LABLE)]
    base_url = 'https://scholar.google.com'

    def __init__(self, *args, **kwargs):
        super(GooglescholarSpider, self).__init__(*args, **kwargs)
        self.authors = 0
        self.papers = 0

    def parse(self, response):
        if self.authors >= GooglescholarSpider.MAX_AUTHORS:
            return
        
        urls = response.css("h3.gs_ai_name a::attr(href)").extract()
        self.authors += len(urls)

        next_onclick = response.css("button.gs_btnPR::attr(onclick)").extract()[0]
        after_author = re.search('after_author\\\\x3d(.+)\\\\x26', next_onclick).group(1)
        start = re.search('start\\\\x3d(\d+)', next_onclick).group(1) 
        next_url = GooglescholarSpider.start_urls[0] + '&after_author={}&astart={}'.format(after_author, start)

        for url in urls:
            url = GooglescholarSpider.base_url + url + '&cstart=0&pagesize={}'.format(GooglescholarSpider.MAX_PAPERS) 
            if GooglescholarSpider.BY_YEAR:
                url += '&view_op=list_works&sortby=pubdate'
            yield scrapy.Request(url , callback=self.parse_author)

        yield scrapy.Request(next_url, callback=self.parse)

    def parse_author(self, response):
        author = response.css("div#gsc_prf_in::text").extract_first()
        titles = response.css("a.gsc_a_at::text").extract()
        citations = [int(x) if x else 0 for x in response.css("a.gsc_a_ac::text").extract()]
        years = response.css("span.gsc_a_hc::text").extract()

        papers = sorted(list(zip(titles, citations, years)), key=lambda x: x[1], reverse=True)

        for paper in papers:
            yield {
                'title': paper[0],
                'author': author,
                'year': paper[2],
                'citation': paper[1]
            }
