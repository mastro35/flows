# FLOWS


*Flows* is a workflow engine for Python(istas). 
With *flows* you will be able to create complex workflows based on the built-in actions and other custom actions that you will be able to create.

With *flows*, creating a custom action is as easy as subclassing a standard Python class and the building of a workflow is even simpler.


# Installation

*flows* can be build from sources or can be obtained from binary distribution.

## For Windows user

If you want to install flows on a Windows machine, please start installing the pypiwin32 package using:

```sh
c:\pip install pypiwin32
```

This is necessary due of a [problem on the pypiwin32 that the maintainer is not going to fix](https://sourceforge.net/p/pywin32/bugs/522/) (basically pypiwin32 doesn't support source builds on Python3 and doesn't have binary builds for Python 3.6. yet)

## Get *flows* from pypi

The raccomended method to get *flows* is by using pip and the [pypi repository](https://pypi.python.org/pypi).

$ pip install flows

Yes, it's so simple.

## Build *flows* from sources

To build *flows* from sources, just install all the requirements listed in requirements.txt by typing

```sh
$ pip install -r requirements.txt
```

Once the requirements have been installed, you can simply install *flows* by typing

```sh
$ python setup.py install
```


# Usage

To start a flow simply start a terminal and type

```sh
$ flows [-h] [-i MS] [-s SEC] [-v] [-V] FILENAME [FILENAME ...]
```

Note that you can start more flows with a single command and every single action contained in every flow will be able to communicate with each others.

Just using flows -h gives you the help of the command line interface.

>
>A workflow engine for Pythonistas  
>  
>positional arguments:  
>  FILENAME              name of the recipe file(s)  
>  
>optional arguments:  
>  -h, --help            show this help message and exit  
>  -i MS, --INTERVAL MS  perform a cycle each [MS] milliseconds. (default = 500)  
>  -s SEC, --STATS SEC   show stats each [SEC] seconds. (default = NO STATS)  
>  -v, --VERBOSE         enable verbose output  
>  -V, --VERSION         show program's version number and exit  

As you can see, if you need to have some statistics on how your workflow is running you can specify the -s option, and each [SEC] seconds you will get an onscreen message with some statistics informations. 

Beside, you can add verbosity to the output of the command just specifying the -v option.

Don't be afraid from the -i option, we will discuss it later. However, the standard usage of *flows* is just by specifing the name of the recipes files to start.


# "Actions": The flows' building blocks

To create your first flow you just need to know what kind of *actions* you can use, because a workflow is just a set of actions that are chained together and that works together to get something. This is why you should consider actions like "building blocks" that you can mix and match with other building blocks to create a workflow.

There are a lot of actions that are ready to use out of the box and here we will explain how they work. 

To make it more clear to the reader, we will talk about two different kind of actions: **input actions** and **work actions**. The former is a type of action that is executed when an event occurs, the latter is a type of action that is called by another action to do something specific.


## Input actions

Input actions don't usually need to listen to other actions, they are usually at the beginning of a flow and are the starters of the whole process.


### Alarm

The alarm action sends a message to listening actions at a specific time of a given date. 

To use this action, put this code in your flow file

```sh
[my_alarm_action_name]
type = alarm
date = 01/11/2035 18:25:06
```

In this example, the alarm will send a message at 6:25.06 pm on November the 1st, 2035.


### Cron

The cron lets you create a schedule to execute actions.

It works exactly like the cron string in a crontab file of a *nix OS. 

To use this action, put this code in your flow file

```sh
[my_cron_action_name]
# 
#					 .---------------- [m]inute: (0 - 59) 
#					 |  .------------- [h]our: (0 - 23)
#					 |  |  .---------- [d]ay of month: (1 - 31)
#					 |  |  |  .------- [mon]th: (1 - 12) or jan,feb,mar,apr... 
#					 |  |  |  |  .---- [w]eek day: (0 - 6) or sun,mon,tue,wed,thu,fri,sat
#					 |  |  |  |  |
# crontab_schedule = *  *  *  *  *
#
type = cron
crontab_schedule = 06 06 06 06 *
```

In this example, the action will send a message yearly at 06:06 am on June the 6th, regardless of the weekday.


### Readfile

The readfile action reads a text file one line at a time and sends a message that contains the read line to the listeners.

To use this action, put this code in your flow file

```sh
[my_read_file_action_name]
type = readfile
input = /home/user/path/to/filename
```


### Tail

The tail action is like the "tail -f" command on *nix OS. It sends the message to the listeners with all the new lines created on a text file by the time they are created. 
It is particularly useful when you are creating a flow to check a log file. 
In this last case you could consider to use the keyword "regex" so to be notified not when a new line arrives but when a bunch of new lines (an exception) arrive.  

To use this action, put this code in your flow file

```sh
[my_tail_action_name]
type = tail
input = /home/user/path/of/the/file/to/be/tailed
# regex_new_buffer = ^(ERROR|INFO|WARN|DEBUG)
```


### Timer

The timer action sends a message every N seconds. The number of the seconds can be set in the configuration of this action.

To use this action, put this code in your flow file

```sh
[my_timer_action_name]
type = timer
delay = 300
```

In this example, the timer will send a message every 5 minutes.


### Watchdog

A watchdog can monitor the filesystem for changes and send a message when something happen. 

To use this action, put this code in your flow file

```sh
[my_watchdog_action_name]
type = watchdog
input = /directory_to/be/monitored/
monitor = create
# the monitor parameter can be set to : create, move, delete, modify, any
option = recursive
#option = nonrecursive
patterns = *.*
# ignore_patterns = *.pdf *.ePS
# case_sensitive
# ignore_directory
```

In this example where are monitoring just the creation of new files under /directory_to/be/monitored/ and recursively under all its subdirectories regardless of the name of the file (\*.\*) .


## Work actions

Work actions are the actions that actually do the real work. They are usually set to listen input actions or other work actions because they can't start without input.


### Log

The log action can write a message on the standard output or on a text file.

After printing the message, this action also sends the message to other listening actions.

To use this action, put this code in your flow file

```sh
[my_log_action_name]
type = log
input = any_other_action
text = Hey, something has happened here! {date} - {time} : {event_type} {file_source}
# option = /path/to/the/filename/to/be/written
# option = null
# rolling
# maxBytes = 20000000
# backupCount = 5
```

In this example we are writing on the screen the string "Hey, something has happened here!" followed by the current system date, the current system time and the type of the event and the filename got by the watchdog action that we are listening to. 

Note that all the tokens in braces {} are actually "variables" resolved at runtime. 

Currently, the variables supported are:

* {date} : current date
* {time} : current time
* {input} : the message sent by the listened action



If the action is set to listen to a watchdog you can also use:

* {event_type} : this is the type of the filesystem event that has happened (creation, modification etc ... ) 
* {file_source} : the source of the file 
* {file_destination} : the destination of the file (for the "move" event)
* {is_directory} : true if the file_source is a directory, false elsewere


If you are redirecting the log to a file, consider the possibility to use the "rolling" keywork to create a rolling file of "maxBytes", with "backupCount" backup files.


### Mail

The mail action sends a mail to recipients when the listened action occurs.

To use this action, put this code in your flow file

```sh
type = mail
input = any_other_action
from = from_mail_address@domain.com
to = destination_mail_address@domain.com
subject = subject of the mail to be sent
body = body of the mail to be sent
smtp_server = address_of_the_smtp_server
smtp_port = 25
```

Note that in "subject" and "body" configuration you can use variables like in the "log" action.


### Pass_on_interval

The "pass_on_interval" action simply sends the input message received from the listened action to the listeners when it's running on a specific time of the day.

To use this action, put this code in your flow file

```sh
[my_pass_on_interval_action_name]
type = pass_on_interval
input = any_other_action
start_date = 01/11/1976
end_date = 28/12/2035
start_time = 08:00
end_time = 20:00
weekdays = 0
# weekdays = 0 2 3 4 5 6
# day = 1
# month = 1
```

In this example, the action sends the input message to the listeners only if the current date is between 1976 November the 1st and 2035 December the 28th, it's a monday and the time is between 8am and 8pm.


### Restart

The restart action stops all the current actions and restart the flow. It is useful just if you need to create a flow that restarts itself when the flow file is changed, so it is usually set to listen to a watchdog action that monitors the "." directory for changes.

To use this action, put this code in your flow file

```sh
[my_restart_action_name]
type = restart
input = any_other_action
```


### Substring

The substring action lets you substring an input string by cutting it or by choosing a field in a character delimited string. To use this action, put this code in your flow file

```sh
[my_substring_action_name]
type = substring
input = any_other_action
subtype = split
separator = ;
item = 1
# subtype = cuts
# from = 1
# to = 10
```


### Webserver

The webserver action starts a webserver that provides a Json dictionary of all latest values received from the listened actions. 

To use this action, put this code in your flow file

```sh
[my_webserver_action_name]
type = webserver
input = any_other_action
hostname = localhost
hostport = 3535
```

In this example to access the webserver you would need to visit http://localhost:3535


### Append_variable_by_time

This action allows you append a value depending on the time of the day to the message got in input. This is very useful for the check_if action if you want to choose dinamically the second operand of the check_if action depending of the time of the day.

To use this action, put this code in your flow file

```sh
[my_append_variable_by_time_action_name]
type = append_variable_by_time
input = any_other_action
00:00 = 0
08:00 = 10
12:00 = 20
18:00 = 80
separator = ";"
```

In this example, from 12:00 am to 08:00 am, to the input message will be appended the value ";0"


### Buffer

The buffer action is very useful when you are working with the tail action and you need to consider a multiline entry like a single entry. Since the tail action sends every single line as a different message you may consider to use a buffer action to collect all the lines and flush the buffer only when a specific regular expression matches.

To use this action, put this code in your flow file

```sh
[my_buffer_action_name]
type = buffer
input = any_other_action
regex_new_buffer = ^(ERROR|INFO|WARN|DEBUG)
```

In this example, the buffer is flushed only when you receive a line that starts with "ERROR", "INFO", "WARN" or "DEBUG". This is useful to parse a log file that handles multiline exception.


### Check_if

The check_if action sends the input message to the listeners only if a condition is met.

To use this action, put this code in your flow file

```sh
[my_check_if_action_name]
# Check if a condition is met
# operation = any of <, <=, >, >=, ==, !=, %% (true if remainder is 0)
# limit = N -> second operand of the check-if action. 
# If omitted the comparsion in made between the two operands 
#              received in input when the input is column separated (like 10;20)
type = check-if
input = any_other_action
operation = <
limit = 100
```

In this example, if the integer value of the input  is less then 100 the condition is met and the message is sent to listeners.


### Command

The command action executes a shell command and sends the results of the standard output to the listeners.

To use this action, put this code in your flow file

```sh
[my_command_action_name]
type = command
input = any_other_action
command = cp {file_source} /home/mastro35/myDestination
```

Note that in the "command" configuration you can use the variables of the log action.


### Count

The count action is just a counter that counts how many times the action is executed. In the default configuration the counter value is sent to the listeners after each hit, but if you specify a timeout you can notify listeners every N seconds on the status of the counter. The "partial" keyword, if specified, resets the counter when the message of the counter value is sent to listeners (so it's useful only if used with a timeout).

To use this action, put this code in your flow file

```sh
[my_count_action_name]
type = count
input = any_other_action
# timeout = 3
# partial
```


### Filter

The filter action sends the input received to listeners only if it matches any of the given regular expressions.

Specifying "invert" as subtype it sends the input to the listeners only if it don't match any of the given regular expressions.

To use this action, put this code in your flow file

```sh
type = filter
# subtype = invert
input = any_other_action
regex = /^ERROR
# regex_file = filename_containing_regexs
```

If you need to match just one regular expression you can put it on the configuration like in this example, but if you need to match more regular expressions you can use a regex_file (that is a normal plain text file containing all the regexes to be matched)


### Get_url

The get_url action visits a web address and returns a string like HTTP_CODE;HTTP_STATUS_DESCRIPTION;HTML

To use this action, put this code in your flow file

```sh
[my_get_url_action_name]
type = get_url
input = any_other_action
url = url_to_get
```


### Check url for 200
The check_url_for_200 action visit a web address and returns the status code of the request when it is equal to 200.
If the "invert" keywork is specified, it returns the status code when it is NOT equal to 200.

```sh
[my_check_url_for_200_action]
type = check_url_for_200
input = any_other_action
url = url_to_get
invert
```


### Hash

This action creates a md5 hash of the input received and sends it to listeners.

To use this action, put this code in your flow file

```sh
[my_hash_action_name]
type = hash
input = any_other_action
```


### AdoDBAction

This action use the adodbapi module to execute query against a database.

To use this action, put this code in your flow file

```sh
[my_sqlserver_query_action]
type = adodb
input = any_other_action
connstring = Provider=SQLNCLI11;Server=srv-mydbInstance;Database=myDB;Uid=Marilyn;Pwd=superstar;
separator = ;
query = SELECT avg(duration) as duration, count(*) as number from entry where data < getdate() 
```

The results are sent one at a time to the listeners.


# Some example

Here you will find just a couple of example to whet your appetite :)

The first one checks every 5 minutes if a website is online and if it's not sends a mail to a specific recipient.

```
# FLOWS

[check_the_time]
type = cron
input = None
crontab_schedule = */5 * * * *

[connection_to_my_website]
type = get_url
input = check_the_time
url = http://mastro35.tumblr.com/

[get_status]
type = substring
input = connection_to_my_website
subtype = split
separator = ;
item = 1

[check_status]
type = check_if
input = get_status
operation = !=
limit = 200

[send_error_by_mail]
type = mail
input = check_status
from = alert@mastro35.com
to = dave35@mastro35.com
subject = Site is down!
body = {input}
smtp_server = mail.mysmtpserver.com
smtp_port = 25

```



The second one checks how many files are created in a given directory every 5 minutes and if the number is greater than 100 prints a message to the standard output.

```
# FLOWS

[my_fileserver]
type = watchdog
input = \\myfolder
monitor = create
option = recursive
patterns = *.*

[count_new_files]
type = count
input = my_fileserver
timeout = 300
partial

[check_number_of_new_files]
type = check_if
input = count_new_files
operation = >
limit = 100

[log_for_too_many_files]
type = log
input = check_number_of_new_files
text =  {date} - {time} : Too much files created in the last 5 minutes ({input}) !

```


# How to create custom actions

Creating custom actions is really easy. All you have to do is to subclass the Action class and put the file you are creating under the "\Actions" subdirectory.

To make it simpler, in the Actions subdirectory you can find a file called GenericCustomAction.py that contains a custom action created for you as an example.

```python
#!/usr/bin/env python

'''
GenericCustomAction.py
----------------------

Copyright 2016 Davide Mastromatteo
License: Apache-2.0
'''

import logging
from flows.Actions.Action import Action

LOGGER = logging.getLogger(__name__)


class GenericCustomAction(Action):
    """
    GenericCustomAction Class
    """

    type = "generic"

    def on_init(self):
        super().on_init()
        # if needed, execute initializazion code HERE

    def on_stop(self):
        # if needed, execute finalization code HERE
        return super().on_stop()

    def on_cycle(self):
        super().on_cycle()
        # if needed, execute code to be executed each cycle HERE

    def on_input_received(self, action_input=None):
        super().on_input_received(action_input)

        # if needed, execute code to handle input received HERE, doing something clever ...
        # - like reverting the input string?
        to_return = action_input.message[::-1]

        # and - if needed - message other actions with the result of your operation
        self.send_message(to_return)
```

As you can see from the example above, all you have to do is to subclass the Action class, define a type name and set it in the "type" class variable and to override four methods. 

The methods that need to be overridden are: 

* on\_init(self) - called when the action is instanciated when you start the flow. It's basically the constructor method of the action.
* on\_stop(self) - called when the action is going to be destroyed, at the end of the execution
* on\_cycle(self) - called on each cycle of the program. This is very important because this **IS** the life cycle of your action. **DO NOT** create your own cycle in the on_init(self) method or do anything stupid, keep it simple! Do you need a cycle inside your action? There's a method for that! (cit) :)
Note that by default this method is called every 500 milliseconds. If you want to make the cycle sleep shorter or longer, you can specify the -i parameter on the command line.
* on\_input\_received(self) - called when your action receive a message from another listened action. If you need to elaborate an input that comes from another action, this is the right place.
It's important to note that you can't estimate when the on\_input\_received will be called because it depends on when the message from the action you have subscribed will arrive. Beside, if the messages are queueing up, the engine will throttle to handle the queue as fast as possible, so bear in mind it.

A very important thing is the naming convention: *flows* will load all the actions it will find in *Action.py python modules under the *\flows\Action directory you will find after the installation on your current python site_packages directory. 
So, I encourage you to call your custom actions like:
* "[Something]Action.py" if it's a work action
* "Input[Something]Action.py" if it's an input action.

Note that the input message can be accessed using the action_input.message and that to send messages to listeners you need to use 

```python
self.send_message("message to be sent to listeners")
```

You can add all the configuration needed by your action within the action configuration in the flow recipe file and your action will be able to access these values using the dictionary pointed by the self.configuration variable. So, for example, if you need a parameter named "myparameter" in your SomethingAction, you can add it to your recipe and in your action you will be able to access it by using

```python
self.configuration["myparameter"]
```

# How to contribute 

This software is free, so your contribution is very precious.

You can contribute in several ways: helping me in the development of the software, spotting and fixing bugs or simply talking about it on social networks using the tag #flowsiscool :) ... but if you really like it, please consider to offer me a Starbucks' "tall pike" by using paypal at http://paypal.me/mastro35  ; because I code better when I'm high on Starbucks' drinks :)
