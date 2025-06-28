from threading import Event
exit_event = Event()

sleep_commands = ['sleep', 'it\'s time to sleep', 'you can rest now', 'bedtime', 
                  'initiate sleep mode', 'sleep well', 'go to sleep', 'go and take rest','rest','take rest', 'time to rest', 'you can sleep now']

wake_up_commands = ['wake up','wake up om','are you there', 'let\'s get back to work', 'you there', 'time to wake up', 'ready to start the day?',
                     'let\'s do some work', 'work time', 'awake and alert', 'hello, ready for the day']

exit_commands = ["bye",'by', 'byy',"good bye","see you later", "goodbye", "farewell", "take care", "until next time", "bye bye", 
                    "catch you later", "have a good one", "by krishna",'exit','okay exit','okay bye','bye Om','okay by']
