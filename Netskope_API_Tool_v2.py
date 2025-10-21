import os
import requests
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime

# ----- CONFIG -----

tenant = input("\nTenant name: ")
api_key = input("API key: ")

tenant_url = f"https://{tenant}.goskope.com"


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def scim_header():
    return {
        "accept": "application/json",
        "Authorization": "Bearer " + api_key
    }

def api_header():
    return {
        "accept": "application/json",
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json"
    }

def safe_request(method, url, headers=None, json=None, params=None, timeout=15):
    try:
        r = requests.request(method, url, headers=headers, json=json, params=params, timeout=timeout)
        return r
    except requests.exceptions.Timeout:
        print("\n[ERROR] Request timed out.")
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Connection error. Check your network or tenant URL.")
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Request failed: {e}")
    return None

def select_option():
    while True:
        clear_screen()
        print("\n----- Netskope API Tool -----\n")
        print("1 - Manage Groups")
        print("2 - Manage Users")
        print("3 - Manage Private Apps")
        print("0 - Exit")

        choice = input("\nChoose a number: ")

        if choice == "1":
            menu_manage_groups()
            input("\nPress ENTER to return to the main menu...")
        elif choice == "2":
            menu_manage_users()
            input("\nPress ENTER to return to the main menu...")
        elif choice == "3":
            menu_manage_papps()
            input("\nPress ENTER to return to the main menu...")
        elif choice == "0":
            print("\n### Script finished ###\n")
            break
        else:
            print("Invalid option!")


# ----- GROUPS -----

def menu_manage_groups():
    while True:
        clear_screen()
        print("\n----- MANAGE GROUPS -----\n")
        print("1 - Create SCIM group")
        print("2 - Add group member")
        print("3 - Remove group member")
        print("4 - Search Group ID")
        print("0 - Return to the main menu")

        choice = input("\nChoose a number: ")

        if choice == "1":
            create_group()
            input("\nPress ENTER to return to the menu...")
        elif choice == "2":
            add_group_member()
            input("\nPress ENTER to return to the menu...")
        elif choice == "3":
            remove_group_member()
            input("\nPress ENTER to return to the menu...")
        elif choice == "4":
            find_group(input("\nGroup name: "))
            input("\nPress ENTER to return to the menu...")
        elif choice == "0":
            break
        else:
            print("Invalid option!")

def create_group():
    print("\n----- CREATE SCIM GROUP -----")
    request_url = tenant_url + "/api/v2/scim/Groups"
    group_name = input("\nGroup name: ")

    data = {
        "displayName": group_name,
        "externalId": group_name,
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"]
    }

    r = safe_request("POST", request_url, headers=scim_header(), json=data)
    if not r:
        return

    if r.status_code == 201:
        resp = r.json()
        print("\nGroup created successfully!")
        print(f"Name: {resp['displayName']}\nExternal ID: {resp['externalId']}\nID: {resp['id']}")
    else:
        print("\nError:", r.text)

def find_group(group_name):
    request_url = f"{tenant_url}/api/v2/scim/Groups"
    params = {"filter": f"displayName eq {group_name}"}
    r = safe_request("GET", request_url, headers=scim_header(), params=params)
    if not r:
        return None

    if r.status_code != 200:
        print("\nError:", r.text)
    elif r.json().get('totalResults', 0) == 0:
        print("\nGroup not found!")
    else:
        group_id = r.json()['Resources'][0]['id']
        print(f"\nGroup found! ID: {group_id}")
        return group_id

def find_user(user):
    request_url = f"{tenant_url}/api/v2/scim/Users"
    params = {"filter": f"userName eq {user}"}
    r = safe_request("GET", request_url, headers=scim_header(), params=params)
    if not r:
        return None

    if r.status_code != 200:
        print("\nError:", r.text)
    elif r.json().get('totalResults', 0) == 0:
        print("\nUser not found!")
    else:
        user_id = r.json()['Resources'][0]['id']
        print(f"\nUser found! ID: {user_id}")
        return user_id

def patch_group_member(group_id, user_id, op):
    request_url = f"{tenant_url}/api/v2/scim/Groups/{group_id}"

    data = {
        "Operations": [
            {
                "op": op,
                "path": "members",
                "value": [{"value": user_id}]
            }
        ],
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"]
    }

    r = safe_request("PATCH", request_url, headers=scim_header(), json=data)
    if not r:
        return

    if r.status_code in (200, 204):
        print(f"\nMember {op} successfully!")
    else:
        print("\nError:", r.text)

def add_group_member():
    print("\n----- ADD GROUP MEMBER -----\n")
    group_id = find_group(input("Group name: "))
    user_id = find_user(input("\nUser: "))
    if group_id and user_id:
        patch_group_member(group_id, user_id, "add")

def remove_group_member():
    print("\n----- REMOVE GROUP MEMBER -----\n")
    group_id = find_group(input("Group name: "))
    user_id = find_user(input("\nUser: "))
    if group_id and user_id:
        patch_group_member(group_id, user_id, "remove")


# ----- USERS -----

def menu_manage_users():
    while True:
        clear_screen()
        print("\n----- MANAGE USERS -----\n")
        print("1 - Search User ID")
        print("2 - Create SCIM User")
        print("3 - Delete SCIM User")
        print("0 - Return to the main menu")

        choice = input("\nChoose a number: ")
        if choice == "1":
            find_user(input("\nUsername: "))
            input("\nPress ENTER to return to the menu...")
        elif choice == "2":
            create_scim_user()
            input("\nPress ENTER to return to the menu...")
        elif choice == "3":
            delete_scim_user(find_user(input("\nUsername: ")))
            input("\nPress ENTER to return to the menu...")
        elif choice == "0":
            break
        else:
            print("Invalid option!")

def delete_scim_user(user_id):
    
    request_url = tenant_url + "/api/v2/scim/Users/"+user_id

    r = safe_request("DELETE", request_url, headers=scim_header())
    if not r:
        return

    if r.status_code == 204:
        print("\nUser deleted successfully!")
    else:
        print("\nError:", r.text)

def create_scim_user():
    
    print("\n----- CREATE SCIM USER -----")
    request_url = tenant_url + "/api/v2/scim/Users"
    first_name = input("\nFirst Name: ")
    last_name = input("Last Name: ")
    username = input("Username (UPN/Email): ")
    
    data = {
    "active": "true",
    "emails": [
        {
        "primary": "true",
        "value": username
        }
    ],
    "externalId": username,
    "meta": {
        "resourceType": "User"
    },
    "name": {
        "familyName": last_name,
        "givenName": first_name
    },
    "schemas": [
        "urn:ietf:params:scim:schemas:core:2.0:User",
        "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
        "urn:ietf:params:scim:schemas:extension:tenant:2.0:User"
    ],
    "userName": username
    }

    r = safe_request("POST", request_url, headers=scim_header(), json=data)
    if not r:
        return

    if r.status_code == 201:
        print("\nUser created successfully!")
    else:
        print("\nError:", r.text)

# ----- PRIVATE APPS -----

def menu_manage_papps():
    while True:
        clear_screen()
        print("\n----- MANAGE PRIVATE APPS -----\n")
        print("1 - Manage Private App Publishers")
        print("2 - Manage Private App Tags")
        print("3 - Remove Private Apps")
        print("4 - Create Private Apps from Excel")
        print("5 - Create Private App policies from Excel")
        print("0 - Return to the main menu")

        choice = input("\nChoose a number: ")

        if choice == "1":
            menu_manage_publishers()
            input("\nPress ENTER to return to the menu...")
        elif choice == "2":
            menu_manage_tags()
            input("\nPress ENTER to return to the menu...")
        elif choice == "3":
            menu_remove_papps()
            input("\nPress ENTER to return to the menu...")
        elif choice == "4":
            create_apps(file_path=input("\nFile path: "),sheet_name=input("Sheet name: "))
            input("\nPress ENTER to return to the menu...")
        elif choice == "5":
            create_papp_policy(file_path=input("\nFile path: "),sheet_name=input("Sheet name: "))
            input("\nPress ENTER to return to the menu...")
        elif choice == "0":
            break
        else:
            print("Invalid option!")

def menu_remove_papps():
    while True:
        clear_screen()
        print("\n----- REMOVE PRIVATE APPS -----\n")
        print("1 - Remove Private Apps that start with...")
        print("2 - Remove all Private Apps")
        print("0 - Return to the main menu")

        choice = input("\nChoose a number: ")

        if choice == "1":
            papps_delete(get_papps(input("\nPrivate Apps starts with: ")))
            input("\nPress ENTER to return to the Private Apps menu...")
        elif choice == "2":
            papps_delete(get_all_papps())
            input("\nPress ENTER to return to the Private Apps menu...")
        elif choice == "0":
            break
        else:
            print("Invalid option!")

def menu_manage_tags():
    while True:
        clear_screen()
        print("\n----- MANAGE PRIVATE APP TAGS -----\n")
        print("1 - Apply tags from Excel (per host)")
        print("2 - Remove tags from Private Apps that start with")
        print("3 - Remove tags from all Private Apps")
        print("0 - Return to the main menu")

        choice = input("\nChoose a number: ")

        if choice == "1":
            papps_tags_from_excel()
            input("\nPress ENTER to return to the Private Apps menu...")
        elif choice == "2":
            papps_tags_delete(get_papps(input("\nPrivate Apps starts with: ")))
            input("\nPress ENTER to return to the Private Apps menu...")
        elif choice == "3":
            papps_delete(get_all_papps())
            input("\nPress ENTER to return to the Private Apps menu...")
        elif choice == "0":
            break
        else:
            print("Invalid option!")

def menu_manage_publishers():
    while True:
        clear_screen()
        print("\n----- MANAGE PRIVATE APP PUBLISHERS -----\n")
        print("1 - Replace publishers from all Private Apps")
        print("2 - Add publishers in all Private Apps")
        print("3 - Remove publishers from all Private Apps")
        print("4 - Replace publishers from specific Private Apps")
        print("5 - Add publishers for specific Private Apps")
        print("6 - Remove publishers from specific Private Apps")
        print("0 - Return to the main menu")

        choice = input("\nChoose a number: ")

        if choice == "1":
            publisher_bulk("replace")
            input("\nPress ENTER to return to the Private Apps menu...")
        elif choice == "2":
            publisher_bulk("add")
            input("\nPress ENTER to return to the Private Apps menu...")
        elif choice == "3":
            publisher_bulk("delete")
            input("\nPress ENTER to return to the Private Apps menu...")
        elif choice == "0":
            break
        else:
            print("Invalid option!")

def get_all_papps():
    r = safe_request("GET", f"{tenant_url}/api/v2/steering/apps/private", headers=api_header())
    if not r:
        return []
    return [app['app_id'] for app in r.json().get('data', {}).get('private_apps', [])]

def get_papps(startswith):
    r = safe_request("GET", f"{tenant_url}/api/v2/steering/apps/private?fields=app_id%2Capp_name&query=name%20sw%20{startswith}", headers=api_header())
    if not r:
        return []
    return [app['app_id'] for app in r.json().get('data', {}).get('private_apps', [])]

def publisher_check():
    r = safe_request("GET", f"{tenant_url}/api/v2/infrastructure/publishers", headers=api_header())
    if not r:
        return []

    if r.status_code == 200:
        print("\nPublishers found:\n")
        publishers = r.json()['data']['publishers']
        for idx, pub in enumerate(publishers):
            print(f"{idx} - {pub['publisher_name']}")

        choice = input("\nChoose publishers (comma separated): ")
        indices = [int(i) for i in choice.split(",") if i.strip().isdigit()]
        return [publishers[i]['publisher_id'] for i in indices if 0 <= i < len(publishers)]
    else:
        print("Error:", r.text)
        return []

def publisher_bulk(action):
    private_apps = [str(x) for x in get_all_papps()]
    publishers = [str(x) for x in publisher_check()]

    if not private_apps or not publishers:
        print("\n[INFO] No apps or publishers selected.")
        return

    data = {"private_app_ids": private_apps, "publisher_ids": publishers}
    url = f"{tenant_url}/api/v2/steering/apps/private/publishers"

    method_map = {
        "replace": "PUT",
        "add": "PATCH",
        "delete": "DELETE"
    }

    r = safe_request(method_map[action], url, headers=api_header(), json=data)
    if not r:
        return

    status = r.json().get("status")
    if status == "success":
        print(f"\nPublishers {action} successfully!")
    else:
        print("\nFailure:", r.text)

def get_all_papps_tags():
    url = f"{tenant_url}/api/v2/steering/apps/private/tags"
    r = safe_request("GET", url, headers=api_header())
    if not r:
        return
    
    tags = []
    
    for tag in r.json()["data"]["tags"]:
        tags.append(tag["tag_name"])

    return(tags)

def papps_tags_delete(private_apps):
    private_apps = [str(x) for x in private_apps]

    if not private_apps:
        print("\n[INFO] No Private Apps found.")
        return

    url = f"{tenant_url}/api/v2/steering/apps/private/tags"

    tags_temp = get_all_papps_tags()

    tags = []

    for tag in tags_temp:
        tags.append({"tag_name": tag})

    data = {
        "ids": private_apps,
        "tags": tags
        }

    r = safe_request("DELETE", url, headers=api_header(), json=data)

    if not r:
        return
    status = r.json().get("status")
    if status == "success":
        print(f"\nTags deleted successfully!")
    else:
        print("\nFailure:", r.text)

def papps_delete(private_apps):
    private_apps = [str(x) for x in private_apps]

    papps_tags_delete(private_apps)

    if not private_apps:
        print("\n[INFO] No Private Apps found.")
        return

    data = {"private_app_ids": private_apps}

    url = f"{tenant_url}/api/v2/steering/apps/private"


    r = safe_request("DELETE", url, headers=api_header(), json=data)

    if not r:
        return
    status = r.json().get("status")
    if status == "success":
        print(f"\nPrivate Apps removed successfully!")
    else:
        print("\nFailure:", r.text)


# ----- PRIVATE APPS TAGS -----

def _clean_tags(raw: str) -> List[Dict[str, str]]:

    if not isinstance(raw, str):
        return []
    seen = set()
    out = []
    for t in (x.strip() for x in raw.split(",")): # x.strip somente para remover espacos extras da tag
        if t and t not in seen:
            out.append({"tag_name": t})
            seen.add(t)
    return out


def _get_private_app_id_by_host(host: str) -> Optional[str]:

    url = f"{tenant_url}/api/v2/steering/apps/private"
    params = {"query": f'name has "{host}"', "silent": "0"}
    r = safe_request("GET", url, headers=api_header(), params=params)
    if not r:
        return None

    try:
        j = r.json()
    except ValueError:
        print(f"\n[WARN] Invalid JSON searching host '{host}'.")
        return None

    if j.get("status") != "success":
        print(f"\n[WARN] Non-success for host '{host}': {j.get('status')}")
        return None

    apps = j.get("data", {}).get("private_apps", []) or []
    if not apps:
        print(f"\n[WARN] App not found for host '{host}'.")
        return None

    app = apps[0]
    app_id = app.get("app_id")
    app_name = app.get("app_name")
    if app_id:
        print(f"\n[OK] Found: {app_name} | ID: {app_id}")
        return str(app_id)

    print(f"\n[WARN] 'app_id' missing for host '{host}'.")
    return None


def _apply_tags_to_ids(ids: List[str], tags: List[Dict[str, str]]) -> bool:

    if not ids:
        print("\n[WARN] No IDs to tag.")
        return False
    if not tags:
        print("\n[WARN] No valid tags to apply.")
        return False

    url = f"{tenant_url}/api/v2/steering/apps/private/tags"
    payload = {"ids": ids, "tags": tags}

    r = safe_request("PATCH", url, headers=api_header(), json=payload)
    if not r:
        return False

    try:
        j = r.json()
    except ValueError:
        print("\n[WARN] Invalid JSON in tag application response.")
        return False

    if j.get("status") == "success":
        data = j.get("data", [])
        if isinstance(data, list):
            for item in data:
                name = item.get("name", "<no-name>")
                print(f"[OK] Tags applied to: {name}")
        else:
            print("[OK] Tags applied.")
        return True

    print("\n[FAIL] Tag application failed:", r.text)
    return False


def papps_tags_from_excel():

    print("\n----- APPLY TAGS FROM EXCEL (PER HOST) -----")
    file_path = input("\nExcel file path: ").strip()
    sheet_name = input("Sheet name: ").strip()

    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        print(f"\n[ERROR] Unable to read Excel: {e}")
        return

    required = {"Host", "Tag"}
    missing = required - set(df.columns)
    if missing:
        print(f"\n[ERROR] Missing columns in sheet: {', '.join(sorted(missing))}")
        return

    print("\n### STARTING TAG ROUTINE ###")
    for _, row in df.iterrows():
        host = str(row["Host"]).strip()
        tags = _clean_tags(row["Tag"])

        print(f"\nHost = {host}")
        app_id = _get_private_app_id_by_host(host)
        if app_id:
            _apply_tags_to_ids([app_id], tags)
        else:
            print("[WARN] Skipping tag application (app not found).")

# ----- PRIVATE APPS CREATION -----

def publisher_validation():

    url = f"{tenant_url}/api/v2/infrastructure/publishers?fields=publisher_id%2Cpublisher_name"

    r = safe_request("GET", url, headers=api_header())

    if not r:
        return
    
    publishers = r.json()['data']['publishers']

    status = r.json().get("status")

    if status == "success":
        return publishers
    else:
        print("\nFailure:", r.text)

def create_apps(file_path: str, sheet_name: str):

    url = f"{tenant_url}/api/v2/steering/apps/private?silent=0"

    logs = []

    if not (file_path and sheet_name):
        print("\n[INFO] Necessary parameters not found!")
        return

    print("\n\n### Automation started ###")
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    for index, row in df.iterrows():

        host = row['Host'].split(',')

        tags = []
        tags_unf = row['Tag'].split(',')
        for tag in tags_unf:
            tags.append({"tag_name": tag})

        publishers = []
        publishers_temp = row['Publisher'].split(',')
        publisher_check_response = publisher_validation()

        for publisher in publishers_temp:
            for index in publisher_check_response:
                if publisher in index['publisher_name']:
                    publishers.append(index)

        protocols = []
        protocol_entries = row['Port'].split(',')
        for entry in protocol_entries:
            proto_type, port = entry.split(':')
            protocols.append({"port": port, "type": proto_type})
        
        app_name = row['Name']
        suffix = row['Suffix']
        access_type = row['Access Type'].split(',')
        anyapp_protocol = row['AnyApp Protocol']
        use_publisher_dns = row['Use Publisher DNS']

        if len(host) == 1:
            app_name = suffix+'_'+app_name
        else:
            app_name = suffix+'_Combined_'+len(host)

        print(f"\nHost = {host}")
        print(f"Port = {protocols}")

        if 'Client' in access_type:
            data = {
                "app_name": app_name,
                "clientless_access": "false",
                "host": host,
                "protocols": protocols,
                "publishers": publishers,
                "tags": tags,
                "use_publisher_dns": use_publisher_dns
            }

            r = safe_request("POST", url, headers=api_header(), json=data)
        
            if r.json()['status'] == "success":
                print("Response Body:","\033[32m", r.json()['status'],"\033[0m")
                print("Private App: "+app_name+"\n")
                response = "\nPrivate App: "+app_name+"\nHost: "+str(host)+"\nProtocols: "+str(protocols)+"\nAccess Type: "+str(access_type)+"\nResponse: "+r.json()['status']
                logs.append(response)
            else:
                print("Response Body:","\033[33m", r.text,"\033[0m")
                response = "\nPrivate App: "+app_name+"\nHost: "+str(host)+"\n"+"Protocols: "+str(protocols)+"\n"+"Error: "+str(r.status_code)+"\n"+"Response: "+r.json()['status']
                logs.append(response)

        if 'Browser' in access_type:
            data = {
                "app_name": app_name+"_Browser",
                "host": host,
                "clientless_access": "true",
                "private_app_protocol": anyapp_protocol,
                "protocols": protocols,
                "publishers": publishers,
                "tags": tags,
                "use_publisher_dns": use_publisher_dns
                }
            
            r = safe_request("POST", url, headers=api_header(), json=data)

            if r.json()['status'] == "success":
                print("Response Body:","\033[32m", r.json()['status'],"\033[0m")
                print("Private App: "+app_name+"\n")
                response = "\nPrivate App: "+app_name+"\nHost: "+str(host)+"\nProtocols: "+str(protocols)+"\nAccess Type: "+str(access_type)+"\nResponse: "+r.json()['status']
                logs.append(response)
            else:
                print("Response Body:","\033[33m", r.text,"\033[0m")
                response = "\nPrivate App: "+app_name+"\nHost: "+str(host)+"\n"+"Protocols: "+str(protocols)+"\n"+"Error: "+str(r.status_code)+"\n"+"Response: "+r.json()['status']
                logs.append(response)

    write_logs(log_filename="papps_creation.txt",logs=logs)

def create_papp_policy(file_path: str, sheet_name: str):

    url = f"{tenant_url}/api/v2/policy/npa/rules"

    logs = []

    if not (file_path and sheet_name):
        print("\n[INFO] Necessary parameters not found!")
        return

    print("\n\n### Automation started ###")
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    for index, row in df.iterrows():

        policy_group = str(row['Policy Group'])

        access_method = str(row['Access Method']) if pd.notna(row['Access Method']) else []
        if access_method != []:
            access_method = access_method.split(',')

        action = str(row['Action']).lower()

        private_apps_temp = str(row['Private Apps']) if pd.notna(row['Private Apps']) else []
        if private_apps_temp != []:
            private_apps_temp = private_apps_temp.split(',')

        private_apps_tags = str(row['Tags']) if pd.notna(row['Tags']) else []
        if private_apps_tags != []:
            private_apps_tags = private_apps_tags.split(',')

        users = str(row['Users']) if pd.notna(row['Users']) else []
        if users != []:
            users = users.split(',')

        user_groups = str(row['Groups']) if pd.notna(row['Groups']) else []
        if user_groups != []:
            user_groups = user_groups.split(',') 

        private_apps = []

        if action == "allow" or "Allow":
            policy_name = '[NPA] Liberar '+private_apps_temp[0]
        elif action == "deny" or "Deny":
            policy_name = '[NPA] Bloquear '+private_apps_temp[0]

        for app in private_apps_temp:
            private_apps.append(f"[{app}]")


        data = {
                    "description": "any",
                    "enabled": "1",
                    "group_name": policy_group,
                    "rule_data": {
                    "access_method": access_method,
                    "json_version": 3,
                    "match_criteria_action": {
                        "action_name": action
                    },
                    "policy_type": "private-app",
                    "privateAppTags": private_apps_tags,
                    "privateApps": private_apps,
                    "userGroups": user_groups,
                    "userType": "user",
                    "users": users,
                    "version": 1
                    },
                    "rule_name": policy_name,
                    "rule_order": {
                    "order": "bottom"
                    }
                }
            
        r = safe_request("POST", url, headers=api_header(), json=data)
        
        if r.json()['status'] == "success":
            print("Response Body:","\033[32m", r.json()['status'],"\033[0m")
            print("Policy Name: "+policy_name+"\n")
            response = "\nPolicy Name: "+policy_name+"\nResponse: "+r.json()['status']
            logs.append(response)

        elif "may exist already" in r.text:
            count = 2
            while "may exist already" in r.text:
                new_policy_name = f"{policy_name} - {count}"
                data = {
                    "description": "any",
                    "enabled": "1",
                    "group_name": policy_group,
                    "rule_data": {
                    "access_method": access_method,
                    "json_version": 3,
                    "match_criteria_action": {
                        "action_name": action
                    },
                    "policy_type": "private-app",
                    "privateAppTags": private_apps_tags,
                    "privateApps": private_apps,
                    "userGroups": user_groups,
                    "userType": "user",
                    "users": users,
                    "version": 1
                    },
                    "rule_name": new_policy_name,
                    "rule_order": {
                    "order": "bottom"
                    }
                }
                r = safe_request("POST", url, headers=api_header(), json=data)
                count = count+1
            if r.json()['status'] == "success":
                print("Response Body:","\033[32m", r.json()['status'],"\033[0m")
                print("Policy Name: "+new_policy_name+"\n")
                response = "\nPolicy Name: "+new_policy_name+"\nResponse: "+r.json()['status']
                logs.append(response)
            else:
                print("Response Body:","\033[33m", r.text,"\033[0m")
                response = "\nPolicy Name: "+new_policy_name+"\nError: "+str(r.status_code)+"\nResponse: "+r.json()['status']
                logs.append(response)
    
        else:
            print("Response Body:","\033[33m", r.text,"\033[0m")
            response = "\nPolicy Name: "+policy_name+"\nError: "+str(r.status_code)+"\nResponse: "+r.json()['status']
            logs.append(response)

    write_logs(log_filename="create_policies.txt",logs=logs)

def write_logs(log_filename: str, logs):
    outputPath = "c:\\Netskope_API_Tool"
    if log_filename and logs:
        if not os.path.exists(outputPath):
            os.mkdir(outputPath)

        dateNow = datetime.now().strftime("%d-%m-%Y_%Hh%Mm")
        pathDate = f"{outputPath}\\{dateNow}"

        os.mkdir(pathDate)

        with open(f"{pathDate}\\{log_filename}", 'w') as arquivo:
            arquivo.write(f"\n{dateNow}\n\n")
            arquivo.writelines('\n'.join(logs))
    else:
        return



if __name__ == "__main__":
    select_option()
    # papps_tags_delete(get_papps(input("\nPrivate Apps starts with: ")))