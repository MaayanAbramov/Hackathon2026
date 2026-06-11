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
from kivy.network.urlrequest import UrlRequest
import random
import json

from kivy_garden.zbarcam import ZBarCam

class ScannerApp(App):
    def build(self):
        Logger.info("ScannerApp: Booting up UI...")
        
        # --- API Configuration ---
        # Change these to match your Flask server's IP and port
        self.SERVER_IP = "132.68.41.143" 
        self.SERVER_PORT = "5000"
        
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
        
        self.remove_checkbox = CheckBox(size_hint=(None, None), size=(80, 80))
        self.remove_checkbox.bind(active=self.toggle_remove_mode)
        
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
        
        self.main_layout.add_widget(self.row1)
        
        if not self.remove_checkbox.active:
            self.main_layout.add_widget(self.row2)
            
        self.main_layout.add_widget(self.remove_row)
        
        self.main_layout.add_widget(self.btn_submit)
        self.main_layout.add_widget(self.output_label)

    def toggle_remove_mode(self, instance, value):
        self.update_layout()
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
        self.current_scan_field = target_field
        self.zbarcam.symbols.clear()
        self.scanner_popup.open()
        Clock.schedule_once(self._start_camera_hardware, 0.5)

    def _start_camera_hardware(self, dt):
        self.zbarcam.ids.xcamera.play = True
        self.scan_event = Clock.schedule_interval(self.check_scan, 0.1)

    def check_scan(self, dt):
        if len(self.zbarcam.symbols) > 0:
            scanned_data = self.zbarcam.symbols[0].data.decode('utf-8')
            Logger.info(f"ScannerApp: *** SYMBOL DECODED: {scanned_data} ***")
            self.current_scan_field.text = scanned_data
            self.close_scanner()

    def close_scanner(self, *args):
        if self.scan_event:
            self.scan_event.cancel()
            self.scan_event = None
        self.scanner_popup.dismiss()
        Clock.schedule_once(self._stop_camera_hardware, 0.3)

    def _stop_camera_hardware(self, dt):
        self.zbarcam.ids.xcamera.play = False

    def submit_action(self, instance):
        patient_number = self.field1.text.strip()
        dept_barcode = self.field2.text.strip()
        
        # --- NEW: Validation Check ---
        # If the field isn't empty, check if it's strictly numeric
        if patient_number and not patient_number.isnumeric():
            error_msg = f"Patient number '{patient_number}' is not a number, please scan the correct patient barcode and try submitting again."
            self.output_label.text = error_msg
            Logger.info(f"ScannerApp: Validation failed -> {error_msg}")
            return
        # -----------------------------
        
        # Path 1: "Remove Patient" is Checked
        if self.remove_checkbox.active:
            if not patient_number:
                self.output_label.text = "Please scan/enter patient number to remove."
                return
            
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

            btn_cancel.bind(on_press=self.confirm_popup.dismiss)
            # Pass the validated patient_number to process_removal
            btn_ok.bind(on_press=lambda x: self.process_removal(patient_number))
            
            self.confirm_popup.open()

        # Path 2: Standard Submission Mode
        else:
            if patient_number and dept_barcode:
                self.output_label.text = "Sending data to server..."
                
                # Setup payload and URL for standard upsert
                # --- NEW: Convert patient_number to int() ---
                payload = {
                    "patientNumber": int(patient_number),
                    "roombarcode": dept_barcode
                }
                url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/api/update_location"
                headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
                
                # Send the async request
                UrlRequest(
                    url,
                    req_body=json.dumps(payload),
                    req_headers=headers,
                    method='POST',
                    on_success=self.on_upsert_success,
                    on_failure=self.on_request_error,
                    on_error=self.on_request_error
                )
                Logger.info(f"ScannerApp: Sending request -> Patient : {patient_number}, Dept: {dept_barcode}")
            else:
                self.output_label.text = "Please complete both scans first."
                Logger.info("ScannerApp: Form submission rejected (fields empty)")

    def process_removal(self, patient_number):
        """Triggered when the user approves the removal popup."""
        self.confirm_popup.dismiss()
        self.output_label.text = "Sending removal request to server..."
        
        # Setup payload and URL for removal
        # --- NEW: Convert patient_number to int() ---
        payload = {
            "patientNumber": int(patient_number)
        }
        url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/api/remove_patient"
        headers = {'Content-type': 'application/json'}
        
        # Send the async request
        UrlRequest(
            url,
            req_body=json.dumps(payload),
            req_headers=headers,
            method='POST',
            on_success=self.on_remove_success,
            on_failure=self.on_request_error,
            on_error=self.on_request_error
        )

    # --- Async Request Callbacks ---
    
    def on_upsert_success(self, request, result):
        Logger.info(f"ScannerApp: Upsert successful -> Server response: {result}")
        self.output_label.text = "Patient successfully submitted."
        self.field1.text = ""
        self.field2.text = ""
        
    def on_remove_success(self, request, result):
        Logger.info(f"ScannerApp: Removal successful -> Server response: {result}")
        self.output_label.text = "Patient was removed."
        self.field1.text = ""

    def on_request_error(self, request, error):
        Logger.error(f"ScannerApp: Server request failed -> {error}")
        self.output_label.text = "Error communicating with server.\nPlease check your connection."

if __name__ == '__main__':
    ScannerApp().run()