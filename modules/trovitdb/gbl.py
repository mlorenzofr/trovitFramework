#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import trovitdb


class dbTrovitGlobalException(Exception):
    pass


class trovitGlobal(trovitdb):
    _confSection = 'trovit_global'
    _verticalMaps = {0: 'generic',
                     1: 'homes',
                     2: 'cars',
                     4: 'jobs',
                     8: 'products',
                     16: 'rentals'}
    _typeMaps = {1: 'search',
                 2: 'kw',
                 12: 'ppc',
                 15: 'trends',
                 16: 'trends2',
                 18: 'geo',
                 19: 'geofilter'}

    def getAllCores(self, dKey='core'):
        """
        Return dictionary with all the Trovit cores and servers
        @dKey: str(core|server) set the key for the dict
        Return: dict{'key': list(server1|core1, server2|core2, ...), ...}
        """
        dictCores = {}
        cores = self.query("SELECT s_server, \
                                   fk_c_id_tbl_countries, \
                                   fk_i_id_tbl_vertical, \
                                   fk_i_id_tbl_type_scripts \
                            FROM tbl_solr_server_index \
                            INNER JOIN tbl_lucene_servers \
                            ON fk_i_id_tbl_lucene_servers = i_id \
                            WHERE i_environment = 1 \
                                  AND tbl_lucene_servers.i_active = 1 \
                                  AND tbl_solr_server_index.i_active = 1")
        for core in cores:
            corename = '%s_%s_%s' % (self._typeMaps[core[3]],
                                     self._verticalMaps[core[2]],
                                     core[1])
            if core[1] in ('gf', 'gg'):
                corename = corename[:-3]
            if dKey == 'server':
                key = core[0]
                value = corename
            else:
                key = corename
                value = core[0]
            if key in dictCores:
                dictCores[key].append(value)
            else:
                dictCores[key] = [value]
        return dictCores
