from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.utils import platform
from kivy.logger import Logger  # <-- IMPORT THE LOGGER
import random

from kivy_garden.zbarcam import ZBarCam

class ScannerApp(App):
    def build(self):
        Logger.info("ScannerApp: Booting up UI...")
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        self.current_scan_field = None 
        self.scan_event = None

        # --- Row 1 ---
        row1 = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.2)
        self.field1 = TextInput(hint_text="Scan Field 1", multiline=False)
        btn_scan1 = Button(text="Scan", size_hint_x=0.3)
        btn_scan1.bind(on_press=lambda instance: self.open_scanner(self.field1))
        row1.add_widget(self.field1)
        row1.add_widget(btn_scan1)

        # --- Row 2 ---
        row2 = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.2)
        self.field2 = TextInput(hint_text="Scan Field 2", multiline=False)
        btn_scan2 = Button(text="Scan", size_hint_x=0.3)
        btn_scan2.bind(on_press=lambda instance: self.open_scanner(self.field2))
        row2.add_widget(self.field2)
        row2.add_widget(btn_scan2)

        # --- Submit Button & Output ---
        btn_submit = Button(text="Submit", size_hint_y=0.3)
        btn_submit.bind(on_press=self.submit_action)
        self.output_label = Label(text="", size_hint_y=0.3)

        self.main_layout.add_widget(row1)
        self.main_layout.add_widget(row2)
        self.main_layout.add_widget(btn_submit)
        self.main_layout.add_widget(self.output_label)

        self.setup_scanner_popup()
        return self.main_layout

    def on_start(self):
        if platform == 'android':
            Logger.info("ScannerApp: Requesting Android permissions...")
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.CAMERA])

    def setup_scanner_popup(self):
        Logger.info("ScannerApp: Initializing singleton ZBarCam...")
        popup_layout = BoxLayout(orientation='vertical')
        
        self.zbarcam = ZBarCam()
        self.zbarcam.ids.xcamera.play = False 
        
        popup_layout.add_widget(self.zbarcam)

        btn_cancel = Button(text="Cancel", size_hint_y=0.2)
        btn_cancel.bind(on_press=self.close_scanner)
        popup_layout.add_widget(btn_cancel)

        self.scanner_popup = Popup(title="Scanning...", content=popup_layout, size_hint=(0.9, 0.9))


    def check_scan(self, dt):
        # We use debug here so it doesn't flood the console *too* heavily, but we can still see it.
        Logger.debug(f"ScannerApp: Tick... Symbols found: {len(self.zbarcam.symbols)}")
        
        if len(self.zbarcam.symbols) > 0:
            scanned_data = self.zbarcam.symbols[0].data.decode('utf-8')
            Logger.info(f"ScannerApp: *** SYMBOL DECODED: {scanned_data} ***")
            self.current_scan_field.text = scanned_data
            self.close_scanner()

    def open_scanner(self, target_field):
        """Prepares the UI, but waits to turn on the camera."""
        self.current_scan_field = target_field
        self.zbarcam.symbols.clear()
        
        # Open the UI popup immediately...
        self.scanner_popup.open()
        
        # ...but give Android hardware 0.5 seconds to catch up before turning the camera on
        Clock.schedule_once(self._start_camera_hardware, 0.5)

    def _start_camera_hardware(self, dt):
        """Actually turns the camera on (called via Clock)."""
        self.zbarcam.ids.xcamera.play = True
        self.scan_event = Clock.schedule_interval(self.check_scan, 0.1)

    def check_scan(self, dt):
        """Fires 10 times a second to check for decoded symbols."""
        if len(self.zbarcam.symbols) > 0:
            scanned_data = self.zbarcam.symbols[0].data.decode('utf-8')
            self.current_scan_field.text = scanned_data
            self.close_scanner()

    def close_scanner(self, *args):
        """Closes the UI, but delays turning off the camera."""
        if self.scan_event:
            self.scan_event.cancel()
            self.scan_event = None
        
        # Close the popup UI immediately...
        self.scanner_popup.dismiss()
        
        # ...but give Android 0.3 seconds to finish its animations before killing the hardware
        Clock.schedule_once(self._stop_camera_hardware, 0.3)

    def _stop_camera_hardware(self, dt):
        """Actually turns the camera off (called via Clock)."""
        self.zbarcam.ids.xcamera.play = False

    def submit_action(self, instance):
        if self.field1.text.strip() and self.field2.text.strip():
            message = random.choice(["Submitted", "Hola Senior"])
            self.output_label.text = message 
            Logger.info(f"ScannerApp: Form submitted successfully -> {message}")
        else:
            self.output_label.text = "Please complete both scans first."
            Logger.info("ScannerApp: Form submission rejected (fields empty)")

if __name__ == '__main__':
    ScannerApp().run()