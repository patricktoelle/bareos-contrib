This plugin uses the baseclass and implements a sender to Icinga2 using the REST API.
It needs the python-requests module from http://python-requests.org

Usage

In bareos-dir.conf enable director plugins and load the Python plugin:

    Director {
      Plugin Directory = /usr/lib64/bareos/plugins
      Plugin Names = "python"
      # ...
    }

In your JobDefs or Job Definition configure the plugin itself:

    Job {
      Name = "BackupClient1"
      DIR Plugin Options ="python:module_path=/usr/lib64/bareos/plugins:module_name=bareos-dir-icinga2-sender:apiAdress=your.icinga2.server:username=apiuser:password=apipassword:checkHost=bareos:checkService=bareos_job_client1"
      JobDefs = "DefaultJob"
    }

* monitorHost: IP or resolvable address of your Icinga 2 host
* checkHost: the host name for your check result
* checkService: the service name for your result
* username: Icinga2 Api username
* password: Icinga2 Api password
