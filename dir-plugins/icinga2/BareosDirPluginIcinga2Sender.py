#!/usr/bin/env python
# -*- coding: utf-8 -*-
# BAREOS - Backup Archiving REcovery Open Sourced
#
# Copyright (C) 2014-2014 Bareos GmbH & Co. KG
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of version three of the GNU Affero General Public
# License as published by the Free Software Foundation, which is
# listed in the file LICENSE.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# Author: Patrick Toelle <mail@patricktoelle.de>
#
# Icinga2Sender for Bareos python plugins
# Functions taken and adapted from bareos-dir-nsca-sender.py

from bareosdir import *
from bareos_dir_consts import *
import BareosDirPluginBaseclass
import requests
import json

class BareosDirPluginIcinga2Sender(BareosDirPluginBaseclass.BareosDirPluginBaseclass):
    ''' Bareos DIR python plugin Icinga 2 sender class '''

    def parse_plugin_definition(self, context, plugindef):
        '''
        Check, if mandatory monitoringHost is set and set default for other unset parameters
        '''
        super(BareosDirPluginIcinga2Sender, self).parse_plugin_definition(
            context, plugindef)
        # Icinga2 API Adress Host is mandatory
        if not 'monitorHost' in self.options:
            JobMessage(context, bJobMessageType['M_WARNING'], "Plugin %s needs parameter 'monitorHost' specified\n" %(self.__class__))
            self.monitorHost = ""
        else:
            self.monitorHost = self.options['monitorHost']
        # monitoring Host is mandatory
        if not 'username' in self.options:
            JobMessage(context, bJobMessageType['M_WARNING'], "Plugin %s needs parameter 'username' specified\n" %(self.__class__))
            self.username = ""
        else:
            self.username = self.options['username']
        # monitoring Host is mandatory
        if not 'password' in self.options:
            JobMessage(context, bJobMessageType['M_WARNING'], "Plugin %s needs parameter 'password' specified\n" %(self.__class__))
            self.password = ""
        else:
            self.password = self.options['password']
        if not 'checkHost' in self.options:
            self.checkHost = 'bareos'
        else:
            self.checkHost = self.options['checkHost']
        if not 'checkService' in self.options:
            self.checkService = 'backup_job'
        else:
            self.checkService = self.options['checkService']

        # we return OK in anyway, we do not want to produce Bareos errors just because of failing
        # Nagios notifications
        return bRCs['bRC_OK']

    def handle_plugin_event(self, context, event):
        '''
        This method is calle for every registered event
        '''

        # We first call the method from our superclass to get job attributes read
        super(BareosDirPluginIcinga2Sender, self).handle_plugin_event(context, event)

        if event == bDirEventType['bDirEventJobEnd']:
            # This event is called at the end of a job, here evaluate the results
            self.evaluateJobStatus (context)
            self.transmitResult (context)

        return bRCs['bRC_OK'];


    def evaluateJobStatus(self,context):
        '''
        Depending on the jobStatus we compute monitoring status and monitoring message
        You may overload this method to adjust messages
        '''
        self.nagiosMessage = "";
        coreMessage = "Bareos job %s on %s with id %d level %s, %d errors, %d jobBytes, %d files terminated with status %s" \
            %(self.jobName, self.jobClient, self.jobId, self.jobLevel, self.jobErrors, self.jobBytes, self.jobFiles, self.jobStatus)
        if (self.jobStatus == 'E' or self.jobStatus == 'f'):
            self.nagiosResult = 2; # critical
            self.nagiosMessage = "CRITICAL: %s" %coreMessage
        elif (self.jobStatus == 'W'):
            self.nagiosResult = 1; # warning
            self.nagiosMessage = "WARNING: %s" %coreMessage
        elif (self.jobStatus == 'A'):
            self.nagiosResult = 1; # warning
            self.nagiosMessage = "WARNING: %s CANCELED" %coreMessage
        elif (self.jobStatus == 'T'):
            self.nagiosResult = 0; # OK
            self.nagiosMessage = "OK: %s" %coreMessage
        else:
            self.nagiosResult = 3; # unknown
            self.nagiosMessage = "UNKNOWN: %s" %coreMessage

	# Performance data according Nagios developer guide
	self.perfdata = [
	  "Errors=%d;;;;" %(self.jobErrors),
	  "Bytes=%d;;;;" %(self.jobBytes),
	  "Files=%d;;;;" %(self.jobFiles),
	  "Throughput=%dB/s;;;;" %(self.throughput),
	  "jobRuntime=%ds;;;;" %(self.jobRunningTime),
	  "jobTotalTime=%ds;;;;" %(self.jobTotalTime)
	]

        DebugMessage(context, 100, "Nagios Code: %d, NagiosMessage: %s\n" %(self.nagiosResult,self.nagiosMessage));
        DebugMessage(context, 100, "Performance data: %s\n" %self.perfdata)


    def transmitResult(self,context):
        '''
        Here we send the result to the Icinga 2 server using the REST API
        Overload this method if you want ot submit your changes on a different way
        '''
        DebugMessage(context, 100, "Submitting check result to %s using username: %s \n" \
            %(self.monitorHost,self.username))
        try:
  	    url = "https://" + self.monitorHost + ":5665/v1/actions/process-check-result"
            params = { "service": self.checkHost + "!" + self.checkService }
            headers = { "Accept": "application/json" }
            postdata = { "exit_status": self.nagiosResult, "plugin_output": self.nagiosMessage, "performance_data": self.perfdata }

            DebugMessage(context, 100, "Data %s, URL %s, Username %s, Password %s, Params %s, Headers %s \n" %(postdata, url, self.username, self.password, params, headers))
            response = requests.post( url , auth=(self.username, self.password), json=postdata, verify=False, headers=headers, params=params )

        except:
	    pass
            DebugMessage(context, 100, response)
            JobMessage(context, bJobMessageType['M_WARNING'], "Plugin %s could not transmit check result to %s \n"\
                 %(self.__class__, self.monitorHost))

# vim: ts=4 tabstop=4 expandtab shiftwidth=4 softtabstop=4
