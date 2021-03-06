#!/usr/bin/python
##
## Copyright (c) 2014-2017 Leidos.
## 
## License: 3-clause BSD, see https://opensource.org/licenses/BSD-3-Clause
##
##
## Developed under contract #FA8750-14-C-0241
##
from __future__ import print_function

import getopt
import json
import os
import sys
import time
import traceback
import MySQLdb

from contextlib import closing

from locallibs import debug
from locallibs import printMsg
from locallibs import warning

###################

class MuseProjectDB:

    ###
    #def __init__(self, db='muse',user='muse',passwd='muse',loc='muse2-int', port=54321):
    def __init__(self, db='muse',user='muse',passwd='muse',loc='muse2-int', port=54321):

        self.db = db
        self.user = user
        self.passwd = passwd
        self.loc = loc
        self.port = port

        self.conn = None

        self.lBuildTypes = ['configureBuildType','configureacBuildType','configureinBuildType','cmakeBuildType','makefileBuildType','antBuildType', 'mavenBuildType']
        self.lSourceTypes = ['cBuildType','cppBuildType']
        self.lAllTypes = self.lBuildTypes + self.lSourceTypes
        self.lTables = ['projects','buildTargets','buildStatus','buildStatusTargets','sourceTargets']
        self.lViews = ['availableProjects', 'availableTargets','availableSourceTargets','availableSourceTargetsWithSite','availableTargetsWithSite','buildFail','buildMinDepth','buildPartial','buildStatusWithTargets','buildSuccess','buildTopTargets','builtWith_ubuntu12','builtWith_ubuntu14','builtWith_fedora20','builtWith_fedora21','cProjects','cProjectsWithNoBuildTargets','numTargetsPerProject','unBuiltProjects', 'unBuiltSourceTargets','unBuiltSourceTargetsWithSite','unBuiltTargets','unBuiltTargetsWithSite','unknownCProjects']

        self.dTables = {
            'projects': {
                'cols': ['projectName','bytecode_available','source','site','codeDir','c','cpp','csharp','java']
            },
            'buildTargets': {
                'cols': ['projectName','projectPath','buildTargetPath'] + self.lBuildTypes + ['ranking','depth'],
                'colsNoBools': ['projectName','projectPath','buildTargetPath', 'ranking','depth']
            },
            'buildStatus': {
                'cols': ['projectName','projectPath','buildTarPath', 'builder','buildTime','version','os','numObjectsPreBuild','numObjectsPostBuild','numObjectsGenerated','numSources','returnCode']
            },
            'buildStatusTargets': {
                'cols': ['projectName','projectPath','buildTarPath', 'buildTargetPath'] + self.lAllTypes + ['builder','version','os','returnCode'],
                'colsNoBools': ['projectName','projectPath','buildTarPath','buildTargetPath', 'builder','version','os','returnCode']
            },
            'sourceTargets': {
                'cols': ['projectName','projectPath','buildTargetPath'] + self.lSourceTypes,
                'colsNoBools': ['projectName','projectPath','buildTargetPath']
            },
        }

    ###
    def getTables(self):

        return self.lTables

    ###
    def getTableCols(self, sTable):

        if sTable in self.lTables:

            return self.dTables[sTable]['cols']

        else:

            warning('func: getTableCols() table provided sTable:', sTable)
            warning('func: getTableCols() valid values for sTable are:', self.lTables)

        return []

    ###
    def getBuildTypes(self):

        return self.lBuildTypes

    ###
    def getSourceTypes(self):

        return self.lSourceTypes

    ###
    def ready(self):

        if self.conn and self.conn.open:

            return True

        return False 

    ###
    def initialize(self, bDebug=False):

        lQueries = []

        if not self.ready(): self.open(bSetSchema=False)

        # SQL initialization statements
        sQuery = 'DROP DATABASE IF EXISTS ' + self.db + ';'
        lQueries.append(sQuery)

        sQuery = 'CREATE DATABASE ' + self.db + ';'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: initDB()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
                    warning('func: initDB() statement failed to execute:', sQuery) 
                    warning('func: initDB() Unexpected error:', e)
                    break

        self.createProjectsTable(bDebug=bDebug)
        self.createBuildTargetsTable(bDebug=bDebug)
        self.createSourceTargetsTable(bDebug=bDebug)
        self.createBuildStatusTargetsTable(bDebug=bDebug)
        self.createBuildStatusTable(bDebug=bDebug)

    ###
    def createProjectsTable(self, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # create projects table
        sQuery = 'CREATE TABLE IF NOT EXISTS projects ('
        sQuery += '`projectName` VARCHAR(255) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`bytecode_available` BOOL DEFAULT FALSE NOT NULL,'
        sQuery += '`source` BOOL DEFAULT FALSE NOT NULL,'
        sQuery += '`site` VARCHAR(255) CHARACTER SET utf8,'
        sQuery += '`codeDir` VARCHAR(255) CHARACTER SET utf8,'
        
        sQuery += '`c` INT UNSIGNED NOT NULL,'
        sQuery += '`cpp` INT UNSIGNED NOT NULL,'
        sQuery += '`csharp` INT UNSIGNED NOT NULL,'
        sQuery += '`java` INT UNSIGNED NOT NULL,'
        
        sQuery += 'PRIMARY KEY(`projectName`));'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX projects_site ON projects (site) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX projects_codeDir ON projects (codeDir) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX projects_c ON projects (c) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX projects_cpp ON projects (cpp) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX projects_csharp ON projects (csharp) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX projects_java ON projects (java) USING BTREE;'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: createProjectsTable()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
                    warning('func: createProjectsTable() statement failed to execute:', sQuery) 
                    warning('func: createProjectsTable() Unexpected error:', e)
                    break

    ###
    def dropProjectsTable(self, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # drop projects table
        sQuery = 'DROP TABLE IF EXISTS projects;'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: dropProjectsTable()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
                    warning('func: dropProjectsTable() statement failed to execute:', sQuery) 
                    warning('func: dropProjectsTable() Unexpected error:', e)
                    break

    ###
    def createBuildTargetsTable(self, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # create buildTargets table 
        sQuery = 'CREATE TABLE IF NOT EXISTS buildTargets ('
        sQuery += '`id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,'
        sQuery += '`projectName` VARCHAR(255) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`projectPath` VARCHAR(255) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`buildTargetPath` VARCHAR(750) CHARACTER SET utf8 NOT NULL,'
        
        for sBuildType in self.lBuildTypes:

            sQuery += '`' + sBuildType + '` BOOL DEFAULT FALSE NOT NULL,'

        sQuery += '`ranking` INT UNSIGNED NOT NULL,'
        sQuery += '`depth` INT UNSIGNED NOT NULL,'
        sQuery += 'PRIMARY KEY(`id`));'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildTargets_projectName ON buildTargets (projectName) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildTargets_ranking ON buildTargets (ranking) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildTargets_depth ON buildTargets (depth) USING BTREE;'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: createBuildTargetsTable()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
                    warning('func: createBuildTargetsTable() statement failed to execute:', sQuery) 
                    warning('func: createBuildTargetsTable() Unexpected error:', e)
                    break        

    ###
    def dropBuildTargetsTable(self, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # drop buildTargets table
        sQuery = 'DROP TABLE IF EXISTS buildTargets;'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: dropBuildTargetsTable()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
                    warning('func: dropBuildTargetsTable() statement failed to execute:', sQuery) 
                    warning('func: dropBuildTargetsTable() Unexpected error:', e)
                    break    

    ###
    def createSourceTargetsTable(self, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # create buildTargets table 
        sQuery = 'CREATE TABLE IF NOT EXISTS sourceTargets ('
        sQuery += '`id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,'
        sQuery += '`projectName` VARCHAR(255) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`projectPath` VARCHAR(255) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`buildTargetPath` VARCHAR(750) CHARACTER SET utf8 NOT NULL,'
        
        for sBuildType in self.lSourceTypes:

            sQuery += '`' + sBuildType + '` BOOL DEFAULT FALSE NOT NULL,'

        sQuery += 'PRIMARY KEY(`id`));'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX sourceTargets_projectName ON sourceTargets (projectName) USING BTREE;'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: createSourceTargetsTable()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
                    warning('func: createSourceTargetsTable() statement failed to execute:', sQuery) 
                    warning('func: createSourceTargetsTable() Unexpected error:', e)
                    break        

    ###
    def dropSourceTargetsTable(self, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # drop buildTargets table
        sQuery = 'DROP TABLE IF EXISTS sourceTargets;'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: dropSourceTargetsTable()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
                    warning('func: dropSourceTargetsTable() statement failed to execute:', sQuery) 
                    warning('func: dropSourceTargetsTable() Unexpected error:', e)
                    break    

    ###
    def createBuildStatusTargetsTable(self, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # create buildStatusTargets table 
        sQuery = 'CREATE TABLE IF NOT EXISTS buildStatusTargets ('
        sQuery += '`id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,'
        sQuery += '`projectName` VARCHAR(255) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`projectPath` VARCHAR(255) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`buildTarPath` VARCHAR(750) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`buildTargetPath` VARCHAR(750) CHARACTER SET utf8 NOT NULL,'
        
        for sBuildType in self.lAllTypes:

            sQuery += '`' + sBuildType + '` BOOL DEFAULT FALSE NOT NULL,'

        sQuery += '`builder` VARCHAR(255) CHARACTER SET utf8,'
        sQuery += '`version` VARCHAR(255) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`os` VARCHAR(255) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`returnCode` INT UNSIGNED NOT NULL,'
        sQuery += 'PRIMARY KEY(`id`));'

        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildStatusTargets_projectName ON buildStatusTargets (projectName) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildStatusTargets_version ON buildStatusTargets (version) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildStatusTargets_os ON buildStatusTargets (os) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildStatusTargets_returnCode ON buildStatusTargets (returnCode) USING BTREE;'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: createBuildStatusTargetsTable()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
                    warning('func: createBuildStatusTargetsTable() statement failed to execute:', sQuery) 
                    warning('func: createBuildStatusTargetsTable() Unexpected error:', e)
                    break    

    ###
    def dropBuildStatusTargetsTable(self, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # delete buildStatusTargets table 
        sQuery = 'DROP TABLE IF EXISTS buildStatusTargets;'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: dropBuildStatusTargetsTable()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
                    warning('func: dropBuildStatusTargetsTable() statement failed to execute:', sQuery) 
                    warning('func: dropBuildStatusTargetsTable() Unexpected error:', e)
                    break

    ###
    def createViews(self,bDebug=False):

        # creates multi-table view between projects table and buildStatus table

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # project related views

        lQueries.append('CREATE OR REPLACE VIEW cProjects AS SELECT * FROM projects WHERE c > 0 OR cpp > 0;')
        lQueries.append('CREATE OR REPLACE VIEW cProjectsWithNoBuildTargets AS SELECT t1.projectName AS projectName FROM cProjects t1 LEFT JOIN buildTargets t2 ON t1.projectName = t2.projectName WHERE t2.projectName IS NULL;')

        # target related views

        lQueries.append('CREATE OR REPLACE VIEW numTargetsPerProject AS SELECT projectName, COUNT(*) AS numTargets FROM buildTargets GROUP BY projectName;')
        lQueries.append('CREATE OR REPLACE VIEW buildMinDepth AS SELECT projectName, MIN(depth) AS minDepth FROM buildTargets GROUP BY projectName;')
        lQueries.append('CREATE OR REPLACE VIEW buildTopTargets AS SELECT full_t.* FROM buildTargets full_t INNER JOIN buildMinDepth min_t USING (projectName) WHERE full_t.depth = min_t.minDepth; ')

        # buildStatus / buildStatusTargets related views

        lQueries.append('CREATE OR REPLACE VIEW builtWith_ubuntu14 AS SELECT projectName FROM buildStatus WHERE os=\'ubuntu14\';')
        lQueries.append('CREATE OR REPLACE VIEW builtWith_ubuntu12 AS SELECT projectName FROM buildStatus WHERE os=\'ubuntu12\';')
        lQueries.append('CREATE OR REPLACE VIEW builtWith_fedora20 AS SELECT projectName FROM buildStatus WHERE os=\'fedora20\';')
        lQueries.append('CREATE OR REPLACE VIEW builtWith_fedora21 AS SELECT projectName FROM buildStatus WHERE os=\'fedora21\';')

        sQuery = 'CREATE OR REPLACE VIEW buildStatusWithSite AS '
        sQuery += 'SELECT '
        sQuery += 't1.*,'
        sQuery += 't2.site AS site FROM '
        sQuery += 'buildStatus t1 INNER JOIN projects t2 USING (projectName);'
        lQueries.append(sQuery)

        lQueries.append('CREATE OR REPLACE VIEW buildSuccess AS SELECT * from buildStatusWithSite WHERE returnCode = 0;') 
        lQueries.append('CREATE OR REPLACE VIEW buildPartial AS SELECT * from buildStatusWithSite WHERE returnCode <> 0 AND numObjectsGenerated > 0;')
        lQueries.append('CREATE OR REPLACE VIEW buildFail AS SELECT * from buildStatusWithSite WHERE returnCode <> 0 AND numObjectsGenerated = 0;')
        lQueries.append('CREATE OR REPLACE VIEW unBuiltProjects AS (SELECT t_all.* FROM projects t_all LEFT JOIN buildStatus t_built USING (projectName) WHERE t_built.projectName IS NULL);')
        lQueries.append('CREATE OR REPLACE VIEW unBuiltCProjects AS SELECT * FROM unBuiltProjects WHERE c > 0 OR cpp > 0;')
        lQueries.append('CREATE OR REPLACE VIEW unBuiltTargets AS (SELECT t_all.* FROM buildTopTargets t_all LEFT JOIN buildStatus t_built USING (projectName) WHERE t_built.projectName IS NULL);')
        lQueries.append('CREATE OR REPLACE VIEW availableProjects AS (SELECT t_all.* FROM projects t_all LEFT JOIN buildSuccess t_success USING (projectName) WHERE t_success.projectName IS NULL);')
        lQueries.append('CREATE OR REPLACE VIEW availableCProjects AS SELECT * FROM availableProjects WHERE c > 0 OR cpp > 0;')
        lQueries.append('CREATE OR REPLACE VIEW availableTargets AS (SELECT t_all.* FROM buildTopTargets t_all LEFT JOIN buildSuccess t_success USING (projectName) WHERE t_success.projectName IS NULL);')

        lQueries.append('CREATE OR REPLACE VIEW availableTargetsWithSite AS SELECT t1.*,t2.site AS site FROM availableTargets t1 INNER JOIN projects t2 USING (projectName);')
        lQueries.append('CREATE OR REPLACE VIEW unBuiltTargetsWithSite AS SELECT t1.*,t2.site AS site FROM unBuiltTargets t1 INNER JOIN projects t2 USING (projectName);')

        sQuery = 'CREATE OR REPLACE VIEW buildSummaryByOS AS '
        sQuery += '(SELECT COUNT(DISTINCT(projectName)) AS projectCount,os, "successes" AS builds from buildSuccess GROUP BY os) UNION '
        sQuery += '(SELECT COUNT(DISTINCT(projectName)) AS projectCount,os, "partials" AS builds from buildPartial GROUP BY os) UNION '
        sQuery += '(SELECT COUNT(DISTINCT(projectName)) AS projectCount,os, "fails" AS builds from buildFail GROUP BY os) UNION '
        sQuery += '(SELECT COUNT(DISTINCT(projectName)) AS projectCount,os, "totals" AS builds from buildStatus GROUP BY os);'
        lQueries.append(sQuery)

        sQuery = 'CREATE OR REPLACE VIEW buildSummaryBySite AS '
        sQuery += '(SELECT COUNT(DISTINCT(projectName)) AS projectCount,site, "successes" AS builds from buildSuccess GROUP BY site) UNION '
        sQuery += '(SELECT COUNT(DISTINCT(projectName)) AS projectCount,site, "partials" AS builds from buildPartial GROUP BY site) UNION '
        sQuery += '(SELECT COUNT(DISTINCT(projectName)) AS projectCount,site, "fails" AS builds from buildFail GROUP BY site) UNION '
        sQuery += '(SELECT COUNT(DISTINCT(projectName)) AS projectCount,site, "totals" AS builds from buildStatusWithSite GROUP BY site);'
        lQueries.append(sQuery)

        sQuery = 'CREATE OR REPLACE VIEW buildSummaryBySiteOS AS '
        sQuery += '(SELECT COUNT(DISTINCT(projectName)) AS projectCount,site,os, "successes" AS builds from buildSuccess GROUP BY site,os) UNION '
        sQuery += '(SELECT COUNT(DISTINCT(projectName)) AS projectCount,site,os, "partials" AS builds from buildPartial GROUP BY site,os) UNION '
        sQuery += '(SELECT COUNT(DISTINCT(projectName)) AS projectCount,site,os, "fails" AS builds from buildFail GROUP BY site,os) UNION '
        sQuery += '(SELECT COUNT(DISTINCT(projectName)) AS projectCount,site,os, "totals" AS builds from buildStatusWithSite GROUP BY site,os);'
        lQueries.append(sQuery)

        lQueries.append('CREATE OR REPLACE VIEW buildSummaryFailIntersection AS SELECT projectName FROM buildSuccess UNION SELECT projectName FROM buildPartial;')

        sQuery = 'CREATE OR REPLACE VIEW buildSummary AS '
        sQuery += '(SELECT COUNT(DISTINCT projectName) AS projectCount, "successes" AS builds FROM buildSuccess) UNION '
        sQuery += '(SELECT COUNT(DISTINCT projectName) AS projectCount, "partials" AS builds FROM buildPartial AS t1 LEFT JOIN buildSuccess AS t2 USING (projectName) WHERE t2.projectName IS NULL) UNION '
        sQuery += '('
        sQuery += 'SELECT COUNT(DISTINCT t1.projectName) AS projectCount, "fails" AS build FROM '
        sQuery += 'buildFail AS t1 '
        sQuery += 'LEFT JOIN buildSummaryFailIntersection AS t2 USING (projectName) '
        sQuery += 'WHERE t2.projectName IS NULL) UNION '
        sQuery += '(SELECT COUNT(DISTINCT projectName), "totals" AS builds FROM buildStatus);'
        lQueries.append(sQuery)

        sQuery = 'CREATE OR REPLACE VIEW buildStatusWithTargets AS '
        sQuery += 'SELECT t1.projectName AS projectName,'
        sQuery += 't1.projectPath AS projectPath,'
        sQuery += 't1.buildTarPath AS buildTarPath,'
        sQuery += 't1.buildTime AS buildTime,'
        sQuery += 't1.version AS version,'
        sQuery += 't1.os AS os,'
        sQuery += 't1.numObjectsPreBuild AS numObjectsPreBuild,'
        sQuery += 't1.numObjectsPostBuild AS numObjectsPostBuild,'
        sQuery += 't1.numObjectsGenerated AS numObjectsGenerated,'
        sQuery += 't1.numSources AS numSources,'
        sQuery += 't2.buildTargetPath AS buildTargetPath,'
        sQuery += 't2.configureBuildType AS configureBuildType,'
        sQuery += 't2.configureacBuildType AS configureacBuildType,'
        sQuery += 't2.configureinBuildType AS configureinBuildType,'
        sQuery += 't2.cmakeBuildType AS cmakeBuildType,'
        sQuery += 't2.makefileBuildType AS makefileBuildType,'
        sQuery += 't2.antBuildType AS antBuildType,'
        sQuery += 't2.mavenBuildType AS mavenBuildType,'
        sQuery += 't2.returnCode AS returnCode '
        sQuery += 'FROM buildStatus AS t1 INNER JOIN buildStatusTargets AS t2 USING (projectName,buildTarPath) ORDER BY t1.projectName;'
        lQueries.append(sQuery)

        lQueries.append('CREATE OR REPLACE VIEW unknownCProjects AS SELECT t1.projectName FROM unBuiltCProjects t1 LEFT JOIN sourceTargets t2 USING (projectName) WHERE t2.projectName is NULL;')
        lQueries.append('CREATE OR REPLACE VIEW unBuiltSourceTargets AS (SELECT t_all.* FROM sourceTargets t_all LEFT JOIN buildStatus t_built USING (projectName) WHERE t_built.projectName IS NULL);')
        lQueries.append('CREATE OR REPLACE VIEW availableSourceTargets AS (SELECT t_all.* FROM sourceTargets t_all LEFT JOIN buildSuccess t_success USING (projectName) WHERE t_success.projectName IS NULL);')
        lQueries.append('CREATE OR REPLACE VIEW availableSourceTargetsWithSite AS SELECT t1.*,t2.site AS site FROM availableSourceTargets t1 INNER JOIN projects t2 USING (projectName);')
        lQueries.append('CREATE OR REPLACE VIEW unBuiltSourceTargetsWithSite AS SELECT t1.*,t2.site AS site FROM unBuiltSourceTargets t1 INNER JOIN projects t2 USING (projectName);')

        # buildStatus & project related views

        sQuery = 'CREATE OR REPLACE VIEW successfulCProjects AS '
        sQuery += 'SELECT COUNT(t2.projectName) AS successes, t2.site AS site FROM '
        sQuery += 'buildSuccess t1 INNER JOIN cProjects t2 USING (projectName) GROUP BY t2.site;'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: createViews()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
            
                    warning('func: createViews() statement failed to execute:', sQuery) 
                    warning('func: createViews() Unexpected error:', e)
                    break

    ###
    def deleteViews(self,bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # delete views associated with projects, buildTargets, buildStatus and buildStatusTargets

        lQueries.append('DROP VIEW IF EXISTS unknownCProjects;')
        lQueries.append('DROP VIEW IF EXISTS availableSourceTargetsWithSite;')
        lQueries.append('DROP VIEW IF EXISTS unBuiltSourceTargetsWithSite;')
        lQueries.append('DROP VIEW IF EXISTS availableSourceTargets;')
        lQueries.append('DROP VIEW IF EXISTS unBuiltSourceTargets;')

        lQueries.append('DROP VIEW IF EXISTS availableCProjects;')
        lQueries.append('DROP VIEW IF EXISTS unBuiltCProjects;')        
        lQueries.append('DROP VIEW IF EXISTS unBuiltProjects;')
        lQueries.append('DROP VIEW IF EXISTS availableProjects;')
        lQueries.append('DROP VIEW IF EXISTS successfulCProjects;')
        lQueries.append('DROP VIEW IF EXISTS cProjectsWithNoBuildTargets;')
        lQueries.append('DROP VIEW IF EXISTS cProjects;')

        lQueries.append('DROP VIEW IF EXISTS availableTargetsWithSite;')
        lQueries.append('DROP VIEW IF EXISTS unBuiltTargetsWithSite;')
        lQueries.append('DROP VIEW IF EXISTS availableTargets;')
        lQueries.append('DROP VIEW IF EXISTS unBuiltTargets;')
        lQueries.append('DROP VIEW IF EXISTS numTargetsPerProject;')
        lQueries.append('DROP VIEW IF EXISTS buildTopTargets;')
        lQueries.append('DROP VIEW IF EXISTS buildMinDepth;')
        
        lQueries.append('DROP VIEW IF EXISTS builtWith_ubuntu14;')
        lQueries.append('DROP VIEW IF EXISTS builtWith_ubuntu12;')
        lQueries.append('DROP VIEW IF EXISTS builtWith_fedora20;')
        lQueries.append('DROP VIEW IF EXISTS builtWith_fedora21;')
        lQueries.append('DROP VIEW IF EXISTS buildSummaryByOS;')
        lQueries.append('DROP VIEW IF EXISTS buildSummaryBySite;')
        lQueries.append('DROP VIEW IF EXISTS buildSummaryBySiteOS')
        lQueries.append('DROP VIEW IF EXISTS buildSummaryFailIntersection;')
        lQueries.append('DROP VIEW IF EXISTS buildSummary;')
        lQueries.append('DROP VIEW IF EXISTS buildSuccess;')
        lQueries.append('DROP VIEW IF EXISTS buildPartial;')
        lQueries.append('DROP VIEW IF EXISTS buildFail;')
        lQueries.append('DROP VIEW IF EXISTS buildStatusWithTargets;')
        lQueries.append('DROP VIEW IF EXISTS buildStatusWithSite;')

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: dropBuildStatusTable()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
                    warning('func: dropBuildStatusTable() statement failed to execute:', sQuery) 
                    warning('func: dropBuildStatusTable() Unexpected error:', e)
                    break    


    ###
    def createBuildStatusTable(self, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # create buildStatus table 
        sQuery = 'CREATE TABLE IF NOT EXISTS buildStatus ('
        sQuery += '`id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,'
        sQuery += '`projectName` VARCHAR(255) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`projectPath` VARCHAR(255) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`buildTarPath` VARCHAR(750) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`builder` VARCHAR(255) CHARACTER SET utf8,'
        sQuery += '`buildTime` INT UNSIGNED NOT NULL,'
        sQuery += '`version` VARCHAR(255) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`os` VARCHAR(255) CHARACTER SET utf8 NOT NULL,'
        sQuery += '`numObjectsPreBuild` INT UNSIGNED NOT NULL,'
        sQuery += '`numObjectsPostBuild` INT UNSIGNED NOT NULL,'
        sQuery += '`numObjectsGenerated` INT UNSIGNED NOT NULL,'
        sQuery += '`numSources` INT UNSIGNED NOT NULL,'
        sQuery += '`returnCode` INT UNSIGNED NOT NULL,'
        sQuery += 'PRIMARY KEY(`id`));'

        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildStatus_projectName ON buildStatus (projectName) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildStatus_version ON buildStatus (version) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildStatus_os ON buildStatus (os) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildStatus_numObjectsPreBuild ON buildStatus (numObjectsPreBuild) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildStatus_numObjectsPostBuild ON buildStatus (numObjectsPostBuild) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildStatus_numObjectsGenerated ON buildStatus (numObjectsGenerated) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildStatus_numSources ON buildStatus (numSources) USING BTREE;'
        lQueries.append(sQuery)

        sQuery = 'CREATE INDEX buildStatus_returnCode ON buildStatus (returnCode) USING BTREE;'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: createBuildStatusTable()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
                    warning('func: createBuildStatusTable() statement failed to execute:', sQuery) 
                    warning('func: createBuildStatusTable() Unexpected error:', e)
                    break    

    ###
    def dropBuildStatusTable(self, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # delete buildStatus table
        sQuery = 'DROP TABLE IF EXISTS buildStatus;'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: dropBuildStatusTable()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
                    warning('func: dropBuildStatusTable() statement failed to execute:', sQuery) 
                    warning('func: dropBuildStatusTable() Unexpected error:', e)
                    break    

    ###
    def truncate(self, bDebug=False):

        # expects initialize has been called and dbs/tables pre-exist

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # truncate projects table
        sQuery = 'TRUNCATE TABLE projects;'
        lQueries.append(sQuery)

        # truncate buildTargets table 
        sQuery = 'TRUNCATE TABLE buildTargets;' 
        lQueries.append(sQuery)

        # truncate sourceTargets table 
        sQuery = 'TRUNCATE TABLE sourceTargets;' 
        lQueries.append(sQuery)

        # truncate buildStatus table 
        sQuery = 'TRUNCATE TABLE buildStatus;' 
        lQueries.append(sQuery)

        # truncate buildStatusTargets table
        sQuery = 'TRUNCATE TABLE buildStatusTargets;'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: truncDB()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
            
                    warning('func: truncDB() statement failed to execute:', sQuery) 
                    warning('func: truncDB() Unexpected error:', e)
                    break

    ###
    def flush(self, sTable, bDebug=False):

        # expects a initDB has been called and dbs/tables pre-exist

        if sTable not in self.lTables:

            warning('func: flush() warning unknown table:', sTable)
            return 

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # create projects table
        sQuery = 'TRUNCATE TABLE ' + sTable + ';'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:
                
                try:

                    if bDebug: debug('func: flush()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
            
                    warning('func: flush() statement failed to execute:', sQuery) 
                    warning('func: flush() Unexpected error:', e)
                    break

    ###
    def open(self, bSetSchema=True):
        debug('####', self.port)
        debug('####', self.loc)
        debug('####', self.db)
        debug('####', self.user)
        try:

            if not self.conn or not self.conn.open:

                if bSetSchema:

                    self.conn = MySQLdb.connect(host=self.loc,port=self.port,user=self.user,passwd=self.passwd,db=self.db,charset='utf8',use_unicode=True)

                else:

                    self.conn = MySQLdb.connect(host=self.loc,port=self.port,user=self.user,passwd=self.passwd,charset='utf8',use_unicode=True)

        except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:

            warning('func: open() connection failed') 
            warning('func: open() Unexpected error:', e)

    ###
    def close(self):
    
        if self.ready():

            self.conn.close()

    ###
    def insertIntoProjects(self, lProjects, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        lArgs = ['bytecode_available', 'source', 'c', 'cpp', 'csharp', 'java']

        for dProject in lProjects:

            if '_source' in dProject:

                dSource = dProject['_source']

                if bDebug: debug( 'func: insertIntoProjects()', json.dumps(dSource, indent=4) ) 

                sQuery = 'INSERT INTO projects ('

                for sArg in lArgs:

                    sQuery += sArg + ','

                sQuery += 'codeDir,site,projectName) VALUES ('

                for sArg in lArgs:

                    if sArg in dSource:

                        sQuery += '\'%s\',' % MySQLdb.escape_string( str( int( dSource[sArg] ) ) )

                    else:

                        sQuery += '\'0\','

                for sArg in ['codeDir','site']:

                    if sArg in dSource and dSource[sArg]:

                        sQuery += '\'%s\',' % MySQLdb.escape_string( dSource[sArg] )

                    else:

                        sQuery += 'NULL,'

                sQuery += '\'%s\');' % MySQLdb.escape_string( dSource['name'] )

                lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:

                try:

                    if bDebug: debug('func: insertIntoProjects()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (UnicodeEncodeError, MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
            
                    warning('func: insertIntoProjects() statement failed to execute:', sQuery) 
                    warning('func: insertIntoProjects() Unexpected error:', e)
                    break

    ###
    def insertIntoBuildTargets(self, lTargets, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        for dArgs in lTargets:

            # verify required arguments are all included
            lArgNames = dArgs.keys()

            lRequiredArgs = self.dTables['buildTargets']['cols']

            bMissingArg = False
            lMissingArgs = []

            for sRequiredArg in lRequiredArgs:

                if sRequiredArg not in lArgNames:

                    bMissingArg = True
                    lMissingArgs.append(sRequiredArg)

            if bMissingArg:

                warning('func: insertIntoBuildTargets() missing required arguments:', lMissingArgs) 

            else:

                # sProjectName, sProjectPath, sBuildTargetPath, bConfigureBuildType=False, bConfigureacBuildType=False, bConfigureinBuildType=False, bCmakeBuildType=False, bMakefileBuildType=False, bAntBuildType=False, bMavenBuildType=False, iDepth=0, 

                sQuery = 'INSERT INTO buildTargets ('
                sQuery += 'projectName,'
                sQuery += 'projectPath,'
                sQuery += 'buildTargetPath,'

                for sBuildType in self.lBuildTypes:

                    sQuery += sBuildType + ','

                sQuery += 'ranking,'
                sQuery += 'depth) VALUES ('
                sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['projectName'] )
                sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['projectPath'] )
                sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['buildTargetPath'] )

                for sBuildType in self.lBuildTypes:

                    sQuery += '\'%s\',' % MySQLdb.escape_string( str( int(dArgs[sBuildType]) ) )

                sQuery += '\'%s\',' % MySQLdb.escape_string( str(dArgs['ranking']) )
                sQuery += '\'%s\');' % MySQLdb.escape_string( str(dArgs['depth']) )
                lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:

                try:

                    if bDebug: debug('func: insertIntoBuildTargets()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (UnicodeEncodeError, MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
            
                    warning('func: insertIntoBuildTargets() statement failed to execute:', sQuery) 
                    warning('func: insertIntoBuildTargets() Unexpected error:', e)
                    break

    ###
    def insertIntoSourceTargets(self, lTargets, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        for dArgs in lTargets:

            # verify required arguments are all included
            lArgNames = dArgs.keys()

            lRequiredArgs = self.dTables['sourceTargets']['cols']

            bMissingArg = False
            lMissingArgs = []

            for sRequiredArg in lRequiredArgs:

                if sRequiredArg not in lArgNames:

                    bMissingArg = True
                    lMissingArgs.append(sRequiredArg)

            if bMissingArg:

                warning('func: insertIntoBuildTargets() missing required arguments:', lMissingArgs) 

            else:

                # sProjectName, sProjectPath, sBuildTargetPath, bConfigureBuildType=False, bConfigureacBuildType=False, bConfigureinBuildType=False, bCmakeBuildType=False, bMakefileBuildType=False, bAntBuildType=False, bMavenBuildType=False, iDepth=0, 

                sQuery = 'INSERT INTO sourceTargets ('
                sQuery += 'projectName,'
                sQuery += 'projectPath,'
                sQuery += 'buildTargetPath,'
                sQuery += 'cBuildType,'
                sQuery += 'cppBuildType) VALUES ('
                sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['projectName'] )
                sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['projectPath'] )
                sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['buildTargetPath'] )
                sQuery += '\'%s\',' % MySQLdb.escape_string( str( int(dArgs['cBuildType']) ) )
                sQuery += '\'%s\')' % MySQLdb.escape_string( str( int(dArgs['cppBuildType']) ) )

                lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            for sQuery in lQueries:

                try:

                    if bDebug: debug('func: insertIntoSourceTargets()', sQuery) 

                    cursor.execute(sQuery)
                    self.conn.commit()
            
                except (UnicodeEncodeError, MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
            
                    warning('func: insertIntoSourceTargets() statement failed to execute:', sQuery) 
                    warning('func: insertIntoSourceTargets() Unexpected error:', e)
                    break

    ###
    #
    ###
    def verifyEncoding(self, sOriginal):

        sTransformed = ''

        try:

            sTransformed = sOriginal.encode('utf-8')
            #sTransformed = sOriginal.decode('utf-8')

        except (ValueError, UnicodeDecodeError, UnicodeEncodeError) as e:

            try:

                sTransformed = sOriginal.encode('latin-1')
                #sTransformed = sOriginal.decode('latin-1')

            except (ValueError, UnicodeDecodeError, UnicodeEncodeError) as e:

                try:

                    sTransformed = sOriginal.encode('utf-16')
                    #sTransformed = sOriginal.decode('utf-16')

                except (ValueError, UnicodeDecodeError, UnicodeEncodeError) as e:

                    warning('func verifyEncoding(): failed to transform sOriginal:', sOriginal, 'with utf-8, latin-1 and utf-16', e)
                    sTransformed = ''

        return sTransformed

    ###
    def insertIntoBuildStatusTargets(self, dArgs, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # verify required arguments are all included
        lArgNames = dArgs.keys()

        lRequiredArgs = self.dTables['buildStatusTargets']['colsNoBools'] + ['targets']
        lRequiredArgs.remove('buildTargetPath')
        lRequiredArgs.remove('builder')

        bMissingArg = False
        lMissingArgs = []

        for sRequiredArg in lRequiredArgs:

            if sRequiredArg not in lArgNames:

                bMissingArg = True
                lMissingArgs.append(sRequiredArg)

        if bMissingArg:

            warning('func: insertIntoBuildStatusTargets() missing required arguments:', lMissingArgs) 

        else:

            for dTarget in dArgs['targets']:

                sQuery = 'INSERT INTO buildStatusTargets ('
                sQuery += 'projectName,'
                sQuery += 'projectPath,'
                sQuery += 'buildTargetPath,'
                sQuery += 'buildTarPath,'
                sQuery += dTarget['buildType'] + ','
                sQuery += 'builder,'
                sQuery += 'version,'
                sQuery += 'os,'
                sQuery += 'returnCode) VALUES ('
                sQuery += '%s,' # projectName
                sQuery += '%s,' # projectPath
                sQuery += '%s,' # buildTargetPath
                sQuery += '%s,' # buildTarPath
                sQuery += '%s,' # dTarget['buildType']
                sQuery += '%s,' # builder
                sQuery += '%s,' # version
                sQuery += '%s,' # os
                sQuery += '%s);' # returnCode

                tArgs = (dArgs['projectName'], dArgs['projectPath'], self.verifyEncoding(dTarget['buildTargetPath']), dArgs['buildTarPath'], str( int(True) ), dArgs['builder'], dArgs['version'], dArgs['os'], str(dTarget['returnCode']))

                lQueries.append( (sQuery, tArgs) )


                # mysql escape_string doesn't handle unicode
                '''

                #sProjectName, sProjectPath, sBuildTargetPath, bConfigureBuildType=False, bConfigureacBuildType=False, bConfigureinBuildType=False, bCmakeBuildType=False, bAntBuildType=False, bMavenBuildType=False, sBuilder='', iBuildTime=0, sVersion="1.0", sOS='ubuntu14', iReturnCode=0, 

                sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['projectName'] )
                sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['projectPath'] )

                try:

                    sQuery += '\'%s\',' % MySQLdb.escape_string( self.verifyEncoding(dTarget['buildTargetPath']) )

                except (UnicodeEncodeError, UnicodeDecodeError) as e:

                    warning('func: insertIntoBuildStatusTargets() having trouble escaping buildTargetPath for builder: ', dArgs['builder'], 'for project:', dArgs['projectName'])
                    raise e

                sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['buildTarPath'] )
                sQuery += '\'%s\',' % MySQLdb.escape_string( str( int(True) ) )
                sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['builder'] )
                sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['version'] )
                sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['os'] )
                sQuery += '\'%s\');' % MySQLdb.escape_string( str(dTarget['returnCode']) )
                lQueries.append(sQuery)
                '''

            with closing( self.conn.cursor() ) as cursor:

                #execute mysql statements
                for sQuery in lQueries:

                    try:

                        if bDebug: debug('func: insertIntoBuildStatusTargets()', sQuery) 

                        if isinstance(sQuery, tuple):

                            (sQuery, tArgs) = sQuery
                            cursor.execute(sQuery, tArgs)

                        else:
                            
                            cursor.execute(sQuery)

                        self.conn.commit()
                
                    except (UnicodeEncodeError, MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
                
                        warning('func: insertIntoBuildStatusTargets() statement failed to execute:', sQuery) 
                        warning('func: insertIntoBuildStatusTargets() Unexpected error:', e)
                        warning('func: insertIntoBuildStatusTargets() for project:', )
                        break

    ###
    def insertIntoBuildStatus(self, dArgs, bDebug=False):

        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        # verify required arguments are all included
        lArgNames = dArgs.keys()

        lRequiredArgs = self.dTables['buildStatus']['cols']
        lRequiredArgs.remove('builder')

        bMissingArg = False
        lMissingArgs = []

        for sRequiredArg in lRequiredArgs:

            if sRequiredArg not in lArgNames:

                bMissingArg = True
                lMissingArgs.append(sRequiredArg)

        if bMissingArg:

            warning('func: insertIntoBuildStatus() missing required arguments:', lMissingArgs) 

        else:

            sQuery = 'INSERT INTO buildStatus ('
            sQuery += 'projectName,'
            sQuery += 'projectPath,'
            sQuery += 'buildTarPath,'
            sQuery += 'builder,'
            sQuery += 'buildTime,'
            sQuery += 'version,'
            sQuery += 'os,'
            sQuery += 'numObjectsPreBuild,'
            sQuery += 'numObjectsPostBuild,'
            sQuery += 'numObjectsGenerated,'
            sQuery += 'numSources,'
            sQuery += 'returnCode) VALUES ('

            sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['projectName'] )
            sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['projectPath'] )
            sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['buildTarPath'] )
            sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['builder'] )
            sQuery += '\'%s\',' % MySQLdb.escape_string( str(dArgs['buildTime']) )
            sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['version'] )
            sQuery += '\'%s\',' % MySQLdb.escape_string( dArgs['os'] )
            sQuery += '\'%s\',' % MySQLdb.escape_string( str(dArgs['numObjectsPreBuild']) )
            sQuery += '\'%s\',' % MySQLdb.escape_string( str(dArgs['numObjectsPostBuild']) )
            sQuery += '\'%s\',' % MySQLdb.escape_string( str(dArgs['numObjectsGenerated']) )            
            sQuery += '\'%s\',' % MySQLdb.escape_string( str(dArgs['numSources']) )
            sQuery += '\'%s\');' % MySQLdb.escape_string( str(dArgs['returnCode']) )
            lQueries.append(sQuery)

            with closing( self.conn.cursor() ) as cursor:

                #execute mysql statements
                for sQuery in lQueries:

                    try:

                        if bDebug: debug('func: insertIntoBuildStatus()', sQuery) 

                        cursor.execute(sQuery)
                        self.conn.commit()
                
                    except (UnicodeEncodeError, MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
                
                        warning('func: insertIntoBuildStatus() statement failed to execute:', sQuery) 
                        warning('func: insertIntoBuildStatus() Unexpected error:', e)
                        break

    ###
    def countRows(self, sTable, bDebug):

        iNumProjects = 0

        if sTable in self.lTables:

            lQueries = []

            if not self.ready(): self.open()
            else: lQueries.append('USE ' + self.db + ';')

            sQuery = 'SELECT COUNT(*) FROM ' + sTable + ';'
            lQueries.append(sQuery)

            with closing( self.conn.cursor() ) as cursor:

                #execute mysql statements
                try:

                    for sQuery in lQueries:

                        if bDebug: debug('func: countRows()', sQuery) 

                        cursor.execute(sQuery)

                    tTup = cursor.fetchone()

                    sNumProjects = ''

                    if tTup:

                        (sNumProjects,) = tTup

                    if sNumProjects:
          
                        iNumProjects = int( sNumProjects )
                
                except (ValueError, MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
            
                    warning('func: countRows() statement failed to execute:', sQuery) 
                    warning('func: countRows() Unexpected error:', e)


        else:

             warning('func: countRows() table provided sTable:', sTable)
             warning('func: countRows() valid values for sTable are:', self.lTables)

        return iNumProjects

    ###
    def findAllBuildTypeProjectsFromTable(self, sBuildType, sTable, bDebug=False):

        lProjects = []

        lTables = ['buildTargets','buildStatus']

        if sTable in lTables and sBuildType in self.lBuildTypes:

            lQueries = []

            if not self.ready(): self.open()
            else: lQueries.append('USE ' + self.db + ';')

            sQuery = 'SELECT projectName FROM ' + sTable + ' WHERE '
            sQuery += sBuildType + ' IS TRUE;'

            lQueries.append(sQuery)

            with closing( self.conn.cursor() ) as cursor:

                #execute mysql statements
                try:

                    for sQuery in lQueries:

                        if bDebug: debug('func: findAllBuildTypeProjectsFromTable()', sQuery) 

                        cursor.execute(sQuery)

                    for iCtr in range(cursor.rowcount):

                        (sProjectName,) = cursor.fetchone()
                        lProjects.append(sProjectName)
                
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
            
                    warning('func: findAllBuildTypeProjectsFromTable() statement failed to execute:', sQuery) 
                    warning('func: findAllBuildTypeProjectsFromTable() Unexpected error:', e)

        else:

             warning('func: findAllBuildTypeProjectsFromTable() invalid build type or table provided sBuildType:', sBuildType,'sTable:', sTable)
             warning('func: findAllBuildTypeProjectsFromTable() valid values for sBuiltType are:', self.lBuildTypes)
             warning('func: findAllBuildTypeProjectsFromTable() valid values for sTable are:', lTables)

        return lProjects

    ###
    def select(self, sSelectClause, sTable, sWhereClause='', sOrderByClause='', sLimitClause='', bDebug=False):

        lRows = []

        if sTable in (self.lTables + self.lViews):

            lQueries = []

            if not self.ready(): self.open()
            else: lQueries.append('USE ' + self.db + ';')

            if sSelectClause:
    
                sQuery = 'SELECT ' + sSelectClause + ' FROM ' + sTable

            else:

                warning('func: select() sSelectClause is not valid:', sSelectClause) 

            if sWhereClause:

                sQuery += ' WHERE ' + sWhereClause

            if sOrderByClause:

                sQuery += ' ORDER BY ' + sOrderByClause

            if sLimitClause:

                sQuery += ' LIMIT ' + sLimitClause

            sQuery += ';'

            lQueries.append(sQuery)

            with closing( self.conn.cursor() ) as cursor:

                #execute mysql statements
                try:

                    for sQuery in lQueries:

                        if bDebug: debug('func: select()', sQuery) 

                        cursor.execute(sQuery)

                    for iCtr in range(cursor.rowcount):

                        tRow = cursor.fetchone()
                        lRows.append(tRow)
                    
                except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
            
                    warning('func: select() statement failed to execute:', sQuery) 
                    warning('func: select() Unexpected error:', e)

        else:

             warning('func: select() table provided sTable:', sTable)
             warning('func: select() valid values for sTable are:', self.lTables + self.lViews)

        return lRows

    ###
    def findMultipleBuildTypeProjects(self, bDebug=False):

        lMultipleSameTypeProjects = []
        lMultipleBuildTypeProjects = []
        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        sQuery = 'SELECT projectName,'

        for sBuildType in self.lBuildTypes:

            sQuery += ' SUM(' + sBuildType + '), '

        sQuery = sQuery[:-2] + ' '

        sQuery += 'FROM buildTargets GROUP BY projectName;'

        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            try:

                for sQuery in lQueries:

                    if bDebug: debug('func: findMultipleBuildTypeProjects()', sQuery) 

                    cursor.execute(sQuery)

                for iCtr in range(cursor.rowcount):

                    dRow = {}
                    tTup = cursor.fetchone()

                    dRow['projectName'] = tTup[0]

                    iCtr = 0

                    for sBuildType in self.lBuildTypes:

                        iCtr += 1
                        dRow[sBuildType] = tTup[iCtr]

                    lBools = []

                    for sBuildType in self.lBuildTypes:

                        if dRow[sBuildType] > 0:

                            lBools.append(True)

                        else:

                            lBools.append(False)

                        if dRow[sBuildType] > 1:

                            dRow['multipleSameTypesFound'] = True

                    if sum(lBools) > 1:

                        dRow['multipleBuildTypesFound'] = True

                    if 'multipleSameTypesFound' in dRow:

                        lMultipleSameTypeProjects.append(dRow)

                    if 'multipleBuildTypesFound' in dRow:
    
                        lMultipleBuildTypeProjects.append(dRow)
            
            except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
        
                warning('func: findMultipleBuildTypeProjects() statement failed to execute:', sQuery) 
                warning('func: findMultipleBuildTypeProjects() Unexpected error:', e)

        return (lMultipleSameTypeProjects, lMultipleBuildTypeProjects)

    ###
    def getProjectBuildTargetsByDepth(self, sProjectName, bDebug=False):

        lRows = []
        lQueries = []

        if not self.ready(): self.open()
        else: lQueries.append('USE ' + self.db + ';')

        sQuery = 'SELECT projectName, projectPath, buildTargetPath, depth FROM buildTargets ORDER BY depth ASC;'
        lQueries.append(sQuery)

        with closing( self.conn.cursor() ) as cursor:

            #execute mysql statements
            try:

                for sQuery in lQueries:

                    if bDebug: debug('func: getProjectBuildTargetsByDepth()', sQuery) 

                    cursor.execute(sQuery)

                for iCtr in range(cursor.rowcount):

                    dRow = {}
                    (dRow['projectName'], dRow['projectPath'], dRow['buildTargetPath'], dRow['depth']) = cursor.fetchone()
                    lRows.append(dRow)
                
            except (MySQLdb.DataError, MySQLdb.IntegrityError, MySQLdb.InternalError, MySQLdb.NotSupportedError, MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
        
                warning('func: getProjectBuildTargetsByDepth() statement failed to execute:', sQuery) 
                warning('func: getProjectBuildTargetsByDepth() Unexpected error:', e)

        return lRows

    ###
    def getBuildSuccessAllBuildTypes(self):

        return None

    ###
    def getBuildSuccessByBuildType(self):

        return None

###
def depth(sPath, bDebug=False):

    return sPath.count(os.path.sep)

###
def usage():
    warning('Usage: projectDB.py --debug')

###
def main(argv):

    bError = False
    bDebug = False

    ### command line argument handling
    options, remainder = getopt.getopt(sys.argv[1:], 'c:f:d', ['corpus-dir-path=','forks=','debug'])

    # debug('func: main()', 'options:', options)
    # debug('func: main()', 'remainder:', remainder)

    for opt, arg in options:

        if opt in ('-d', '--debug'):

            bDebug = True

    if bError: usage()
    else:

        dMp = MuseProjectDB()

        sProjectName = 'f604b7a8-de6b-4996-b8ff-a3ef56f86378'
        sProjectPath = '/data/corpus/f/6/0/4/b/7/a/8/f604b7a8-de6b-4996-b8ff-a3ef56f86378'
        sBuildTargetPath = 'latest/libclastfm/configure.ac'

        dMp.initialize()
        #dMp.insertIntoProjects(lProjectNames=[sProjectName], bDebug=bDebug)

        dArgs = {}
        dArgs['projectName'] = sProjectName
        dArgs['projectPath'] = sProjectPath
        dArgs['buildTargetPath'] = sBuildTargetPath

        lBuildTypes = dMp.getBuildTypes()
        for sBuildType in lBuildTypes:

            dArgs[sBuildType] = False

        dArgs['configureacBuildType'] = True
        dArgs['depth'] = depth(sBuildTargetPath)

        dMp.insertIntoBuildTargets(lTargets=[dArgs], bDebug=bDebug)

        dArgs['depth'] = 1

        dMp.insertIntoBuildTargets(lTargets=[dArgs], bDebug=bDebug)

        dArgs['configureacBuildType'] = False
        dArgs['configureinBuildType'] = True

        dMp.insertIntoBuildTargets(lTargets=[dArgs], bDebug=bDebug)

        lRows = dMp.findMultipleBuildTypeProjects(bDebug=bDebug)

        for dRow in lRows:

            if bDebug: 

                debug('func: main() buildable project:', dRow)

                if 'multipleBuildTypesFound' in dRow: debug('func: main() multiple build-type project found:', dRow['projectName'])
                if 'multipleSameTypesFound' in dRow: debug('func: main() multiple same build-type project found:', dRow['projectName'])

        lRows = dMp.getProjectBuildTargetsByDepth(sProjectName, bDebug=bDebug)

        for dRow in lRows:

            if bDebug: debug('func: main() project:', sProjectName, 'buildable target sorted by depth:', dRow)

        dArgs = {}
        dArgs['projectName'] = sProjectName
        dArgs['projectPath'] = sProjectPath
        dArgs['buildTargetPath'] = sBuildTargetPath
        lBuildTypes = dMp.getBuildTypes()
        for sBuildType in lBuildTypes:

            dArgs[sBuildType] = False
        dArgs['configureacBuildType'] = True
        dArgs['builder'] = 'musebuilder-ubuntu12_0'
        dArgs['buildTime'] = 37
        dArgs['version'] = '1.0'
        dArgs['os'] = 'ubuntu12'
        dArgs['returnCode'] = 1

        dMp.insertIntoBuildStatus(dArgs=dArgs, bDebug=bDebug)

        #sProjectName = 'f36b4d21-de39-4106-80d8-91c790726d1e'
        #dMp.insertIntoProjects(lProjectNames=[sProjectName], bDebug=bDebug)

        nRows = dMp.countRows(sTable='projects', bDebug=bDebug)

        lProjects = dMp.findAllBuildTypeProjectsFromTable(sBuildType='configureacBuildType', sTable='buildTargets', bDebug=bDebug)

        for sProject in lProjects:

            if bDebug: debug('func: main() configureac projects found:', sProject)

        for sTable in dMp.getTables():

            lCols = dMp.getTableCols(sTable=sTable)

            if sTable != 'buildStatus':

                sCols = ','.join(lCols)
    
                lRows = dMp.select(sSelectClause=sCols, sTable=sTable, sWhereClause='', bDebug=bDebug)

                for tRow in lRows:
    
                    if bDebug: debug('func: main() tRow:', tRow)

            else:

                sCols = ','.join(lCols)

                lRows = dMp.select(sSelectClause=sCols, sTable=sTable, sWhereClause='returnCode = 1', bDebug=bDebug)

                for tRow in lRows:

                    if bDebug: debug('func: main() builds where returncode was 1:', tRow)

                    lCols = dMp.getTableCols(sTable=sTable)
                    
                    dRow = {}

                    iCtr = 0
                    for sCol in lCols:

                        dRow[sCol] = tRow[iCtr]
                        iCtr += 1

                    if bDebug: debug('func: main() builds where returncode was 1:', dRow)

        dMp.truncate()

        dMp.close()

###
if __name__ == "__main__":
    main(sys.argv[1:])
