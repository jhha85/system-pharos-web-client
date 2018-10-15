import os
import requests
import json
import logging

from flask import request, abort
from src.common.objects import SDAManager, Port


class GroupAPI:
    def __init__(self):
        pass

    @classmethod
    def register_api(cls, app):
        # Get groups Info.
        @app.route("/sdamanager/groups", methods=["GET"])
        def sda_manager_groups():
            logging.info("[" + request.method + "] sda manager groups - IN")

            l = list()
            ret = dict()

            # No Input Target Address
            if SDAManager().get_sda_manager_ip() == "":
                d = dict()
                d.update({"address": ""})
                return json.dumps(d), 200

            response = requests.get(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups",
                timeout=1500)

            if response.status_code is not 200:
                logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                abort(500)

            for obj in response.json()["groups"]:
                d = dict()
                if "id" in obj:
                    d.update({"id": str(obj["id"])})
                if "name" in obj:
                    d.update({"name": (obj["name"]).encode('utf-8')})
                if "members" in obj:
                    d.update({"members": str(len(obj["members"]))})
                l.append(d)

            ret.update({"groups": l, "address": SDAManager().get_sda_manager_ip()})

            return json.dumps(json.dumps(ret)), 200

        # Get devices(SDAs) in selected group
        @app.route("/sdamanager/group", methods=["POST"])
        def sda_manager_group():
            logging.info("[" + request.method + "] sda manager group - IN")

            l = list()
            ret = dict()

            data = json.loads(request.data)
            SDAManager.set_group_id(data["id"])
            SDAManager.set_current_group_name(data["name"])

            response = requests.get(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                    + SDAManager.get_group_id(),
                timeout=1500)

            response2 = requests.get(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/nodes",
                timeout=1500)

            if response.status_code is not 200 or response2.status_code is not 200:
                logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                abort(500)

            for obj in response2.json()["nodes"]:
                for member in response.json()["members"]:
                    d = dict()
                    if obj["id"] == member:
                        if "id" in obj:
                            d.update({"id": str(obj["id"])})

                            res = requests.get(
                                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/nodes/" + str(obj["id"]) + "/configuration",
                                timeout=1500)
                            if res.status_code is 200:
                                for prop in res.json()["properties"]:
                                    if "devicename" in prop:
                                        d.update({"name": str(prop["devicename"])})
                        if "ip" in obj:
                            d.update({"ip": str(obj["ip"])})
                        if "status" in obj:
                            d.update({"status": str(obj["status"])})
                        l.append(d)

            ret.update({"devices": l})

            return json.dumps(json.dumps(ret)), 200

        # Create a group
        @app.route("/sdamanager/group/create", methods=["POST"])
        def sda_manager_create_group():
            logging.info("[" + request.method + "] sda manager create group - IN")

            l = list()

            data = json.loads(request.data)
            response = requests.post(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/create",
                data=json.dumps(data),
                timeout=1500)

            response2 = requests.post(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                    + response.json()["id"] + "/join",
                data=json.dumps(data["members"]),
                timeout=1500)

            if response.status_code is not 200 or response2.status_code is not 200:
                logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                abort(500)

            return "", 200

        # Delete a group
        @app.route("/sdamanager/group/delete", methods=["DELETE"])
        def sda_manager_group_delete():
            logging.info("[" + request.method + "] sda manager group delete - IN")

            response = requests.delete(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                    + SDAManager.get_group_id(),
                timeout=1500)

            if response.status_code is not 200:
                logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                abort(500)

            return "", 200

        @app.route("/sdamanager/group/devices", methods=["GET"])
        def sda_manager_group_devices():
            logging.info("[" + request.method + "] sda manager group devices - IN")

            l = list()
            l2 = list()
            ret = dict()

            response = requests.get(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                    + SDAManager.get_group_id(),
                timeout=1500)

            response2 = requests.get(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/nodes")

            if response.status_code is not 200 or response2.status_code is not 200:
                logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                abort(500)

            for obj in response.json()["members"]:
                l2.append(str(obj))

            for obj in response2.json()["nodes"]:
                d = dict()
                if "id" in obj and str(obj["id"]) in l2:
                    d.update({"id": str(obj["id"])})
                    res = requests.get(
                        url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/nodes/" + str(obj["id"]) + "/configuration",
                        timeout=1500)
                    if res.status_code is 200:
                        for prop in res.json()["properties"]:
                            if "devicename" in prop:
                                d.update({"name": str(prop["devicename"])})
                    if "ip" in obj:
                        d.update({"ip": str(obj["ip"])})
                    if "status" in obj:
                        d.update({"status": str(obj["status"])})
                    l.append(d)

            ret.update({"devices": l})

            return json.dumps(json.dumps(ret)), 200

        # Deploy an app to the group
        @app.route("/sdamanager/group/deploy", methods=["POST"])
        def sda_manager_group_app_install():
            logging.info("[" + request.method + "] sda manager group app install - IN")

            l = list()
            d = dict()
            ret = dict()

            data = json.loads(request.data)
            response = requests.post(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                    + SDAManager.get_group_id() + "/apps/deploy",
                data=data["data"],
                timeout=1500)

            if response.status_code is not 200:
                logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                abort(500)

            d.update({"id": response.json()["id"], "name": data["name"]})

            root_path = os.getcwd()

            if not os.path.exists(root_path + "/static/user/apps"):
                with open(root_path + "/static/user/apps", 'w'): pass

            with open(root_path + "/static/user/apps", 'r') as content_file:
                content = content_file.read()
                if content == "":
                    apps = {"apps": l}
                else:
                    apps = json.loads(content)

                apps["apps"].append(d)

            with open(root_path + "/static/user/apps", 'w+') as content_file:
                content_file.write(json.dumps(apps))

            ret.update({"id": response.json()["id"]})

            return json.dumps(json.dumps(ret)), 200

        # Change an group members
        @app.route("/sdamanager/group/members", methods=["POST"])
        def sda_manager_group_members():
            logging.info("[" + request.method + "] sda manager group members - IN")

            join_dict = dict()
            leave_dict = dict()

            response = requests.get(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/" + SDAManager.get_group_id(),
                timeout=1500)

            if response.status_code is not 200:
                logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                abort(500)

            join_list = request.json["nodes"]
            leave_list = response.json()["members"]

            for i in join_list[:]:
                if i in leave_list:
                    join_list.remove(i)
                    leave_list.remove(i)

            join_dict.update({"nodes": join_list})
            leave_dict.update({"nodes": leave_list})

            response2 = requests.post(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                    + SDAManager.get_group_id() + "/join",
                data=json.dumps(join_dict),
                timeout=1500)

            response3 = requests.post(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                    + SDAManager.get_group_id() + "/leave",
                data=json.dumps(leave_dict),
                timeout=1500)

            if response2.status_code is not 200 and response3.status_code is not 200:
                logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                abort(500)

            return "", 200

        # Get a group apps Info.
        @app.route("/sdamanager/group/apps", methods=["GET"])
        def sda_manager_group_apps():
            logging.info("[" + request.method + "] sda manager group apps - IN")

            l = list()
            apps = list()
            ret = dict()

            response = requests.get(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                    + SDAManager.get_group_id() + "/apps",
                timeout=1500)

            if response.status_code is not 200:
                logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                abort(500)

            root_path = os.getcwd()

            if not os.path.exists(root_path + "/static/user/apps"):
                with open(root_path + "/static/user/apps", 'w'): pass

            with open(root_path + "/static/user/apps", 'r') as content_file:
                content = content_file.read()
                if content != "":
                    apps = json.loads(content)["apps"]

            for obj in response.json()["apps"]:
                d = dict()
                d.update({"id": str(obj["id"])})
                response2 = requests.get(
                    url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                        + SDAManager.get_group_id() + "/apps/" + str(obj["id"]),
                    timeout=1500)

                if response2.status_code is not 200:
                    logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                    abort(500)

                d.update({"services": len(response2.json()["responses"][0]["services"])})

                for app in apps:
                    if "id" in app and app["id"] == str(obj["id"]):
                        d.update({"name": app["name"]})
                l.append(d)

            ret.update({"group": "Group Name: " + SDAManager.get_current_group_name(), "apps": l})

            return json.dumps(json.dumps(ret)), 200

        # Get a group's app Info & Delete a group's app
        @app.route("/sdamanager/group/app", methods=["POST", "DELETE"])
        def sda_manager_group_app():
            if request.method == "POST":
                logging.info("[" + request.method + "] sda manager group app - IN")

                l = list()
                l2 = list()
                ret = dict()

                SDAManager.set_app_id(json.loads(request.data)["id"])

                response = requests.get(
                    url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/nodes",
                    timeout=1500)

                response2 = requests.get(
                    url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                        + SDAManager.get_group_id() + "/apps",
                    timeout=1500)

                if response.status_code is not 200:
                    logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                    abort(500)

                for obj in response.json()["nodes"]:
                    d = dict()
                    if "id" in obj:
                        d.update({"id": str(obj["id"])})

                        res = requests.get(
                            url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/nodes/" + str(obj["id"]) + "/configuration",
                            timeout=1500)
                        if res.status_code is 200:
                            for prop in res.json()["properties"]:
                                if "devicename" in prop:
                                    d.update({"name": str(prop["devicename"])})
                    if "ip" in obj:
                        d.update({"ip": str(obj["ip"])})
                    if "status" in obj:
                        d.update({"status": str(obj["status"])})
                    l.append(d)

                for obj2 in response2.json()["apps"]:
                    if obj2["id"] == SDAManager.get_app_id():
                        for device in l:
                            for member in obj2["members"]:
                                if device["id"] == member:
                                    l2.append(device)
                                    break

                    ret.update({"devices": l2})

                return json.dumps(json.dumps(ret)), 200
            elif request.method == "DELETE":
                response = requests.delete(
                    url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                        + SDAManager.get_group_id() + "/apps/" + SDAManager.get_app_id(),
                    timeout=1500)

                if response.status_code is not 200:
                    logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                    abort(500)

                return "", 200

        # Start a group's app
        @app.route("/sdamanager/group/app/start", methods=["GET"])
        def sda_manager_group_app_start():
            logging.info("[" + request.method + "] sda manager group app update - IN")

            response = requests.post(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                    + SDAManager.get_group_id() + "/apps/" + SDAManager.get_app_id()
                    + "/start",
                timeout=1500)

            if response.status_code is not 200:
                logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                abort(500)

            return "", 200

        # Stop a group's app
        @app.route("/sdamanager/group/app/stop", methods=["GET"])
        def sda_manager_group_app_stop():
            logging.info("[" + request.method + "] sda manager group app update - IN")

            response = requests.post(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                    + SDAManager.get_group_id() + "/apps/" + SDAManager.get_app_id()
                    + "/stop",
                timeout=1500)

            if response.status_code is not 200:
                logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                abort(500)

            return "", 200

        # Update a group's app
        @app.route("/sdamanager/group/app/update", methods=["GET"])
        def sda_manager_group_app_update():
            logging.info("[" + request.method + "] sda manager group app update - IN")

            response = requests.post(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                    + SDAManager.get_group_id() + "/apps/" + SDAManager.get_app_id()
                    + "/update",
                timeout=1500)

            if response.status_code is not 200:
                logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                abort(500)

            return "", 200

        # Update a group's app Yaml file to SDA DB
        @app.route("/sdamanager/group/app/yaml", methods=["POST"])
        def sda_manager_group_app_yaml():
            logging.info("[" + request.method + "] sda manager group app YAML - IN")

            data = json.loads(request.data)

            response = requests.post(
                url="http://" + SDAManager().get_sda_manager_endpoint() + "/api/v1/management/groups/"
                    + SDAManager.get_group_id() + "/apps/" + SDAManager.get_app_id(),
                data=data["data"],
                timeout=1500)

            if response.status_code is not 200:
                logging.error("SDAM Server Return Error, Error Code(" + str(response.status_code) + ") - OUT")
                abort(500)

            return "", 200
