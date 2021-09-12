import requests
import ftplib
import json
import os
import random
import valve.rcon # pip install python-valve

API_CALL = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key=7BAAE5A35399433A53AD843D0B595324&vanityurl="
MAPLIST = ["de_vertigo", "de_dust2", "de_inferno", "de_mirage", "de_nuke", "de_overpass", "de_train"]
TEAMS = {}
SERVERS = {}
UPLOADED = set()
RUNNING = set()
global TOURNAMENT_NAME
PRINT_INSTRUCTIONS = True
YES = ["y", "Y", "yes", "YES", "Yes", "1"]
global DATHOST, DATHOST_user, DATHOST_pass


def init():
    global TOURNAMENT_NAME
    clear()
    TOURNAMENT_NAME = input("Enter the name of the tournament (will be added as a cvar to all matches): ").strip()
    clear()
    if not os.path.exists("files/"):
        os.mkdir("files")
    global DATHOST, DATHOST_user, DATHOST_pass
    DATHOST = os.path.exists("files/dathost.txt")
    if DATHOST:
        file = open("files/dathost.txt")
        DATHOST_user = file.readline().strip()
        DATHOST_pass = file.readline().strip()
        file.close()
    if not os.path.exists("out/"):
        os.mkdir("out")
    if os.path.exists("files/teams.json"): 
        file = open("files/teams.json", "r")
        data = json.load(file)
        file.close()
        for team in data['teams']:
            TEAMS[team['teamname']] = team
    if os.path.exists("files/servers.json"):
        file = open("files/servers.json", "r")
        data = json.load(file)
        file.close()
        for server in data['servers']:
            SERVERS[server['name']] = server
    if not os.path.exists("files/servers.json") or os.stat("files/servers.json").st_size < 15:
        file = open("files/servers.json", "w")
        json.dump({"servers": []}, file)
        file.close()
    if not os.path.exists("files/teams.json") or os.stat("files/teams.json").st_size < 13:
        file = open("files/teams.json", "w")
        json.dump({"files/teams": []}, file)
        file.close()
    if not os.path.exists("files/matches.json") or os.stat("files/matches.json").st_size < 15:
        file = open("files/matches.json", "w")
        json.dump({"matches": []}, file)
        file.close()


def upload(ftp, file, filename="match_config.cfg"):
    ftp.storlines('STOR '+filename, open(file, 'rb'))


# creates a new team and asks the user for their URLs and nicknames
def new_team(teamname, players):
    file = open("files/teams.json", "r")
    data = json.load(file)
    file.close()

    file = open("files/teams.json", "w")
    data['teams'].append({
        'teamname': teamname,
        'players': players
    })
    json.dump(data, file)
    file.close()
    TEAMS[teamname] = {"teamname" : teamname, "players": players}


def new_team_with_entry():
    teamname = input("Enter the team name: ").strip()
    if len(teamname) == 0:
        print("Name cannot be empty, team not created")
        return
    if teamname in TEAMS.keys():
        print("This name is already used, team not created")
        return
    players = []
    for i in range(5):
        player = {}
        tempinput = input("Enter the profile URL: ").strip()
        if tempinput[-1] == '/':
            tempinput = tempinput[:-1:]
        tempinput = tempinput[tempinput.rfind("/")+1::]
        response = requests.get(API_CALL+tempinput)
        if not response.json()['response']['success'] == 42:
            player["steamid"] = response.json()['response']['steamid']
        else:
            player["steamid"] = tempinput
        player['nick'] = input("Enter the player's nick (leave ampty if Steam's): ").strip()
        players.append(player)
    new_team(teamname, players)


def team_info(teamname):
    team = TEAMS[teamname]
    print("Team name: "+teamname)
    print("Players:")
    for player in team['players']:
        print("\t"+player['steamid']+" "+player['nick'])
    print()


# creates a new server and asks the user for the credentials
def new_server(name, host, port, user, password, rcon, rcon_port, rcon_pass, srv_id):
    file = open("files/servers.json", "r")
    data = json.load(file)
    file.close()

    file = open("files/servers.json", "w")
    data['servers'].append({
        'name': name,
        'host': host,
        'port': port,
        'user': user,
        'pass': password,
        'rcon': rcon,
        'rcon_port': rcon_port,
        'rcon_pass': rcon_pass,
        'srv_id': srv_id
    })
    json.dump(data, file)
    file.close()
    SERVERS[name] = {"name": name, "host": host, "port": port, "user": user, "pass": password,
                     'rcon': rcon, 'rcon_port': rcon_port, 'rcon_pass': rcon_pass, 'srv_id': srv_id}


# creates a new server and asks the user for the credentials
def new_server_with_entry():
    name = input("Enter the server's name: ").strip()
    if len(name) == 0:
        print("Name cannot be empty, server not created")
        return
    if name in SERVERS.keys():
        print("This name is already used, server not created")
        return
    new_server(name, input("Enter the host (IP for FTP): ").strip(),
               int(input("Enter the FTP port: ").strip()), input("Enter the FTP username: ").strip(),
                input("Enter the FTP password: ").strip(), input("Enter the rcon address: ").strip(),
               int(input("Enter the rcon port: ").strip()), input("Enter the rcon password: ").strip(),
               input("Enter the server ID (if you use dathost):"))


def server_list():
    servers = ""
    for temp in SERVERS.keys():
        if len(servers) != 0:
            servers += ", "
        servers += temp
    return servers+"\n"

def team_list():
    out = ""
    for key in TEAMS.keys():
        if len(out) != 0:
            out += ", "
        out += key
    return out+"\n"


def server_info(servername):
    server = SERVERS[servername]
    print("Server name: "+servername)
    print("FTP IP: "+server['host'])
    print("FTP port: "+str(server['port']))
    print("FTP username: "+server['user'])
    print("FTP password: "+server['pass'])
    print("RCON address: "+server['rcon'])
    print("RCON port: "+str(server['rcon_port']))
    print("RCON password: "+server['rcon_pass'])
    if DATHOST:
        print("Server ID: "+server['srv_id'])
        response = requests.get("https://dathost.net/api/0.1/game-servers/"+server['srv_id'], auth=(DATHOST_user, DATHOST_pass)).json()
        print("Server is running: "+str(response['on']))
    print()


def stop(servername):
    server = SERVERS[servername]
    requests.post("https://dathost.net/api/0.1/game-servers/" + server['srv_id'] + "/stop",
                  auth=(DATHOST_user, DATHOST_pass))

def clear():
    if os.name == "nt":
        _ = os.system('cls')
    else:
        _ = os.system('clear')


def new_game(id, team1, team2):
    if os.path.exists("out/"+id+".cfg"):
        confirmation = input("A config with that config already exists, do you want to continue?").strip()
        if confirmation not in YES:
            print("config not created")
            return
    if team1 not in TEAMS.keys() or team2 not in TEAMS.keys():
        print("One of the teams does not exist, match not created")
        return
    team1 = TEAMS[team1]
    team2 = TEAMS[team2]
    file = open("out/"+id+".cfg", "w")
    file.write('"Match"\n{\n\t"matchid"\t"'+id+'"\n\t"num_maps"\t"'+input("Enter the number of maps: ").strip()+'"\n\n\t')
    file.write('"spectators"\n\t{\n\t\t"players"\n\t\t{')
    if os.path.exists("files/admins.txt"):
        admins = open("files/admins.txt", "r")
        for row in admins:
            row = row.strip()
            file.write("\n\t\t\t"+row)
    file.write('\n\t\t}\n\t}\n\n\t')
    file.write('"skip_veto"\t"0"\n\t"veto_first"\t')
    if bool(random.getrandbits(1)):
        file.write('"team1"')
    else:
        file.write('"team2"')
    file.write('\n\t"side_type"\t"always_knife"\n\n\t"maplist"\n\t{')
    for map in MAPLIST:
        file.write('\n\t\t"'+map+'"\t""')
    file.write("\n\t}\n\n")
    file.write('\t"players_per_team"\t"5"\n\t"min_players_to_ready"\t"1"\n\t"min_spectators_to_ready"\t"0"\n\n\t')
    file.write('"team1"\n\t{\n\t\t"name"\t"'+team1['teamname']+'"\n\t\t"tag"\t""\n\t\t"flag"\t""\n\t\t"logo"\t""\n\t\t')
    file.write('"players"\n\t\t{')
    for player in team1['players']:
        file.write('\n\t\t\t"'+player['steamid']+'"\t"'+player['nick']+'"')
    file.write('\n\t\t}\n\t}\n\n\t')
    file.write('"team2"\n\t{\n\t\t"name"\t"'+team2['teamname']+'"\n\t\t"tag"\t""\n\t\t"flag"\t""\n\t\t"logo"\t""\n\t\t')
    file.write('"players"\n\t\t{')
    for player in team2['players']:
        file.write('\n\t\t\t"' + player['steamid'] + '"\t"' + player['nick'] + '"')
    file.write('\n\t\t}\n\t}\n\n\t')
    file.write('"cvars"\n\t{\n\t\t"hostname"\t"'+TOURNAMENT_NAME+'"\n\t}\n}')
    file.close()


init()
instructions = "Main menu - "+TOURNAMENT_NAME+"\n1: Teams menu, 2: Servers menu, 3: Create a new config, 4: Upload a match to a server, 9: toggle instructions, 0: Exit"
while True:
    if PRINT_INSTRUCTIONS:
        print(instructions)
    usr_input = input("Enter one of the options: ")[0]
    clear()
    if usr_input == "1":
        sub_instructions = "Teams menu - "+TOURNAMENT_NAME+"\n1: Print all teams, 2: Print team info, 3: Create a new team, 0: Go back"
        while True:
            print(sub_instructions)
            sub_usr_input = input("Enter one of the options: ")[0]
            clear()
            if sub_usr_input == "1":
                print(team_list())
            elif sub_usr_input == "2":
                teamname = input("Enter the team's name: ").strip()
                if teamname in TEAMS.keys():
                    team_info(teamname)
                else:
                    print("There is no team with that name")
            elif sub_usr_input == "3":
                new_team_with_entry()
            elif sub_usr_input == "0":
                break
    elif usr_input == "2":
        sub_instructions = "Servers menu - "+TOURNAMENT_NAME+"\n1: Print all servers, 2: Print server info, 3: Create a new server, 0: Go back"
        if DATHOST:
            sub_instructions = sub_instructions[:-10:]
            sub_instructions += "4: stop a server, 0: Go back"
        while True:
            print(sub_instructions)
            sub_usr_input = input("Enter one of the options: ")[0]
            clear()
            if sub_usr_input == "1":
                print(server_list())
            elif sub_usr_input == "2":
                servername = input("Enter the server's name: ").strip()
                if servername in SERVERS.keys():
                    server_info(servername)
                else:
                    print("There is no server with that name")
            elif sub_usr_input == "3":
                new_server_with_entry()
            elif sub_usr_input == "4" and DATHOST:
                running = ""
                for server in RUNNING:
                    if len(running) != 0:
                        running += ", "
                    running += server
                print("Currently running servers: "+running)
                to_close = input("Enter the name of the server you want to stop: ")
                if to_close not in RUNNING:
                    print("There is no server running with that name")
                    continue
                stop(servername)
                RUNNING.remove(servername)
            elif sub_usr_input == "0":
                break
    elif usr_input == "3":
        id = input("Enter the match ID: ").strip().zfill(2)
        print(team_list())
        new_game(id, input("Enter the teamname for team1: ").strip(), input("Enter the teamname for team2: ").strip())
    elif usr_input == "4":
        available = ""
        dupes = "("
        list = os.listdir("out/")
        if len(list) < 1:
            print("No config files are created, nothing was uploaded")
            continue
        for file in list:
            if file in UPLOADED:
                dupes += file + ", "
            else:
                available += ", " + file
        if len(UPLOADED) == 0:
            dupes += "  "
        dupes = dupes[:-2:] + ")"
        available = available[2::]
        print("Files in the directory: "+available+" "+dupes)
        filename = input("Which file do you wish to upload? ").strip()
        if filename in UPLOADED:
            confirmation = input("The file has already been uploaded, do you wish to continue? ").strip()
            if confirmation not in YES:
                print("nothing was uploaded")
                continue
        if not os.path.exists("out/"+filename):
            print("The file does not exist, nothing was uploaded")
            continue
        print(server_list())
        servername = input("Enter the name of the server you want to upload the file to: ").strip()
        if servername not in SERVERS.keys():
            print("That server does not exist, nothing was uploaded")
            continue
        server = SERVERS[servername]
        if server["srv_id"] != "" and DATHOST and servername not in RUNNING:
            requests.post("https://dathost.net/api/0.1/game-servers/"+server['srv_id']+"/start",
                          auth=(DATHOST_user, DATHOST_pass))
        RUNNING.add(servername)
        ftplib.FTP_PORT = server['port']
        ftp = ftplib.FTP(server['host'], server['user'], server['pass'])
        upload(ftp, "out/"+filename, filename)
        UPLOADED.add(filename)
        with valve.rcon.RCON((server['rcon'], server['rcon_port']), server['rcon_pass']) as rcon:
            rcon("get5_loadmatch "+filename)
    elif usr_input == "9":
        if PRINT_INSTRUCTIONS:
            print("printing instructions turned OFF, turn back on with command '9'")
        PRINT_INSTRUCTIONS = not PRINT_INSTRUCTIONS
    elif usr_input == "0":
        exit(0)
