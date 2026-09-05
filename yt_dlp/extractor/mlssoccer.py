from .common import InfoExtractor


class MLSSoccerIE(InfoExtractor):
    _VALID_DOMAINS = r'(?:(?:cfmontreal|intermiamicf|lagalaxy|lafc|houstondynamofc|dcunited|atlutd|mlssoccer|fcdallas|columbuscrew|coloradorapids|fccincinnati|chicagofirefc|austinfc|nashvillesc|whitecapsfc|sportingkc|soundersfc|sjearthquakes|rsl|timbers|philadelphiaunion|orlandocitysc|newyorkredbulls|nycfc)\.com|(?:torontofc)\.ca|(?:revolutionsoccer)\.net)'
    _VALID_URL = rf'https?://(?:www\.)?{_VALID_DOMAINS}/video/#?(?P<id>[^/&$#?]+)'

    _TESTS = [{
        'url': 'https://www.mlssoccer.com/video/the-octagon-can-alphonso-davies-lead-canada-to-first-world-cup-since-1986#the-octagon-can-alphonso-davies-lead-canada-to-first-world-cup-since-1986',
        'md5': 'd35fb3ec5c36bcde5a8ffd367b2312c0',
        'info_dict': {
            'id': '6276033198001',
            'ext': 'mp4',
            'title': 'Can Alphonso Davies lead Canada to its first World Cup since 1986?',
            'description': 'md5:2e219018f7bb03eb2da78f74a09d2dfe',
            'thumbnail': r're:https?://.+\.jpg',
            'duration': 350.165,
            'timestamp': 1633627291,
            'uploader_id': '5530036772001',
            'tags': ['club/canada', 'competition/concacaf world cup qualifiers'],
            'upload_date': '20211007',
        },
        # Default format `b` prefers HLS; force progressive so --test is a stable 10KiB HTTP sample
        'params': {'format': 'best[protocol=https]'},
    }, {
        'url': 'https://www.whitecapsfc.com/video/highlights-san-jose-earthquakes-vs-vancouver-whitecaps-fc-october-23-2021#highlights-san-jose-earthquakes-vs-vancouver-whitecaps-fc-october-23-2021',
        'only_matching': True,
    }, {
        'url': 'https://www.torontofc.ca/video/highlights-toronto-fc-vs-cf-montreal-october-23-2021-x6733#highlights-toronto-fc-vs-cf-montreal-october-23-2021-x6733',
        'only_matching': True,
    }, {
        'url': 'https://www.sportingkc.com/video/post-match-press-conference-john-pulskamp-oct-27-2021#post-match-press-conference-john-pulskamp-oct-27-2021',
        'only_matching': True,
    }, {
        'url': 'https://www.soundersfc.com/video/highlights-seattle-sounders-fc-vs-sporting-kansas-city-october-23-2021',
        'only_matching': True,
    }, {
        'url': 'https://www.sjearthquakes.com/video/#highlights-austin-fc-vs-san-jose-earthquakes-june-19-2021',
        'only_matching': True,
    }, {
        'url': 'https://www.rsl.com/video/2021-u-of-u-health-mic-d-up-vs-colorado-10-16-21#2021-u-of-u-health-mic-d-up-vs-colorado-10-16-21',
        'only_matching': True,
    }, {
        'url': 'https://www.timbers.com/video/highlights-d-chara-asprilla-with-goals-in-portland-timbers-2-0-win-over-san-jose#highlights-d-chara-asprilla-with-goals-in-portland-timbers-2-0-win-over-san-jose',
        'only_matching': True,
    }, {
        'url': 'https://www.philadelphiaunion.com/video/highlights-torvphi',
        'only_matching': True,
    }, {
        'url': 'https://www.orlandocitysc.com/video/highlight-columbus-crew-vs-orlando-city-sc',
        'only_matching': True,
    }, {
        'url': 'https://www.newyorkredbulls.com/video/all-access-matchday-double-derby-week#all-access-matchday-double-derby-week',
        'only_matching': True,
    }, {
        'url': 'https://www.nycfc.com/video/highlights-nycfc-1-0-chicago-fire-fc#highlights-nycfc-1-0-chicago-fire-fc',
        'only_matching': True,
    }, {
        'url': 'https://www.revolutionsoccer.net/video/two-minute-highlights-revs-1-rapids-0-october-27-2021#two-minute-highlights-revs-1-rapids-0-october-27-2021',
        'only_matching': True,
    }, {
        'url': 'https://www.nashvillesc.com/video/goal-c-j-sapong-nashville-sc-92nd-minute',
        'only_matching': True,
    }, {
        'url': 'https://www.cfmontreal.com/video/faits-saillants-tor-v-mtl#faits-saillants-orl-v-mtl-x5645',
        'only_matching': True,
    }, {
        'url': 'https://www.intermiamicf.com/video/all-access-victory-vs-nashville-sc-by-ukg#all-access-victory-vs-nashville-sc-by-ukg',
        'only_matching': True,
    }, {
        'url': 'https://www.lagalaxy.com/video/#moment-of-the-month-presented-by-san-manuel-casino-rayan-raveloson-scores-his-se',
        'only_matching': True,
    }, {
        'url': 'https://www.lafc.com/video/breaking-down-lafc-s-final-6-matches-of-the-2021-mls-regular-season#breaking-down-lafc-s-final-6-matches-of-the-2021-mls-regular-season',
        'only_matching': True,
    }, {
        'url': 'https://www.houstondynamofc.com/video/postgame-press-conference-michael-nelson-presented-by-coushatta-casino-res-x9660#postgame-press-conference-michael-nelson-presented-by-coushatta-casino-res-x9660',
        'only_matching': True,
    }, {
        'url': 'https://www.dcunited.com/video/tony-alfaro-my-family-pushed-me-to-believe-everything-was-possible',
        'only_matching': True,
    }, {
        'url': 'https://www.fcdallas.com/video/highlights-fc-dallas-vs-minnesota-united-fc-october-02-2021#highlights-fc-dallas-vs-minnesota-united-fc-october-02-2021',
        'only_matching': True,
    }, {
        'url': 'https://www.columbuscrew.com/video/match-rewind-columbus-crew-vs-new-york-red-bulls-october-23-2021',
        'only_matching': True,
    }, {
        'url': 'https://www.coloradorapids.com/video/postgame-reaction-robin-fraser-october-27#postgame-reaction-robin-fraser-october-27',
        'only_matching': True,
    }, {
        'url': 'https://www.fccincinnati.com/video/#keeping-cincy-chill-presented-by-coors-lite',
        'only_matching': True,
    }, {
        'url': 'https://www.chicagofirefc.com/video/all-access-fire-score-dramatic-road-win-in-cincy#all-access-fire-score-dramatic-road-win-in-cincy',
        'only_matching': True,
    }, {
        'url': 'https://www.austinfc.com/video/highlights-colorado-rapids-vs-austin-fc-september-29-2021#highlights-colorado-rapids-vs-austin-fc-september-29-2021',
        'only_matching': True,
    }, {
        'url': 'https://www.atlutd.com/video/goal-josef-martinez-scores-in-the-73rd-minute#goal-josef-martinez-scores-in-the-73rd-minute',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        data_json = self._parse_json(
            self._html_search_regex(r'data-options\=\"([^\"]+)\"', webpage, 'json'), video_id)['videoList'][0]
        return {
            'id': video_id,
            '_type': 'url',
            'url': 'https://players.brightcove.net/{}/default_default/index.html?videoId={}'.format(data_json['accountId'], data_json['videoId']),
            'ie_key': 'BrightcoveNew',
        }
