import flet as ft
import os
from elements import single_test


def main(page: ft.Page) -> None:
    """
    The main function that sets up the user interface and handles the routing.

    Args:
        page (ft.Page): The page object representing the user interface.
    """
    page.title = "B.A.C.U"
    page.horizontal_alignment = ft.MainAxisAlignment.CENTER
    page.window.width = 1200
    page.window.height = 1000
    page.window.resizable = False
    page.theme_mode = 'light'

    input_height = 100
    input_width = 550
    input_text_size = 40
    
    logo = ft.Image = ft.Image(src="logo.jpeg", width=150)
    text_name: ft.TextField = ft.TextField(label="Operator's Name:", text_align=ft.TextAlign.LEFT, width=input_width, height=input_height, text_size=input_text_size, helper_text='Enter your name')
    text_serial: ft.TextField = ft.TextField(label="Serial Number:", text_align=ft.TextAlign.LEFT, width=input_width, height=input_height, text_size=input_text_size, helper_text='Enter the 6 numerical digits of the serial number only')
    button_continue: ft.ElevatedButton = ft.ElevatedButton(text='Continue', width=input_width, on_click=lambda _:page.go('/confirm_serial'), disabled=True, height=input_height)
    case_integrity: ft.TextField = ft.TextField(label="Case Integrity:", text_align=ft.TextAlign.LEFT, width=input_width, height=input_height, text_size=input_text_size)
    rsu_connector: ft.TextField = ft.TextField(label="RSU Connector:", text_align=ft.TextAlign.LEFT, width=input_width, height=input_height, text_size=input_text_size)
    handtest_connectors: ft.TextField = ft.TextField(label="HandTest Connectors:", text_align=ft.TextAlign.LEFT, width=input_width, height=input_height, text_size=input_text_size)
    encoder_connector: ft.TextField = ft.TextField(label="Encoder Connector:", text_align=ft.TextAlign.LEFT, width=input_width, height=input_height, text_size=input_text_size)
    battery_cable: ft.TextField = ft.TextField(label="Battery Cable:", text_align=ft.TextAlign.LEFT, width=input_width, height=input_height, text_size=input_text_size)
    details_input: ft.TextField = ft.TextField(label="Enter Details:", text_align=ft.TextAlign.LEFT, width=input_width, multiline=True, height=input_height, text_size=36)
    button_visual: ft.ElevatedButton = ft.ElevatedButton(text='Submit', on_click=lambda _: page.go('/confirm_visual'), disabled=True, height=input_height, width=input_width)

    def validate_home(e: ft.ControlEvent) -> None:
        """
        Validates the input fields on the home page and enables/disables the continue button accordingly.

        Args:
            e (ft.ControlEvent): The control event that triggered the validation.
        """
        if len(text_name.value) > 0 and len(text_serial.value) == 6:
            button_continue.disabled = False
        else:
            button_continue.disabled = True

    
        page.update()

    def validate_visual(e: ft.ControlEvent) -> None:
        """
        Validates the input fields on the visual inspection page and enables/disables the submit button accordingly.

        Args:
            e (ft.ControlEvent): The control event that triggered the validation.
        """
        if all([case_integrity.value, rsu_connector.value,handtest_connectors.value, encoder_connector.value,
                battery_cable.value]):
            button_visual.disabled = False
        else:
            button_visual.disabled = True

        page.update()

    text_name.on_change = validate_home
    text_serial.on_change = validate_home

    case_integrity.on_change = validate_visual
    rsu_connector.on_change = validate_visual
    encoder_connector.on_change = validate_visual
    handtest_connectors.on_change = validate_visual
    battery_cable.on_change = validate_visual

    def route_change(e: ft.RouteChangeEvent) -> None:
        """
        Handles the routing logic based on the current route.

        Args:
            e (ft.RouteChangeEvent): The route change event.
        """
        def restart_test(e: ft.ControlEvent) -> None:
            """
            Restarts the test by clearing the views and going to the home page.

            Args:
                e (ft.ControlEvent): The control event that triggered the restart.
            """
            text_name.value = '' 
            text_serial.value = '' 
            case_integrity.value = '' 
            rsu_connector.value = '' 
            handtest_connectors.value = '' 
            encoder_connector.value = '' 
            battery_cable.value = ''
            details_input.value = ''

            validate_home(e)
            validate_visual(e)

            page.views.clear()
            page.go('/')
            
            
        page.views.clear()

        page.views.append(
            ft.View(
                route = '/',
                controls=[
                    logo,
                    ft.Text(value='B-Scan Automated Calibration Unit', text_align=ft.TextAlign.CENTER, size=40),
                    text_name,
                    text_serial,
                    button_continue,
                    # ft.FloatingActionButton(icon=ft.icons.SETTINGS, on_click=lambda _: page.go('/settings'))
                ],
                vertical_alignment = ft.MainAxisAlignment.START,
                horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                spacing=26
            )
        )
        

        if page.route == '/settings':
            page.views.append(
                ft.View(
                    route = '/settings',
                    controls = [
                        logo,
                        ft.Text(value='Settings', size=40),
                        ft.Row(
                            controls = [
                                ft.Column(
                                    controls=[
                                        ft.Text(value='Tests', size=32),
                                        ft.ElevatedButton(text='Transmitter Pulse Parameters', on_click=lambda _: single_test('transmitter'), height=input_height, width=350),
                                        ft.ElevatedButton(text='Frequency Response', on_click=lambda _: single_test('frequency'), height=input_height, width=350),
                                        ft.ElevatedButton(text='Equivalant Noise', on_click=lambda _: single_test('noise'), height=input_height, width=350),
                                        ft.ElevatedButton(text='Attenuator Accuracy', on_click=lambda _: single_test('attenuator'), height=input_height, width=350),
                                        ft.ElevatedButton(text='Vertical Linearity', on_click=lambda _: single_test('vertical'), height=input_height, width=350),
                                        ],
                                    alignment=ft.MainAxisAlignment.START,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(value='Utilites', size=32),
                                        ft.ElevatedButton(text='Attenuator Reference Check', on_click = lambda _: os.startfile(r"C:\Users\Jonathan.Watkins\OneDrive - Sperry Rail\Documents\Atten.exe"), height=input_height, width=350),
                                        ft.ElevatedButton(text='Attenuator Adjustment', on_click = lambda _: os.startfile(r"C:\Users\Jonathan.Watkins\OneDrive - Sperry Rail\Documents\Atten_adj.exe"), height=input_height, width=350)
                                        ],
                                    alignment=ft.MainAxisAlignment.START,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        )
                    ],
                    vertical_alignment = ft.MainAxisAlignment.START,
                    horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                    spacing = 26 
                )
            )

        if page.route == '/confirm_serial':
            page.views.append(
                ft.View(
                    route = '/confirm_serial',
                    controls = [
                        logo,
                        ft.Text(value='Correct? please confirm', size=32),
                        ft.Text(value=f"Operator's Name: {text_name.value}", size=32),
                        ft.Text(value=f'Serial Number: SRT-{text_serial.value}', size=32),
                        ft.ElevatedButton(text='Confirm', on_click=lambda _: page.go('/visual'), height=input_height, width=input_width),
                        ft.ElevatedButton(text='Make Changes', on_click=lambda _: page.go('/'), height=input_height, width=input_width)
                    ],
                    vertical_alignment = ft.MainAxisAlignment.CENTER,
                    horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                    spacing = 26 
                )
            )

        if page.route == '/visual':
            page.views.append(
                ft.View(
                    route = '/visual',
                    controls = [
                        ft.Column(
                            controls = [
                                logo,
                                ft.Text(value=f'Welcome {text_name.value}', size=32),
                                ft.Text(value='Enter Visual Inspection Results', size=22),
                                ft.Row(controls=[
                                ft.Column(
                                    controls=[
                                        case_integrity,
                                        handtest_connectors,
                                        battery_cable,
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    alignment=ft.MainAxisAlignment.START,

                                ),
                                ft.Column(
                                    controls=[
                                        rsu_connector,
                                        encoder_connector,
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    alignment=ft.MainAxisAlignment.START,
                                )
                            ]
                        ),
                        details_input,
                        button_visual,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,

                )
                         ],
                vertical_alignment = ft.MainAxisAlignment.CENTER,
                horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                spacing = 10,
            ))

        if page.route == '/confirm_visual':
            page.views.append(
                ft.View(
                    route = '/confirm_visual',
                    controls = [
                        logo,
                        ft.Text(value='Confirm Results', size=32),
                        ft.Text(value=f'Case Integrity: {case_integrity.value}', size=22),
                        ft.Text(value=f'RSU Connector: {rsu_connector.value}', size=22),
                        ft.Text(value=f'HandTest Connector: {handtest_connectors.value}', size=22),
                        ft.Text(value=f'Encoder Connector: {encoder_connector.value}', size=22),
                        ft.Text(value=f'Battery Cable: {battery_cable.value}', size=22),
                        ft.Text(value=f'Details: {details_input.value}', size=22),
                        ft.ElevatedButton(text='Confirm', on_click=lambda _: page.go('/power'), height=input_height, width=input_width),
                        ft.ElevatedButton(text='Make Changes', on_click=lambda _: page.go('/visual'), height=input_height, width=input_width)
                    ],
                    vertical_alignment = ft.MainAxisAlignment.CENTER,
                    horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                    spacing = 10
                )
            )

        if page.route == '/power':
            page.views.append(
                ft.View(
                    route = '/power',
                    controls = [
                        logo,
                        ft.Text(value='Connect the Flaw Detector and Power On', size=40),
                        ft.ElevatedButton(text='Confirm', on_click=lambda _: page.go('/start'), height=input_height, width=input_width)                       
                    ],
                    vertical_alignment = ft.MainAxisAlignment.CENTER,
                    horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                    spacing = 26 
                )
            )

        if page.route == '/start':
            page.views.append(
                ft.View(
                    route = '/start',
                    controls = [
                        logo,
                        ft.Text(value='Performing Tests', size=40),                      
                    ],
                    vertical_alignment = ft.MainAxisAlignment.CENTER,
                    horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                    spacing = 26 
                )
            )
            page.update()
            from procedure import main
            import time
            userData = {
                "Operator's Name": text_name.value,
                "Serial Number": text_serial.value,
                'Case Integrity': case_integrity.value,
                'RSU Connector': rsu_connector.value,
                'HandTest Connector': handtest_connectors.value,
                'Encoder Connector': encoder_connector.value,
                'Battery Cable': battery_cable.value,
                'Details': details_input.value,
            }
            main(userData)
            time.sleep(5)
            page.go('/complete')

        if page.route == '/complete':
            page.views.append(
                ft.View(
                    route = '/complete',
                    controls = [
                        logo,
                        ft.Text(value='Testing Complete', size=40),
                        ft.Text(value='The Flaw Detector may be disconnected', size=32),
                        ft.Text(value='Restart software to start new test', size=32),
                        ft.ElevatedButton(text='Restart', on_click=restart_test, height=input_height, width=input_width)
                    ],
                    vertical_alignment = ft.MainAxisAlignment.CENTER,
                    horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                    spacing = 26 
                )
            )
        page.update()

    def view_pop(e: ft.ViewPopEvent) -> None:
        """
        Handles the view pop event.

        Args:
            e (ft.ViewPopEvent): The view pop event.
        """
        page.views.pop()
        top_view: ft.View = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)

ft.app(main)

