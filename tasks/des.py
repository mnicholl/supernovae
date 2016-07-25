"""Import tasks for the Dark Energy Survey.
"""
import json
import os

from astrocats.catalog.utils import pbar
from bs4 import BeautifulSoup

from ..supernova import SUPERNOVA


def do_des(catalog):
    task_str = catalog.get_current_task_str()
    des_url = 'https://portal.nersc.gov/des-sn/'
    des_trans_url = des_url + 'transients/'
    ackn_url = ('http://www.noao.edu/'
                'noao/library/NOAO_Publications_Acknowledgments.html'
                '#DESdatause')
    # Make sure there is aa trailing slash
    des_path = os.path.join(catalog.get_current_task_repo(), 'DES', '')
    html = catalog.load_url(des_trans_url, des_path + 'transients.html')
    if not html:
        return
    bs = BeautifulSoup(html, 'html5lib')
    trs = bs.find('tbody').findAll('tr')
    for tri, tr in enumerate(pbar(trs, task_str)):
        name = ''
        # source = ''
        if tri == 0:
            continue
        tds = tr.findAll('td')
        for tdi, td in enumerate(tds):
            if tdi == 0:
                name = catalog.add_entry(td.text.strip())
            if tdi == 1:
                (ra, dec) = [xx.strip() for xx in td.text.split('\xa0')]
            if tdi == 6:
                atellink = td.find('a')
                if atellink:
                    atellink = atellink['href']
                else:
                    atellink = ''

        sources = [catalog.entries[name]
                   .add_source(url=des_url, name='DES Bright Transients',
                               acknowledgment=ackn_url)]
        if atellink:
            sources.append(
                catalog.entries[name]
                .add_source(name='ATel ' + atellink.split('=')[-1],
                            url=atellink))
        sources += [catalog.entries[name]
                    .add_source(bibcode='2012ApJ...753..152B'),
                    catalog.entries[name].add_source(
                        bibcode='2015AJ....150..150F'),
                    catalog.entries[name].add_source(
                        bibcode='2015AJ....150...82G'),
                    catalog.entries[name]
                    .add_source(bibcode='2015AJ....150..172K')]
        sources = ','.join(sources)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, sources)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, ra, sources)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, dec, sources)

        html2 = catalog.load_url(
            des_trans_url + name, des_path + name + '.html')
        if not html2:
            continue
        lines = html2.splitlines()
        for line in lines:
            if 'var data = ' in line:
                jsontxt = json.loads(line.split('=')[-1].rstrip(';'))
                for ii, band in enumerate(jsontxt['band']):
                    upl = True if float(jsontxt['snr'][ii]) <= 3.0 else ''
                    (catalog.entries[name]
                     .add_photometry(time=jsontxt['mjd'][ii],
                                     magnitude=jsontxt['mag'][ii],
                                     e_magnitude=jsontxt['mag_error'][ii],
                                     band=band, observatory='CTIO',
                                     telescope='Blanco 4m', instrument='DECam',
                                     upperlimit=upl, source=sources))

    catalog.journal_entries()
    return
