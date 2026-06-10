from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.clock import Clock
from kivy.utils import platform
from kivy.logger import Logger
import random

from kivy_garden.zbarcam import ZBarCam

class ScannerApp(App):
    def build(self):
        Logger.info("ScannerApp: Booting up UI...")
        
        # Increased padding and spacing for a more spacious layout
        self.main_layout = BoxLayout(orientation='vertical', padding=40, spacing=30)
        
        self.current_scan_field = None 
        self.scan_event = None

        # --- Row 1: Patient Barcode ---
        self.row1 = BoxLayout(orientation='horizontal', spacing=15, size_hint_y=None, height=60)
        self.field1 = TextInput(hint_text="Patient Barcode", multiline=False, size_hint_x=0.7)
        btn_scan1 = Button(text="Scan", size_hint_x=0.3)
        btn_scan1.bind(on_press=lambda instance: self.open_scanner(self.field1))
        self.row1.add_widget(self.field1)
        self.row1.add_widget(btn_scan1)

        # --- Row 2: Room/Department Barcode ---
        self.row2 = BoxLayout(orientation='horizontal', spacing=15, size_hint_y=None, height=60)
        self.field2 = TextInput(hint_text="Room\\Department Barcode", multiline=False, size_hint_x=0.7)
        btn_scan2 = Button(text="Scan", size_hint_x=0.3)
        btn_scan2.bind(on_press=lambda instance: self.open_scanner(self.field2))
        self.row2.add_widget(self.field2)
        self.row2.add_widget(btn_scan2)

        # --- Remove Checkbox Row (Moved Below Rows & Increased Size) ---
        self.remove_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=10)
        
        # Made the checkbox significantly larger to fix the tiny size issue
        self.remove_checkbox = CheckBox(size_hint=(None, None), size=(80, 80))
        self.remove_checkbox.bind(active=self.toggle_remove_mode)
        
        # Removed the fixed width so the text no longer gets clipped/squished out of view
        lbl_remove = Label(text="Remove Patient", halign="left", valign="center", size_hint_x=1)
        lbl_remove.bind(size=lbl_remove.setter('text_size'))
        
        self.remove_row.add_widget(self.remove_checkbox)
        self.remove_row.add_widget(lbl_remove)

        # --- Submit Button & Output ---
        self.btn_submit = Button(
            text="Submit", 
            size_hint_y=None, 
            height=60, 
            size_hint_x=0.5, 
            pos_hint={'center_x': 0.5}
        )
        self.btn_submit.bind(on_press=self.submit_action)
        
        self.output_label = Label(text="", size_hint_y=0.4, text_size=(None, None), halign='center')

        # Draw the initial layout
        self.update_layout()
        self.setup_scanner_popup()
        
        return self.main_layout

    def update_layout(self):
        """Clears and redraws the main layout based on the Checkbox state."""
        self.main_layout.clear_widgets()
        
        # Added Patient Row first
        self.main_layout.add_widget(self.row1)
        
        # Only add Dept Row if "Remove Patient" is NOT checked
        if not self.remove_checkbox.active:
            self.main_layout.add_widget(self.row2)
            
        # Add the Remove Checkbox row directly below the scan fields
        self.main_layout.add_widget(self.remove_row)
        
        # Add the rest of the UI
        self.main_layout.add_widget(self.btn_submit)
        self.main_layout.add_widget(self.output_label)

    def toggle_remove_mode(self, instance, value):
        """Triggered whenever the Checkbox is checked or unchecked."""
        self.update_layout()
        
        # Clear out the room/dept field when hidden so old data isn't sitting there
        if value:
            self.field2.text = ""

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
        Logger.debug(f"ScannerApp: Tick... Symbols found: {len(self.zbarcam.symbols)}")
        if len(self.zbarcam.symbols) > 0:
            scanned_data = self.zbarcam.symbols[0].data.decode('utf-8')
            Logger.info(f"ScannerApp: *** SYMBOL DECODED: {scanned_data} ***")
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
        patient_number = self.field1.text.strip()
        dept_barcode = self.field2.text.strip()
        
        # Path 1: "Remove Patient" is Checked
        if self.remove_checkbox.active:
            if not patient_number:
                self.output_label.text = "Please scan/enter patient number to remove."
                return
            
            # Create the confirmation popup
            content = BoxLayout(orientation='vertical', spacing=15, padding=10)
            msg_label = Label(text="Removed was checked, please approve removal", halign='center')
            content.add_widget(msg_label)

            btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
            btn_ok = Button(text="OK")
            btn_cancel = Button(text="Cancel")
            
            btn_layout.add_widget(btn_ok)
            btn_layout.add_widget(btn_cancel)
            content.add_widget(btn_layout)

            self.confirm_popup = Popup(
                title="Confirm Removal", 
                content=content, 
                size_hint=(0.8, 0.4), 
                auto_dismiss=False
            )

            # Bind the popup buttons
            btn_cancel.bind(on_press=self.confirm_popup.dismiss) # Closes popup, nothing else happens
            btn_ok.bind(on_press=lambda x: self.process_removal(patient_number))
            
            self.confirm_popup.open()

        # Path 2: Standard Submission Mode
        else:
            if patient_number and dept_barcode:
                message = f"Patient Number : {patient_number} with department {dept_barcode}\nhas been successfully submitted."
                self.output_label.text = message 
                Logger.info(f"ScannerApp: Form submitted successfully -> Patient: {patient_number}, Dept: {dept_barcode}")
                
                # Reset the scan fields back to empty
                self.field1.text = ""
                self.field2.text = ""
            else:
                self.output_label.text = "Please complete both scans first."
                Logger.info("ScannerApp: Form submission rejected (fields empty)")

    def process_removal(self, patient_number):
        """Callback for when the user clicks 'OK' on the remove confirmation popup."""
        self.confirm_popup.dismiss()
        self.output_label.text = f"Patient number {patient_number} was removed"
        Logger.info(f"ScannerApp: Patient removed -> Patient: {patient_number}")
        
        # Reset the patient scan field
        self.field1.text = ""

if __name__ == '__main__':
    ScannerApp().run()