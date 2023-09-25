import os
import sys

import flet as ft
from keri.core.coring import Tiers
from signify.app.clienting import SignifyClient

DEFAULT_AGENT_URL = "http://localhost:3901"
DEFAULT_PASSCODE = "0123456789abcdefghijk"


class NotifcationsApp:

    def __init__(self):
        self.client = None
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Message Type")),
                ft.DataColumn(ft.Text("Source")),
                ft.DataColumn(ft.Text("Destination"), numeric=True),
            ]
        )

    def connect(self, url, passcode):
        tier = Tiers.low
        self.client = SignifyClient(passcode=passcode, tier=tier, url=url)
        notifications = self.client.notifications()
        res = notifications.list()
        for note in res['notes']:
            route = note['r']
            match route:
                case "/multisig/icp":
                    row = ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("Multisig Inception Request")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text("")),
                        ],
                    )
                    self.table.rows.append(row)
                case "/multisig/vcp":
                    row = ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("Multisig Credential Registration Request")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text("")),
                        ],
                    )
                    self.table.rows.append(row)
                case "/multisig/iss":
                    row = ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("Multisig Credential Creation Request")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text("")),
                        ],
                    )
                    self.table.rows.append(row)

        self.table.update()


def main(page: ft.Page):
    app = NotifcationsApp()

    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.title = "SignifyPy Notifications"

    url = ft.TextField(value=DEFAULT_AGENT_URL)
    passcode = ft.TextField(password=True, value=DEFAULT_PASSCODE)

    column = ft.Column([
        ft.Text("Agent URL"),
        url,
        ft.Text("Agent Passcode"),
        passcode
    ])

    def cancel_dlg(e):
        dlg_modal.open = False
        page.update()

    def connect_dlg(e):
        dlg_modal.open = False
        bran = passcode.value.encode("utf-8")
        app.connect(url.value, bran)
        page.update()

    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("Connect to Agent"),
        content=column,
        actions=[
            ft.TextButton("Connect", on_click=connect_dlg),
            ft.TextButton("Cancel", on_click=cancel_dlg),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e: print("Modal dialog dismissed!"),
    )

    def open_dlg_modal(e):
        url.value = DEFAULT_AGENT_URL
        passcode.value = DEFAULT_PASSCODE
        page.dialog = dlg_modal
        dlg_modal.open = True
        page.update()

    def exitApp(e):
        page.window_destroy()

    page.appbar = ft.AppBar(
        leading=ft.Icon(ft.icons.VPN_LOCK),
        leading_width=40,
        title=ft.Text("Agent"),
        center_title=False,
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[
            ft.IconButton(ft.icons.NOTIFICATIONS_NONE),
            ft.PopupMenuButton(
                items=[
                    ft.PopupMenuItem(text="Connect", on_click=open_dlg_modal),
                    ft.PopupMenuItem(text="Exit", on_click=exitApp),
                ]
            ),
        ],
    )

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=400,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.FAVORITE_BORDER, selected_icon=ft.icons.FAVORITE, label="Identifers"
            ),
            ft.NavigationRailDestination(
                icon_content=ft.Icon(ft.icons.BOOKMARK_BORDER),
                selected_icon_content=ft.Icon(ft.icons.BOOKMARK),
                label="Credentials",
            ),
            ft.NavigationRailDestination(
                icon_content=ft.Icon(ft.icons.CONTACTS),
                selected_icon_content=ft.Icon(ft.icons.BOOKMARK),
                label="Contacts",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon_content=ft.Icon(ft.icons.SETTINGS),
                label_content=ft.Text("Settings"),
            ),
        ],
        on_change=lambda e: print("Selected destination:", e.control.selected_index),
    )

    page.add(
        ft.Row(
            [
                rail,
                ft.VerticalDivider(width=1),
                ft.Column([app.table], alignment=ft.MainAxisAlignment.START, expand=True),
            ],
            expand=True,
        )
    )


ft.app(target=main)
