# angry_debugger
Debugging routine that tracks a data path through a program. It is written for Python 2.7+, 3.5+

OK so this is the skinny on how this works.

log_it is if the main entry point. It logs the data path through a program.

it provides output that looks like this

    2019-12-07 17:36:45,229 - [ANGRY] Thread-5[14016]
                              src: __main__.SomeClass.property_test_1 [C:/Users/Administrator/Documents/GitHub/angry_debugger/angry_debugger/__init__.py:783]
                              dst: __main__.SomeClass.property_test_4 (getter) [C:/Users/Administrator/Documents/GitHub/angry_debugger/angry_debugger/__init__.py:838]
                              function called: __main__.SomeClass.property_test_4()
                              duration: 0.5148007869720459 sec
                              __main__.SomeClass.property_test_4 => 'This is the property_test_4 getter'

    2019-12-07 17:36:45,073 - [ANGRY] Thread-4[14292]
                              src: __main__.do [C:/Users/Administrator/Documents/GitHub/angry_debugger/angry_debugger/__init__.py:889]
                              dst: __main__.SomeClass.method_test_1 [C:/Users/Administrator/Documents/GitHub/angry_debugger/angry_debugger/__init__.py:859]
                              function called: __main__.SomeClass.method_test_1(arg='argument 1')
                              duration: 358.80041122436523 ms
                              __main__.SomeClass.method_test_1 => None


the layout of a log entry is as follows.

    {date} {time},{fractions of a second} - [{log level}] {thread name}[{thread id}]
                                            src: {call origin} [{file}:{line number}]
                                            dst: {call destinaion} [{file}:{line number}]
                                            function called: {call destination}({arguments passed if any including defaults})
                                            duration: {length of time the call took}
                                            {call destination} => {return value}

log_it can be used as a decorator for functions, methods and properties. It can also be used as a callable for
class attributes.

    @log_it
    def some_method_or_function():
        pass

if used on properties you have to place it before the property decorator. it is a selective decoration,
what that meas is if you want to log only the setter portion you can do that by placing the log_it decorator
before the setter only. This will log the getter, setter and deleter.

#*class attributes*
instead of using log_it as a decorator you need to use it like you would a function and place the data
into the function call that you want to have the attribnute set to.

    class SomeClass(object):
        class_attribute = log_it('this is the contents')

you will have a log entry when the data gets accessed or changed.

No I am sure at some point or another you have had to deal ith the logging mess when running a multi
threaded application. It is a daunting task to sift through the log having to piece together a log that makes sense.

I have simplified this for you. there are 2 functions also in this module.

* `start_logging_run`: starts a loggin run 
* `end_logging_run`: ends a logging run

so say you have a thread that is about to go to work. if you 'call start_logging_run' then do the work
and call `end_logging_run` when finished it is going to spit out anl logging done by using log_it in the order
in which each step through your application was taken. it keeps everything all nice and neat and easy to understand.
it also times how long it took for the complete run to take. This is nice for determining a bottleneck.

This library uses the logging module which is a standard library included with Python. This is important if you
want things to get displayed correctly. You will want to have the following code in each of the files here you are
using log_it.

    import logging
    logger = logging.getLogger(__name__)

you can have logger set to LOGGER if you like it will work either way.

log_it searches the functions, methods or properties \_\_globals\_\_ attribute to see if `logger' or `LOGGER` exits.
and this is what gets used to output the log information for where the decorator is located.

you are also going to wat to have the following in the \_\_init\_\_ of your application

    import logging

    FORMAT = '%(asctime)-15s - %(message)s'
    logging.basicConfig(level=NOTSET, format=FORMAT)

you would change NOTSET to any of the logging levels included in this library. None of the logging levels that are
apart of the logging library are going to make this decorator function.

* LEVEL_TIME_IT: times the calls
* LEVEL_ARGS: logs any parameters passed to a call
* LEVEL_RETURN: logs the return data from a call
* LEVEL_CALL_FROM: file and lone number information where the call was made from
* LEVEL_CALL_TO: file and line number information where the call was made to.
* LEVEL_ANGRY: all of the above

I created the logging levels so they can be combined by means of "bitwise or" `|`. So if you want to log the    
returned data and the passed arguments you would use  `LEVEL_ARGS | LEVEL_RETURN` `LEVEL_ANGRY` is the same as doing
`LEVEL_TIME_IT | LEVEL_ARGS | LEVEL_RETURN | LEVEL_CALL_FROM | LEVEL_CALL_TO`

So here is the brief version

Add this to the first file that gets run in your application

    import logging
    import angry_debugger
        
        
    FORMAT = '%(asctime)-15s - %(message)s'
    logging.basicConfig(level=angry_debugger.LEVEL_ARGS | angry_debugger.LEVEL_RETURN, format=FORMAT)

you can change the level to any of the angry_debugger.LEVEL_* constants or a combination of them using
the `|` between them

add this to that first file as well and also to any file that is using log_it

    import logging
    logger = logging.getLogger(__name__)


add this before a function, methods r property decleration

    @angry_debugger.log_it

add this for a class attribute

    some_attribute = angry_debugger.log_it('some attribute value')
    
***IMPORTANT***
    
This debugging routine is very expensive to run. It WILL slow down the program you are using it in if the 
logging level is set to one of the level constants. This library is for debugging use ONLY. it can create HUGE 
amounts of data in a really small period of time. So be careful when having it write to a file. 
