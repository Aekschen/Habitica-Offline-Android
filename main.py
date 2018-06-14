# -*- coding: utf-8 -*-
import json
import requests
import os
import webbrowser

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.image import Image
from kivy.clock import Clock

from kivymd.button import MDIconButton
from kivymd.list import ILeftBody, \
    ILeftBodyTouch, \
    IRightBodyTouch, \
    TwoLineAvatarIconListItem
from kivymd.snackbar import Snackbar
from kivymd.theming import ThemeManager


class HabiticaOffline(App):
    theme_cls = ThemeManager()
    title = "Habitica Offline"

    def build(self):
        # main_widget = Builder.load_string(main_widget_kv)  # commented out
        main_widget = Builder.load_file('./layout.kv')
        # self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'DeepPurple'
        self.theme_cls.primary_hue = '800'

        return main_widget

    def on_start(self):
        global configFilePath
        configFilePath = './config.json'
        global todoFilePath
        todoFilePath = './todos.json'
        global config
        config = self.loadConfig()

        if config['user_id'] == "" or config['api_token'] == "":
            self.root.ids.scr_mngr.current = 'settings'
            self.show_snackbar_message(
                'Welcome! Please enter your Habitica ' +
                'user credentials first. Open the Habitica user profile ' +
                'with the button above to view your personal ' +
                'api-token and user-id.',
                15)
        else:
            self.reloadTodos()  # load todos file
            # set focus on the todos subject line
            Clock.schedule_once(self.setFocusToToDoField, 4)

    def on_pause(self):
        return True

    def openBrowserTab(self, url, mode):
        webbrowser.open(url, new=mode)

    def openHabiticaBrowser(self):
        link = 'https://habitica.com/user/settings/api'
        self.openBrowserTab(link, 2)

    def openGithubBrowser(self):
        link = 'https://github.com/Aekschen/Habitica-Offline-Android'
        self.openBrowserTab(link, 2)

    def openGithubIssueBrowser(self):
        link = 'https://github.com/Aekschen/Habitica-Offline-Android/issues'
        self.openBrowserTab(link, 2)

    def setFocusToToDoField(self, *args):
        self.root.ids.todo_name_field.focus = True

    # Display snackbar message with text and duration
    def show_snackbar_message(self, message, duration):
        Snackbar(text=message, duration=duration).show()

    # load user credentials from the config file
    def loadConfig(self):
        if os.path.isfile(todoFilePath):
            json_data = open(configFilePath)
            data = json.load(json_data)
            json_data.close()
            self.root.ids.user_id_field.text = data['user_id']
            self.root.ids.api_token_field.text = data['api_token']
        else:
            data = {'user_id': '', 'api_token': ''}
        return data

    # Save user credentials to the config file
    def saveConfig(self):
        out_file = open(configFilePath, "w")
        data = [{
            "user_id": self.root.ids.user_id_field.text,
            "api_token": self.root.ids.api_token_field.text}]
        json.dump(data[0], out_file, indent=4)
        out_file.close()

    # Reload todos from file
    def reloadTodos(self):
        self.root.ids.ml.clear_widgets()  # clear the list and repopulate later
        items = self.getKivyTodosFromFile()
        for i in items:
            self.root.ids.ml.add_widget(i)

    # Writes list of to-dos to file
    def writeTodosToFile(self, data):
        if os.path.isfile(todoFilePath):
            out_file = open(todoFilePath, "w")
            json.dump(data, out_file, indent=4)
            out_file.close()

    # Returns list of to-dos
    def getTodosFromFile(self):
        if os.path.isfile(todoFilePath):
            json_data = open(todoFilePath)
            data = json.load(json_data)
            json_data.close()
        else:
            data = []
        return data

    # Returns list of to-dos for kivy ui
    def getKivyTodosFromFile(self):
        data = self.getTodosFromFile()

        items = []
        for index, item in enumerate(reversed(data)):
            i = TwoLineAvatarIconListItem(
                id="todoid" + str(index),
                text=item['name'],
                secondary_text=item['description'])

            # i.add_widget(AvatarSampleWidget(source = './assets/a.png') )
            i.add_widget(IconLeftSampleWidget(icon='star-circle'))

            i.add_widget(IconRightWidget(
                id=str(index),
                icon='pencil',
                on_release=lambda btn: self.editItem(int(btn.id))))

            i.add_widget(IconRightWidget(
                id=str(index),
                icon='delete',
                on_release=lambda btn: self.removeItems([int(btn.id)])))

            items.append(i)
        return items

    # Add item from input field to json file and reload list
    def addItem(self):
        name = self.root.ids.todo_name_field.text
        description = self.root.ids.todo_description_field.text

        # set fields to blank after adding the item
        self.root.ids.todo_name_field.text = ""
        self.root.ids.todo_description_field.text = ""

        if len(name) > 0:
            json_data = open(todoFilePath)
            data = json.load(json_data)
            json_data.close()

            if len(data) == 0 or data[-1]['name'] != name:
                data.append({
                    'name': name,
                    'description': description,
                    'synced': False})

                self.writeTodosToFile(data)
                self.reloadTodos()

            else:
                self.show_snackbar_message('To-Do already added', 3)
        else:
            self.show_snackbar_message('Please enter a To-Do subject first', 3)

    def removeItems(self, ids):
        data = self.getTodosFromFile()
        data = list(reversed(data))
        for index in sorted(ids, reverse=True):
            del data[index]
        self.writeTodosToFile(list(reversed(data)))
        self.reloadTodos()

    def editItem(self, id):
        data = self.getTodosFromFile()
        data = list(reversed(data))
        editItem = data[id]
        del data[id]  # delete position x from array
        self.writeTodosToFile(list(reversed(data)))
        self.reloadTodos()
        self.root.ids.todo_name_field.text = editItem['name']
        self.root.ids.todo_description_field.text = editItem['description']

    def syncItemsWithHabitica(self):
        baseurl = "https://habitica.com"
        baseurl += "/api/v3/"
        headers = {
            "x-api-user": config['user_id'],
            "x-api-key": config['api_token'],
            "Content-Type": "application/json"}

        data = self.getTodosFromFile()

        if len(data) > 0:
            successfulRequests = []

            for index, item in enumerate(data):
                payload = {
                    "text": item['name'],
                    "type": "todo",
                    "notes": item['description'],
                    "priority": 2}

                req = requests.post(
                    baseurl + "tasks/user",
                    data=json.dumps(payload),
                    headers=headers)

                if req.json()['success'] is True:
                    successfulRequests.append(index)
                else:
                    self.show_snackbar_message('Ohoh! Some sync failed!', 5)

            self.removeItems(successfulRequests)
            self.show_snackbar_message('Sync done!', 3)
        else:
            self.show_snackbar_message('No To-Dos to sync available', 3)

    def checkHabiticaConnection(self, *args):
        self.saveConfig()
        baseurl = "https://habitica.com"
        baseurl += "/api/v3/"
        headers = {
            "x-api-user": config['user_id'],
            "x-api-key": config['api_token'],
            "Content-Type": "application/json"}

        req = requests.get(baseurl + "user", headers=headers)
        if req.json()['success'] is True:
            self.show_snackbar_message(
                'Welcome ' + req.json()['data']['auth']['local']['username'] +
                '! The connection was successful!', 5)
            self.root.ids.scr_mngr.current = 'todos'
        else:
            self.show_snackbar_message(
                'Ohoh! The connection failed! Please check your numbers.', 5)


class AvatarSampleWidget(ILeftBody, Image):
    pass


class IconLeftSampleWidget(ILeftBodyTouch, MDIconButton):
    pass


class IconRightWidget(IRightBodyTouch, MDIconButton):
    pass


if __name__ == '__main__':
    HabiticaOffline().run()
